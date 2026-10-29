import pytest
import logging
from pydantic import ValidationError
from app.core.config import Settings
from app.core.logging_config import SensitiveDataRedactingFilter

@pytest.mark.asyncio
async def test_security_response_headers(async_client):
    # 1. Base endpoint headers
    resp = await async_client.get("/health/live")
    assert resp.status_code == 200

    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "strict-origin-when-cross-origin" in headers.get("Referrer-Policy", "")
    assert "geolocation=()" in headers.get("Permissions-Policy", "")

    # 2. Sensitive endpoints must have Cache-Control: no-store
    auth_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@test.com", "password": "WrongPassword123"}
    )
    assert "no-store" in auth_resp.headers.get("Cache-Control", "")


@pytest.mark.asyncio
async def test_rate_limiting_on_verification_endpoint(async_client):
    # Sensitive endpoints are rate limited to 30 requests per minute per IP
    # Send validly formatted requests to /api/v1/verify
    payload = {"reference_token": "neev_vrf_sample_dummy_token_123456789"}
    got_rate_limited = False

    for _ in range(35):
        resp = await async_client.post("/api/v1/verify", json=payload)
        if resp.status_code == 429:
            got_rate_limited = True
            err_data = resp.json()
            assert err_data.get("error_code") == "RATE_LIMIT_EXCEEDED" or "Too many requests" in str(err_data)
            break

    assert got_rate_limited is True, "Expected 429 Rate limit exceeded after exceeding 30 requests"


def test_production_security_configuration_validation():
    # 1. Dev configuration passes with dev keys
    dev_settings = Settings(
        ENVIRONMENT="development",
        SECRET_KEY="insecure-dev-key",
        APAAR_FINGERPRINT_KEY="insecure-fingerprint-key",
        DATABASE_URL="postgresql+asyncpg://postgres:2006@localhost:5432/neev_dev",
        SYNC_DATABASE_URL="postgresql://postgres:2006@localhost:5432/neev_dev"
    )
    assert dev_settings.ENVIRONMENT == "development"

    # 2. Production configuration fails if using insecure default secret key
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="change-in-production-placeholder-secret-key-that-is-long",
            APAAR_FINGERPRINT_KEY="strong_prod_fingerprint_key_at_least_32_bytes_long!!",
            DATABASE_URL="postgresql+asyncpg://postgres:securepass@localhost:5432/neev_prod",
            SYNC_DATABASE_URL="postgresql://postgres:securepass@localhost:5432/neev_prod"
        )
    assert "Production configuration error" in str(exc_info.value)
    assert "SECRET_KEY" in str(exc_info.value)

    # 3. Production configuration fails if SECRET_KEY is too short
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="too-short",
            APAAR_FINGERPRINT_KEY="strong_prod_fingerprint_key_at_least_32_bytes_long!!",
            DATABASE_URL="postgresql+asyncpg://postgres:securepass@localhost:5432/neev_prod",
            SYNC_DATABASE_URL="postgresql://postgres:securepass@localhost:5432/neev_prod"
        )
    assert "at least 32 characters" in str(exc_info.value)

    # 4. Production configuration succeeds with strong distinct secrets
    prod_valid_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a_very_secure_production_secret_key_that_is_long_and_complex_12345",
        APAAR_FINGERPRINT_KEY="another_very_secure_fingerprint_key_for_hmac_sha256_987654321",
        DATABASE_URL="postgresql+asyncpg://postgres:securepass@localhost:5432/neev_prod",
        SYNC_DATABASE_URL="postgresql://postgres:securepass@localhost:5432/neev_prod"
    )
    assert prod_valid_settings.ENVIRONMENT == "production"


def test_sensitive_data_log_redaction():
    filter_instance = SensitiveDataRedactingFilter()
    
    # Check APAAR 12-digit redaction
    record1 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py", lineno=1,
        msg="Processing record for student with APAAR 123456789012 in submission batch",
        args=(), exc_info=None
    )
    filter_instance.filter(record1)
    assert "123456789012" not in record1.msg
    assert "XXXX" in record1.msg

    # Check password and token redaction
    record2 = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py", lineno=1,
        msg='Failed login attempt with password="MySecretPassword123" and token="eyJh...secret"',
        args=(), exc_info=None
    )
    filter_instance.filter(record2)
    assert "MySecretPassword123" not in record2.msg
    assert "[REDACTED_SECRET]" in record2.msg
