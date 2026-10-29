import pytest

@pytest.mark.asyncio
async def test_cross_institution_conflict_detection(async_client):
    # Log in as national admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Trigger reconciliation
    recon_resp = await async_client.post("/api/v1/integrity/reconcile", headers=headers)
    assert recon_resp.status_code == 200
    data = recon_resp.json()
    assert data["status"] == "COMPLETED"
    assert data["conflicts_detected"] >= 1

    # Fetch conflicts list
    conflicts_resp = await async_client.get("/api/v1/integrity/conflicts", headers=headers)
    assert conflicts_resp.status_code == 200
    conflicts = conflicts_resp.json()
    assert len(conflicts) >= 1

    # Verify DUP-002 active conflict is detected
    dup_002 = next((c for c in conflicts if c["rule_code"] == "DUP-002"), None)
    assert dup_002 is not None
    assert dup_002["severity"] == "CRITICAL"
    assert "Cross-institution dual active enrolment" in dup_002["explanation"]

@pytest.mark.asyncio
async def test_reconciliation_is_idempotent(async_client):
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    r1 = await async_client.post("/api/v1/integrity/reconcile", headers=headers)
    assert r1.status_code == 200

    findings_1 = (await async_client.get("/api/v1/findings", headers=headers)).json()
    total_1 = findings_1["total"]

    r2 = await async_client.post("/api/v1/integrity/reconcile", headers=headers)
    assert r2.status_code == 200

    findings_2 = (await async_client.get("/api/v1/findings", headers=headers)).json()
    total_2 = findings_2["total"]

    # Rerunning reconciliation must not duplicate active findings
    assert total_1 == total_2

@pytest.mark.asyncio
async def test_missing_identifier_does_not_match_on_name_alone(async_client):
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    findings = (await async_client.get("/api/v1/findings", headers=headers)).json()
    for item in findings["items"]:
        # Verify no finding matches on name alone
        assert "Ananya Iyer" not in item["explanation"]
