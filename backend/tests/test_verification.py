import pytest

@pytest.mark.asyncio
async def test_verification_reference_issuance_and_disclosure(async_client):
    # Log in as DIT institution admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch enrolments to pick a record
    enrol_resp = await async_client.get("/api/v1/enrolments?limit=5", headers=headers)
    assert enrol_resp.status_code == 200
    enrol_items = enrol_resp.json().get("items", [])
    assert len(enrol_items) > 0
    record_id = enrol_items[0]["id"]

    # Issue verification reference
    issue_payload = {
        "enrolment_record_id": record_id,
        "purpose": "Employment Verification",
        "disclosure_profile": {
            "disclose_student_name": True,
            "disclose_programme": True,
            "disclose_enrolment_status": True,
            "disclose_academic_year": True,
            "disclose_institution": True,
            "disclose_admission_date": False
        },
        "expires_in_days": 30,
        "max_uses": 2
    }
    issue_resp = await async_client.post("/api/v1/verification-references", json=issue_payload, headers=headers)
    assert issue_resp.status_code == 200 or issue_resp.status_code == 201
    issued_data = issue_resp.json()

    # Raw bearer token must be provided exactly once upon issuance
    raw_token = issued_data.get("raw_bearer_token")
    assert raw_token is not None
    assert raw_token.startswith("neev_vrf_")
    assert issued_data["public_reference_code"].startswith("VRF-2026-")
    assert issued_data["status"] == "ACTIVE"
    assert issued_data["use_count"] == 0
    assert issued_data["max_uses"] == 2

    # Query details endpoint - ensure raw bearer token is NEVER exposed again
    ref_id = issued_data["id"]
    detail_resp = await async_client.get(f"/api/v1/verification-references/{ref_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data.get("raw_bearer_token") is None
    assert detail_data["public_reference_code"] == issued_data["public_reference_code"]


@pytest.mark.asyncio
async def test_verification_resolution_and_synthetic_disclaimer(async_client):
    # Log in as DIT institution admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Fetch enrolment
    enrol_resp = await async_client.get("/api/v1/enrolments?limit=1", headers=headers)
    record_id = enrol_resp.json()["items"][0]["id"]

    # Issue single-use reference
    issue_payload = {
        "enrolment_record_id": record_id,
        "purpose": "Bank Loan Clearance",
        "disclosure_profile": {
            "disclose_student_name": True,
            "disclose_programme": True,
            "disclose_enrolment_status": True,
            "disclose_academic_year": True,
            "disclose_institution": True,
            "disclose_admission_date": False
        },
        "expires_in_days": 10,
        "max_uses": 1
    }
    issue_resp = await async_client.post("/api/v1/verification-references", json=issue_payload, headers=headers)
    assert issue_resp.status_code in [200, 201]
    raw_token = issue_resp.json()["raw_bearer_token"]
    public_code = issue_resp.json()["public_reference_code"]

    # 1. Resolve verification via public verification endpoint (no auth header needed)
    verify_payload = {
        "reference_token": raw_token
    }
    verify_resp = await async_client.post("/api/v1/verify", json=verify_payload)
    assert verify_resp.status_code == 200
    res_data = verify_resp.json()

    assert res_data["outcome"] == "SUCCESS"
    assert res_data["public_reference_code"] == public_code
    assert "Synthetic demonstration — not an official APAAR verification." in res_data["synthetic_disclaimer"]
    
    # Assert claims minimized: student name, programme, institution; no raw APAAR
    disclosed = res_data["disclosed_claims"]
    assert "student_full_name" in disclosed
    assert "programme_name" in disclosed
    assert "institution_name" in disclosed
    assert "apaar_id" not in disclosed
    assert "apaar_number" not in disclosed

    # 2. Second verification must result in USE_LIMIT_EXCEEDED because max_uses was 1
    verify_resp_2 = await async_client.post("/api/v1/verify", json=verify_payload)
    assert verify_resp_2.status_code == 200
    res_data_2 = verify_resp_2.json()
    assert res_data_2["outcome"] == "USE_LIMIT_EXCEEDED"
    assert "limit" in res_data_2["message"].lower()


@pytest.mark.asyncio
async def test_verification_revocation_workflow(async_client):
    # Log in as DIT admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    enrol_resp = await async_client.get("/api/v1/enrolments?limit=1", headers=headers)
    record_id = enrol_resp.json()["items"][0]["id"]

    issue_resp = await async_client.post(
        "/api/v1/verification-references",
        headers=headers,
        json={
            "enrolment_record_id": record_id,
            "purpose": "Scholarship Review",
            "expires_in_days": 15,
            "max_uses": 5
        }
    )
    assert issue_resp.status_code in [200, 201]
    ref_id = issue_resp.json()["id"]
    raw_token = issue_resp.json()["raw_bearer_token"]

    # Reject revocation with empty/short rationale (< 5 chars)
    bad_revoke = await async_client.post(
        f"/api/v1/verification-references/{ref_id}/revoke",
        headers=headers,
        json={"revocation_reason": "no"}
    )
    assert bad_revoke.status_code in [400, 422]

    # Valid revocation
    revoke_resp = await async_client.post(
        f"/api/v1/verification-references/{ref_id}/revoke",
        headers=headers,
        json={"revocation_reason": "Applicant requested immediate invalidation due to changed scholarship application."}
    )
    assert revoke_resp.status_code == 200
    revoked_data = revoke_resp.json()
    assert revoked_data["status"] == "REVOKED"
    assert revoked_data["revocation_reason"] is not None

    # Verification attempt against revoked reference must return REVOKED outcome
    verify_resp = await async_client.post(
        "/api/v1/verify",
        json={"reference_token": raw_token}
    )
    assert verify_resp.status_code == 200
    res_data = verify_resp.json()
    assert res_data["outcome"] == "REVOKED"
    assert "revoked" in res_data["message"].lower()


@pytest.mark.asyncio
async def test_verification_cross_tenant_isolation(async_client):
    # Login as AICTE admin to get two different institutions
    aicte_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    aicte_headers = {"Authorization": f"Bearer {aicte_login.json()['access_token']}"}
    insts = (await async_client.get("/api/v1/institutions", headers=aicte_headers)).json()["items"]
    assert len(insts) >= 2
    mtu_inst = insts[1]

    # Get an enrolment from MTU
    mtu_enrols = (await async_client.get(f"/api/v1/enrolments?institution_id={mtu_inst['id']}&limit=1", headers=aicte_headers)).json()["items"]
    assert len(mtu_enrols) > 0
    mtu_record_id = mtu_enrols[0]["id"]

    # Now login as DIT institutional admin
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    # Attempt to issue reference for MTU record using DIT credentials -> must be rejected (403 or 404)
    cross_issue = await async_client.post(
        "/api/v1/verification-references",
        headers=dit_headers,
        json={
            "enrolment_record_id": mtu_record_id,
            "purpose": "Cross Tenant Unauthorized Attempt",
            "expires_in_days": 10
        }
    )
    assert cross_issue.status_code in [403, 404]
