import pytest

@pytest.mark.asyncio
async def test_case_creation_and_rationale_enforcement(async_client):
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    admin_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    insts = (await async_client.get("/api/v1/institutions", headers=admin_headers)).json()
    dit_id = insts["items"][0]["id"]

    # 1. Reject case creation without rationale
    bad_resp = await async_client.post(
        "/api/v1/audit-cases",
        headers=admin_headers,
        json={
            "institution_id": dit_id,
            "case_category": "REGULATORY_REVIEW",
            "priority": "HIGH",
            "creation_rationale": "short"  # < 10 characters
        }
    )
    assert bad_resp.status_code in [400, 422]
    bad_msg = bad_resp.json().get("detail") or bad_resp.json().get("message")
    assert "at least 10 characters" in bad_msg

    # 2. Successful case creation
    create_resp = await async_client.post(
        "/api/v1/audit-cases",
        headers=admin_headers,
        json={
            "institution_id": dit_id,
            "case_category": "REGULATORY_REVIEW",
            "priority": "HIGH",
            "creation_rationale": "Initiating formal regulatory review due to repeated intake capacity warnings."
        }
    )
    assert create_resp.status_code in [200, 201]
    case_data = create_resp.json()
    assert case_data["case_reference"].startswith("CASE-")
    assert case_data["status"] == "OPEN"
    assert case_data["institution_id"] == dit_id

@pytest.mark.asyncio
async def test_case_assignment_and_state_transitions(async_client):
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    admin_user_id = login_resp.json()["user"]["id"]

    # Create new case
    insts = (await async_client.get("/api/v1/institutions", headers=admin_headers)).json()
    case = (await async_client.post(
        "/api/v1/audit-cases",
        headers=admin_headers,
        json={
            "institution_id": insts["items"][0]["id"],
            "case_category": "CAPACITY_EXCEEDED",
            "priority": "MEDIUM",
            "creation_rationale": "Capacity discrepancy flagged during admission reconciliation audit."
        }
    )).json()
    case_id = case["id"]

    # 1. Assignment
    assign_resp = await async_client.patch(
        f"/api/v1/audit-cases/{case_id}/assignment",
        headers=admin_headers,
        json={"reviewer_id": admin_user_id, "rationale": "Assigned to primary audit officer."}
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["assigned_reviewer_id"] == admin_user_id
    assert assign_resp.json()["status"] == "ASSIGNED"

    # 2. Illegal transition test (WF-001): ASSIGNED -> RESOLVED without review
    illegal_resp = await async_client.post(
        f"/api/v1/audit-cases/{case_id}/events",
        headers=admin_headers,
        json={"target_status": "RESOLVED", "rationale": "Premature closure attempt"}
    )
    assert illegal_resp.status_code in [400, 422]
    ill_msg = illegal_resp.json().get("detail") or illegal_resp.json().get("message")
    assert "WF-001" in ill_msg

    # 3. Permitted transition: ASSIGNED -> UNDER_REVIEW
    review_resp = await async_client.post(
        f"/api/v1/audit-cases/{case_id}/events",
        headers=admin_headers,
        json={"target_status": "UNDER_REVIEW", "rationale": "Commencing evidentiary review"}
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "UNDER_REVIEW"

    # 4. Record decision without rationale (WF-002) -> 400
    no_rat_resp = await async_client.post(
        f"/api/v1/audit-cases/{case_id}/decisions",
        headers=admin_headers,
        json={"decision_type": "RESOLVED", "decision_rationale": "ok"}  # < 10 chars
    )
    assert no_rat_resp.status_code in [400, 422]
    no_msg = no_rat_resp.json().get("detail") or no_rat_resp.json().get("message")
    assert "WF-002" in no_msg

    # 5. Record valid decision -> 200, status becomes RESOLVED
    decision_resp = await async_client.post(
        f"/api/v1/audit-cases/{case_id}/decisions",
        headers=admin_headers,
        json={
            "decision_type": "RESOLVED",
            "decision_rationale": "Institution submitted approved revised sanction orders from the state government. Roster cleared.",
            "follow_up_action": "Record closure and schedule routine follow-up."
        }
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["decision_type"] == "RESOLVED"
    updated_case = (await async_client.get(f"/api/v1/audit-cases/{case_id}", headers=admin_headers)).json()
    assert updated_case["status"] == "RESOLVED"
    assert updated_case["closed_at"] is not None

@pytest.mark.asyncio
async def test_clarification_workflow_and_cross_tenant_isolation(async_client):
    # Log in as Admin
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # Log in as DIT Admin
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    # Log in as MTU Admin
    mtu_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mtu.synthetic.edu.in", "password": "MtuAdmin@2026"}
    )
    mtu_headers = {"Authorization": f"Bearer {mtu_login.json()['access_token']}"}

    # Get DIT institution ID
    insts = (await async_client.get("/api/v1/institutions", headers=admin_headers)).json()
    dit_inst = next(i for i in insts["items"] if "Delhi" in i["name"])

    # Create case for DIT
    case = (await async_client.post(
        "/api/v1/audit-cases",
        headers=admin_headers,
        json={
            "institution_id": dit_inst["id"],
            "case_category": "DATA_DISCREPANCY",
            "priority": "HIGH",
            "creation_rationale": "Cross-institution duplicate student detected requiring clarification."
        }
    )).json()

    # Move to UNDER_REVIEW
    await async_client.post(
        f"/api/v1/audit-cases/{case['id']}/events",
        headers=admin_headers,
        json={"target_status": "UNDER_REVIEW", "rationale": "Transition to active review"}
    )

    # 1. Issue clarification request
    clr_resp = await async_client.post(
        f"/api/v1/audit-cases/{case['id']}/clarification-requests",
        headers=admin_headers,
        json={
            "subject": "Verification of Student Migration Documentation",
            "information_requested": "Please submit certified migration certificate confirming date of admission cancellation."
        }
    )
    assert clr_resp.status_code in [200, 201]
    clr = clr_resp.json()
    assert clr["status"] == "PENDING_RESPONSE"
    clr_id = clr["id"]

    # 2. MTU tries to respond to DIT's clarification request -> 403 Forbidden
    mtu_resp = await async_client.post(
        f"/api/v1/clarification-requests/{clr_id}/respond",
        headers=mtu_headers,
        json={"explanation": "Unauthorized cross-tenant attempt"}
    )
    assert mtu_resp.status_code == 403
    mtu_msg = mtu_resp.json().get("detail") or mtu_resp.json().get("message")
    assert "Access denied" in mtu_msg

    # 3. DIT responds to own clarification request -> 200 OK
    dit_resp = await async_client.post(
        f"/api/v1/clarification-requests/{clr_id}/respond",
        headers=dit_headers,
        json={
            "explanation": "Student migration confirmed; copy of stamped release certificate has been archived."
        }
    )
    assert dit_resp.status_code == 200
    assert dit_resp.json()["status"] in ["RESPONSE_RECEIVED", "RESPONDED"]

    # Case status should now be RESPONSE_RECEIVED
    updated_case = (await async_client.get(f"/api/v1/audit-cases/{case['id']}", headers=admin_headers)).json()
    assert updated_case["status"] == "RESPONSE_RECEIVED"

@pytest.mark.asyncio
async def test_internal_reviewer_notes_confidentiality(async_client):
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    # Fetch seeded case 1 (DIT case)
    cases = (await async_client.get("/api/v1/audit-cases", headers=admin_headers)).json()
    dit_case = next(c for c in cases["items"] if "CASE-2026-0001" in c["case_reference"])

    # Admin posts a confidential reviewer note
    note_resp = await async_client.post(
        f"/api/v1/audit-cases/{dit_case['id']}/notes",
        headers=admin_headers,
        json={
            "note": "CONFIDENTIAL: Suspected fraudulent migration certificate; pending verification with state board.",
            "is_internal": True
        }
    )
    assert note_resp.status_code == 200

    # Admin workspace view sees confidential event
    admin_workspace = (await async_client.get(f"/api/v1/audit-cases/{dit_case['id']}", headers=admin_headers)).json()
    admin_event_notes = [e["description"] for e in admin_workspace["events"]]
    assert any("CONFIDENTIAL: Suspected fraudulent" in n for n in admin_event_notes)

    # Institution user workspace view MUST NOT see confidential notes
    dit_workspace = (await async_client.get(f"/api/v1/audit-cases/{dit_case['id']}", headers=dit_headers)).json()
    dit_event_notes = [e["description"] for e in dit_workspace["events"]]
    assert not any("CONFIDENTIAL" in n for n in dit_event_notes)
