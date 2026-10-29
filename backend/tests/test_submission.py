import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_submission_workflow_and_idempotency(async_client: AsyncClient):
    # 1. Login as DIT Admin
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@dit.synthetic.edu.in",
        "password": "DitAdmin@2026"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get DIT Institution ID and Academic Year ID
    inst_resp = await async_client.get("/api/v1/institutions", headers=headers)
    inst_id = inst_resp.json()["items"][0]["id"]

    ay_resp = await async_client.get("/api/v1/academic-years", headers=headers)
    ay_id = ay_resp.json()[0]["id"]

    # 3. Create submission batch
    batch_resp = await async_client.post("/api/v1/batches", json={
        "institution_id": inst_id,
        "academic_year_id": ay_id,
        "submission_type": "REGULAR_ENROLMENT"
    }, headers=headers)
    assert batch_resp.status_code == 201
    batch_data = batch_resp.json()
    batch_id = batch_data["id"]
    assert batch_data["processing_status"] == "CREATED"

    # 4. Upload valid CSV file
    csv_content = (
        "institution_student_id,student_full_name,admission_date,enrolment_status,programme_code,admission_category,apaar_id\n"
        "DIT-2024-TEST-101,John Doe,2024-07-20,ACTIVE,BTECH-CSE,OPEN,100120045901\n"
        "DIT-2024-TEST-102,Jane Smith,2024-07-21,ACTIVE,BTECH-CSE,OBC,100120045902\n"
    )

    upload_resp = await async_client.post(
        f"/api/v1/batches/{batch_id}/file",
        files={"file": ("roster.csv", csv_content.encode("utf-8"), "text/csv")},
        headers=headers
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["processing_status"] == "VALIDATED"
    assert upload_data["row_count"] == 2
    assert upload_data["valid_count"] == 2
    assert upload_data["rejected_count"] == 0

    # 5. Fetch preview
    preview_resp = await async_client.get(f"/api/v1/batches/{batch_id}/preview", headers=headers)
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["total_rows"] == 2
    assert len(preview_data["rows"]) == 2
    assert preview_data["rows"][0]["processing_status"] in ["VALID", "WARNING"]

    # 6. Finalize batch
    finalize_resp = await async_client.post(f"/api/v1/batches/{batch_id}/finalize", headers=headers)
    assert finalize_resp.status_code == 200
    fin_data = finalize_resp.json()
    assert fin_data["status"] == "FINALIZED"
    assert fin_data["accepted_count"] == 2
    receipt_ref = fin_data["receipt_reference"]
    assert receipt_ref.startswith("NEEV-RCPT-")

    # 7. Test Idempotency: Repeating finalization must NOT duplicate records or error
    repeat_fin = await async_client.post(f"/api/v1/batches/{batch_id}/finalize", headers=headers)
    assert repeat_fin.status_code == 200
    assert repeat_fin.json()["receipt_reference"] == receipt_ref
    assert "idempotent" in repeat_fin.json()["message"].lower()

    # 8. Fetch Receipt
    receipt_resp = await async_client.get(f"/api/v1/batches/{batch_id}/receipt", headers=headers)
    assert receipt_resp.status_code == 200
    assert receipt_resp.json()["receipt_reference"] == receipt_ref
    assert receipt_resp.json()["summary_snapshot"]["accepted_count"] == 2

    # 9. Verify canonical enrolment records were created and are searchable
    enr_resp = await async_client.get(
        "/api/v1/enrolments?search=DIT-2024-TEST-101",
        headers=headers
    )
    assert enr_resp.status_code == 200
    enr_data = enr_resp.json()
    assert enr_data["total"] >= 1
    record = enr_data["items"][0]
    assert record["institution_student_id"] == "DIT-2024-TEST-101"
    # APAAR ID must be masked by default
    assert "••••-••••-" in record["masked_apaar_id"]
