import pytest

@pytest.mark.asyncio
async def test_enrolment_correction_creates_version_and_history(async_client):
    # Log in as national admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Get a list of enrolments to pick one
    enr_list = (await async_client.get("/api/v1/enrolments?page_size=5", headers=headers)).json()
    record = enr_list["items"][0]
    rec_id = record["id"]

    # 1. Test HIS-001: Missing or too short correction reason rejected
    bad_reason_resp = await async_client.post(
        f"/api/v1/enrolments/{rec_id}/corrections",
        headers=headers,
        json={
            "expected_version": 1,
            "correction_reason": "short",
            "enrolment_status": "ACTIVE"
        }
    )
    assert bad_reason_resp.status_code == 422
    assert "HIS-001" in bad_reason_resp.json()["message"]

    # 2. Test HIS-002: Stale expected version rejected with 409 Conflict
    stale_resp = await async_client.post(
        f"/api/v1/enrolments/{rec_id}/corrections",
        headers=headers,
        json={
            "expected_version": 999,  # Stale version
            "correction_reason": "Updating admission category after document verification",
            "admission_category": "OBC"
        }
    )
    assert stale_resp.status_code == 409
    assert "HIS-002" in stale_resp.json()["message"]

    # 3. Valid correction
    corr_resp = await async_client.post(
        f"/api/v1/enrolments/{rec_id}/corrections",
        headers=headers,
        json={
            "expected_version": 1,
            "correction_reason": "Updating admission category after document verification",
            "admission_category": "OBC"
        }
    )
    assert corr_resp.status_code == 200
    corr_data = corr_resp.json()
    assert corr_data["success"] is True
    assert corr_data["new_version"] == 2

    # 4. Fetch history and verify version 1 snapshot is preserved
    hist_resp = await async_client.get(f"/api/v1/enrolments/{rec_id}/history", headers=headers)
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["current_version"] == 2
    assert len(hist_data["versions"]) >= 1
    assert hist_data["versions"][0]["version_number"] == 1
    assert "Updating admission category" in hist_data["versions"][0]["change_reason"]

@pytest.mark.asyncio
async def test_tenant_cannot_correct_other_institution_record(async_client):
    # Log in as National Admin first to find an MTU record
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    enr_list = (await async_client.get("/api/v1/enrolments?search=MTU", headers=admin_headers)).json()
    mtu_record = next((r for r in enr_list["items"] if "MTU" in r["institution_student_id"]), None)
    assert mtu_record is not None
    mtu_rec_id = mtu_record["id"]

    # Now log in as DIT admin and attempt to modify MTU's record
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    assert dit_login.status_code == 200
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    unauth_resp = await async_client.post(
        f"/api/v1/enrolments/{mtu_rec_id}/corrections",
        headers=dit_headers,
        json={
            "expected_version": 1,
            "correction_reason": "Attempting unauthorized cross-tenant correction",
            "enrolment_status": "WITHDRAWN"
        }
    )
    assert unauth_resp.status_code == 403
