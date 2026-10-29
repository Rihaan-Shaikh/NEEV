import pytest
from app.services.reporting_service import ReportingService

def test_csv_formula_injection_neutralization():
    """Verify formula injection characters (=, +, -, @, \\t, \\r) are safely escaped."""
    assert ReportingService.sanitize_csv_cell("=cmd|'/C calc'!A0") == "'=cmd|'/C calc'!A0"
    assert ReportingService.sanitize_csv_cell("+12345") == "'+12345"
    assert ReportingService.sanitize_csv_cell("-99.99") == "'-99.99"
    assert ReportingService.sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert ReportingService.sanitize_csv_cell("\tTabPrefix") == "'\tTabPrefix"
    assert ReportingService.sanitize_csv_cell("Standard College Name") == "Standard College Name"
    assert ReportingService.sanitize_csv_cell(12345) == "12345"

@pytest.mark.asyncio
async def test_reports_catalog_generation_and_download(async_client):
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 1. Fetch catalog
    cat_resp = await async_client.get("/api/v1/reports", headers=admin_headers)
    assert cat_resp.status_code == 200
    catalog = cat_resp.json()
    assert len(catalog) >= 10
    types = [c["report_type"] for c in catalog]
    assert "ENROLMENT_RECONCILIATION" in types
    assert "PROGRAMME_INTAKE_VARIANCE" in types
    assert "DATA_QUALITY_SUMMARY" in types
    assert "IDENTIFIER_COVERAGE" in types
    assert "DUPLICATE_CONFLICT_FINDINGS" in types
    assert "FINDING_RESOLUTION_PERFORMANCE" in types
    assert "SUBMISSION_TIMELINESS" in types
    assert "AUDIT_CASE_STATUS_OUTCOMES" in types
    assert "HISTORICAL_RECORD_CHANGES" in types
    assert "STATE_PROGRAMME_AGGREGATES" in types

    # 2. Generate report
    job_resp = await async_client.post(
        "/api/v1/reports",
        headers=admin_headers,
        json={"report_type": "ENROLMENT_RECONCILIATION", "export_format": "CSV"}
    )
    assert job_resp.status_code in [200, 201]
    job = job_resp.json()
    assert job["status"] == "COMPLETED"
    assert job["file_size_bytes"] is not None
    job_id = job["id"]

    # 3. Download report
    dl_resp = await async_client.get(f"/api/v1/reports/{job_id}/download", headers=admin_headers)
    assert dl_resp.status_code == 200
    content = dl_resp.text
    assert "Institution Code" in content
    assert "Institution Name" in content
    assert "State" in content

@pytest.mark.asyncio
async def test_report_download_tenant_isolation(async_client):
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

    # Admin creates national report (not scoped to DIT)
    job = (await async_client.post(
        "/api/v1/reports",
        headers=admin_headers,
        json={"report_type": "STATE_PROGRAMME_AGGREGATES", "export_format": "CSV"}
    )).json()

    # DIT user attempts to download national report -> 403 Forbidden
    resp = await async_client.get(f"/api/v1/reports/{job['id']}/download", headers=dit_headers)
    assert resp.status_code == 403
    err_msg = resp.json().get("detail") or resp.json().get("message")
    assert "Access denied" in err_msg
