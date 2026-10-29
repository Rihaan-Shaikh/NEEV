import pytest

@pytest.mark.asyncio
async def test_national_oversight_dashboard_and_tenant_restriction(async_client):
    # Log in as AICTE National Admin
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 1. Admin accesses national dashboard
    resp = await async_client.get("/api/v1/dashboard/national", headers=admin_headers)
    assert resp.status_code == 200
    metrics = resp.json()
    assert metrics["covered_institutions_count"] >= 2
    assert metrics["programmes_with_intake_count"] >= 2
    assert metrics["total_submitted_enrolments"] >= 10
    assert metrics["total_active_enrolments"] >= 10
    assert 0.0 <= metrics["submission_completion_rate_pct"] <= 100.0
    assert 0.0 <= metrics["required_fields_complete_pct"] <= 100.0
    assert 0.0 <= metrics["valid_format_apaar_pct"] <= 100.0
    assert metrics["unresolved_conflict_findings_count"] >= 1
    assert metrics["open_audit_cases_count"] >= 1
    assert "risk_band_distribution" in metrics
    dist = metrics["risk_band_distribution"]
    assert "ROUTINE" in dist
    assert "WATCH" in dist
    assert "REVIEW_RECOMMENDED" in dist
    assert "PRIORITY_REVIEW" in dist

    # 2. Institution user restricted from national dashboard
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    denied_resp = await async_client.get("/api/v1/dashboard/national", headers=dit_headers)
    assert denied_resp.status_code == 403
    denied_msg = denied_resp.json().get("detail") or denied_resp.json().get("message")
    assert "Access denied" in denied_msg

@pytest.mark.asyncio
async def test_institution_dashboard_metrics_and_isolation(async_client):
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    insts = (await async_client.get("/api/v1/institutions", headers=admin_headers)).json()
    dit_inst = next(i for i in insts["items"] if "Delhi" in i["name"])
    mtu_inst = next(i for i in insts["items"] if "Mumbai" in i["name"])

    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    # 1. DIT user views own dashboard
    dit_resp = await async_client.get(
        f"/api/v1/dashboard/institution/{dit_inst['id']}",
        headers=dit_headers
    )
    assert dit_resp.status_code == 200
    metrics = dit_resp.json()
    assert metrics["institution_id"] == dit_inst["id"]
    assert metrics["total_enrolments_count"] > 0
    assert metrics["active_enrolments_count"] > 0
    assert metrics["programmes_count"] >= 2
    assert "current_risk_band" in metrics
    assert "current_risk_score" in metrics

    # 2. DIT user attempts to view MTU's institution dashboard -> 403 Forbidden
    cross_resp = await async_client.get(
        f"/api/v1/dashboard/institution/{mtu_inst['id']}",
        headers=dit_headers
    )
    assert cross_resp.status_code == 403
    cross_msg = cross_resp.json().get("detail") or cross_resp.json().get("message")
    assert "Access denied" in cross_msg
