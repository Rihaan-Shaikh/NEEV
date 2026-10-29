import pytest

@pytest.mark.asyncio
async def test_integration_status_listing_and_simulation_guarantee(async_client):
    # Log in as AICTE admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Fetch all integration adapter statuses
    status_resp = await async_client.get("/api/v1/integrations/status", headers=headers)
    assert status_resp.status_code == 200
    adapters = status_resp.json()
    assert isinstance(adapters, list)
    assert len(adapters) >= 5

    # Check each adapter adheres to simulated state and has required metadata
    adapter_codes = [a["adapter_code"] for a in adapters]
    assert "APAAR_DIGILOCKER" in adapter_codes
    assert "AISHE_PORTAL" in adapter_codes
    assert "AICTE_APPROVAL_PORTAL" in adapter_codes

    for adapter in adapters:
        assert adapter["is_simulated"] is True
        assert adapter["status"] in ["CONFIGURED", "NOT_CONFIGURED", "SIMULATED", "HEALTHY", "DEGRADED", "OFFLINE", "UNAVAILABLE"]
        assert len(adapter["supported_claims"]) > 0
        assert adapter["known_limitations"] is not None


@pytest.mark.asyncio
async def test_integration_contract_probe(async_client):
    # Log in as AICTE admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Run contract test on APAAR_DIGILOCKER
    probe_resp = await async_client.post(
        "/api/v1/integrations/APAAR_DIGILOCKER/test-contract",
        headers=headers
    )
    assert probe_resp.status_code == 200
    probe_data = probe_resp.json()
    assert probe_data["adapter_code"] == "APAAR_DIGILOCKER"
    assert probe_data["contract_test_status"] in ["PASSED", "SUCCESS", "HEALTHY", "PASS"]
    assert "latency_ms" in probe_data

    # Unknown adapter code should return 404
    bad_probe = await async_client.post(
        "/api/v1/integrations/NON_EXISTENT_ADAPTER/test-contract",
        headers=headers
    )
    assert bad_probe.status_code == 404
