import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_valid_credentials(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/login", json={
        "email": "aicte.admin@neev.aicte.gov.in",
        "password": "NeevAdmin@2026"
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email_normalized"] == "aicte.admin@neev.aicte.gov.in"
    assert "AICTE_ADMIN" in data["user"]["roles"]

@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/login", json={
        "email": "aicte.admin@neev.aicte.gov.in",
        "password": "WrongPassword123!"
    })
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["message"]

@pytest.mark.asyncio
async def test_login_nonexistent_user_generic_error(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/login", json={
        "email": "nonexistent.user@random.org",
        "password": "SomePassword123!"
    })
    assert resp.status_code == 401
    # Generic error without revealing account existence
    assert "Invalid email or password" in resp.json()["message"]

@pytest.mark.asyncio
async def test_login_disabled_account_rejected(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/login", json={
        "email": "disabled.user@neev.aicte.gov.in",
        "password": "DisabledUser@2026"
    })
    assert resp.status_code == 403
    assert "suspended" in resp.json()["message"].lower()

@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/institutions")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["message"]

@pytest.mark.asyncio
async def test_refresh_token_rotation_and_logout(async_client: AsyncClient):
    # 1. Login
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@dit.synthetic.edu.in",
        "password": "DitAdmin@2026"
    })
    assert login_resp.status_code == 200
    cookies = login_resp.cookies
    old_access_token = login_resp.json()["access_token"]

    # 2. Refresh session
    refresh_resp = await async_client.post("/api/v1/auth/refresh", cookies=cookies)
    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["access_token"]
    assert new_access_token != old_access_token
    new_cookies = refresh_resp.cookies

    # 3. Old refresh token should now be invalidated (revoked via rotation)
    old_rf_retry = await async_client.post("/api/v1/auth/refresh", cookies=cookies)
    assert old_rf_retry.status_code == 401

    # 4. Logout with new cookie
    logout_resp = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access_token}"},
        cookies=new_cookies
    )
    assert logout_resp.status_code == 200

    # 5. Refresh after logout must fail
    after_logout_rf = await async_client.post("/api/v1/auth/refresh", cookies=new_cookies)
    assert after_logout_rf.status_code == 401

@pytest.mark.asyncio
async def test_refresh_absent_token_fails_gracefully(async_client: AsyncClient):
    """Calling /auth/refresh without cookies or token must return 401 with a clean message and no crash."""
    resp = await async_client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401
    assert "No active session found" in resp.json()["message"]

@pytest.mark.asyncio
async def test_session_restoration_cycle(async_client: AsyncClient):
    """Validates session restoration: login -> get refresh cookie -> use /auth/refresh to restore access token -> call /auth/me."""
    # 1. Login
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "aicte.admin@neev.aicte.gov.in",
        "password": "NeevAdmin@2026"
    })
    assert login_resp.status_code == 200
    cookies = login_resp.cookies

    # 2. Simulate page reload / new tab: no access token in memory, only refresh cookie
    refresh_resp = await async_client.post("/api/v1/auth/refresh", cookies=cookies)
    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["access_token"]
    assert new_access_token

    # 3. Use restored access token to fetch user profile
    me_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email_normalized"] == "aicte.admin@neev.aicte.gov.in"

@pytest.mark.asyncio
async def test_unauthenticated_access_me(async_client: AsyncClient):
    """Direct call to /auth/me without an Authorization token must return 401."""
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["message"]

@pytest.mark.asyncio
async def test_refresh_revoked_session(async_client: AsyncClient):
    """Attempting to refresh with an already rotated/revoked refresh token must be rejected."""
    # 1. Login
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@mtu.synthetic.edu.in",
        "password": "MtuAdmin@2026"
    })
    assert login_resp.status_code == 200
    cookies = login_resp.cookies

    # 2. First refresh (rotates token, revoking the first one)
    refresh_resp = await async_client.post("/api/v1/auth/refresh", cookies=cookies)
    assert refresh_resp.status_code == 200

    # 3. Second attempt with the original revoked token must trigger reuse detection
    reused_resp = await async_client.post("/api/v1/auth/refresh", cookies=cookies)
    assert reused_resp.status_code == 401
    assert "Session expired due to concurrent access" in reused_resp.json()["message"]

@pytest.mark.asyncio
async def test_cookie_attributes_local_vs_https(async_client: AsyncClient):
    """Verifies that HTTP uses SameSite=Lax and no Secure, while HTTPS requests use SameSite=None and Secure=True."""
    # 1. Local HTTP login
    http_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@dit.synthetic.edu.in",
        "password": "DitAdmin@2026"
    })
    assert http_resp.status_code == 200
    set_cookie_http = http_resp.headers.get("set-cookie", "").lower()
    assert "samesite=lax" in set_cookie_http
    assert "secure" not in set_cookie_http

    # 2. HTTPS / Forwarded HTTPS login (Production deployment simulation)
    https_resp = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@dit.synthetic.edu.in",
            "password": "DitAdmin@2026"
        },
        headers={"x-forwarded-proto": "https"}
    )
    assert https_resp.status_code == 200
    set_cookie_https = https_resp.headers.get("set-cookie", "").lower()
    assert "samesite=none" in set_cookie_https
    assert "secure" in set_cookie_https

@pytest.mark.asyncio
async def test_cors_credentials_for_vercel_origin(async_client: AsyncClient):
    """Verifies CORS headers allow credentials from the Vercel production origin."""
    resp = await async_client.options(
        "/api/v1/auth/login",
        headers={
            "origin": "https://neev01.vercel.app",
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type"
        }
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://neev01.vercel.app"
    assert resp.headers.get("access-control-allow-credentials") == "true"


