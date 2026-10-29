import pytest

@pytest.mark.asyncio
async def test_finding_lifecycle_transitions_and_rationale(async_client):
    # Log in as national admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Ensure reconciliation has run
    await async_client.post("/api/v1/integrity/reconcile", headers=headers)

    findings = (await async_client.get("/api/v1/findings?status=OPEN", headers=headers)).json()
    assert findings["total"] >= 1
    finding_id = findings["items"][0]["id"]

    # 1. Invalid transition test: OPEN -> RESOLVED directly without review (WF-001)
    invalid_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/transition",
        headers=headers,
        json={"target_status": "RESOLVED", "rationale": "Direct resolution not allowed"}
    )
    assert invalid_resp.status_code == 400
    assert "WF-001" in invalid_resp.json()["message"]

    # 2. Permitted transition: OPEN -> UNDER_REVIEW
    t1_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/transition",
        headers=headers,
        json={"target_status": "UNDER_REVIEW"}
    )
    assert t1_resp.status_code == 200
    assert t1_resp.json()["status"] == "UNDER_REVIEW"

    # 3. Terminal transition without rationale rejected (WF-002)
    no_rat_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/transition",
        headers=headers,
        json={"target_status": "RESOLVED", "rationale": ""}
    )
    assert no_rat_resp.status_code == 422
    assert "WF-002" in no_rat_resp.json()["message"]

    # 4. Valid terminal transition with rationale
    resolve_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/transition",
        headers=headers,
        json={
            "target_status": "RESOLVED",
            "rationale": "Documented transfer certificate verified by national regulatory review board."
        }
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert resolve_resp.json()["resolution_rationale"] is not None

@pytest.mark.asyncio
async def test_institution_user_cannot_resolve_finding(async_client):
    # Log in as National Admin to get an OPEN finding
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # Ensure reconciliation has run
    await async_client.post("/api/v1/integrity/reconcile", headers=admin_headers)

    findings = (await async_client.get("/api/v1/findings", headers=admin_headers)).json()
    assert findings["total"] >= 1
    finding_id = findings["items"][0]["id"]

    # Log in as DIT Institution Admin
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    assert dit_login.status_code == 200
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    # Attempt to resolve finding
    unauth_resolve = await async_client.post(
        f"/api/v1/findings/{finding_id}/transition",
        headers=dit_headers,
        json={"target_status": "RESOLVED", "rationale": "Institution attempting self-resolution"}
    )
    assert unauth_resolve.status_code in (400, 403)

@pytest.mark.asyncio
async def test_submit_institutional_response(async_client):
    # Log in as National Admin to ensure reconciliation
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    await async_client.post("/api/v1/integrity/reconcile", headers=admin_headers)

    # Log in as DIT Institution Admin
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    assert dit_login.status_code == 200
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    findings = (await async_client.get("/api/v1/findings", headers=dit_headers)).json()
    assert findings["total"] >= 1
    finding_id = findings["items"][0]["id"]

    # Submit response
    resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/responses",
        headers=dit_headers,
        json={
            "response_type": "EXPLANATION",
            "explanation": "Student has completed their transfer formalities on 2024-07-28 and TC has been dispatched."
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["response_type"] == "EXPLANATION"
    assert "transfer formalities" in data["explanation"]
