import pytest
import io

@pytest.mark.asyncio
async def test_evidence_upload_and_download_flow(async_client):
    # Log in as National Admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Ensure reconciliation
    await async_client.post("/api/v1/integrity/reconcile", headers=headers)

    findings = (await async_client.get("/api/v1/findings", headers=headers)).json()
    assert findings["total"] >= 1
    finding_id = findings["items"][0]["id"]

    # 1. Valid PDF upload
    pdf_content = b"%PDF-1.4 Mock Transfer Certificate Evidence Content"
    files = {"file": ("transfer_cert.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {"evidence_category": "TRANSFER_CERTIFICATE", "source_provenance": "MANUAL_DOCUMENT_REVIEW"}

    upload_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/evidence",
        headers=headers,
        files=files,
        data=data
    )
    assert upload_resp.status_code == 200
    ev_data = upload_resp.json()
    assert ev_data["original_filename"] == "transfer_cert.pdf"
    assert ev_data["file_size_bytes"] == len(pdf_content)
    assert len(ev_data["sha256_checksum"]) == 64
    evidence_id = ev_data["id"]

    # 2. Download by authorized user
    dl_resp = await async_client.get(f"/api/v1/evidence/{evidence_id}", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.content == pdf_content
    assert dl_resp.headers["content-type"] == "application/pdf"

@pytest.mark.asyncio
async def test_evidence_upload_unsupported_media_type_rejected(async_client):
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    await async_client.post("/api/v1/integrity/reconcile", headers=headers)
    findings = (await async_client.get("/api/v1/findings", headers=headers)).json()
    finding_id = findings["items"][0]["id"]

    # Attempt to upload executable file
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00FakeExePayload"
    files = {"file": ("malicious.exe", io.BytesIO(exe_content), "application/x-msdownload")}
    resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/evidence",
        headers=headers,
        files=files,
        data={"evidence_category": "OTHER", "source_provenance": "INSTITUTION_SUBMISSION"}
    )
    assert resp.status_code == 415
    assert "Unsupported file type" in resp.json()["message"]

@pytest.mark.asyncio
async def test_evidence_cross_tenant_download_prohibited(async_client):
    # Log in as National Admin and upload an evidence for DIT
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    await async_client.post("/api/v1/integrity/reconcile", headers=admin_headers)
    findings = (await async_client.get("/api/v1/findings", headers=admin_headers)).json()
    finding_id = findings["items"][0]["id"]

    # Log in as DIT Admin and upload evidence owned by DIT
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    assert dit_login.status_code == 200
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    pdf_content = b"%PDF-1.4 DIT Specific Verification Document"
    files = {"file": ("dit_doc.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/evidence",
        headers=dit_headers,
        files=files,
        data={"evidence_category": "OTHER", "source_provenance": "INSTITUTION_SUBMISSION"}
    )
    assert upload_resp.status_code == 200
    evidence_id = upload_resp.json()["id"]

    # Log in as MTU Admin and attempt to download DIT's evidence
    mtu_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mtu.synthetic.edu.in", "password": "MtuAdmin@2026"}
    )
    assert mtu_login.status_code == 200
    mtu_headers = {"Authorization": f"Bearer {mtu_login.json()['access_token']}"}

    # If MTU is not the uploader institution for this evidence, access is prohibited
    # In findings with primary DIT and secondary MTU, MTU can only access MTU evidence
    # National admin uploaded on behalf of primary DIT
    unauth_dl = await async_client.get(f"/api/v1/evidence/{evidence_id}", headers=mtu_headers)
    assert unauth_dl.status_code in (403, 404)
