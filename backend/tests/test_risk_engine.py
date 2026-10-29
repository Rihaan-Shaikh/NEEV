import pytest
from app.services.risk_engine_service import RiskEngineService

def test_risk_band_boundaries():
    """Verify deterministic boundary thresholds for all 4 risk bands."""
    assert RiskEngineService.determine_risk_band(0.0) == "ROUTINE"
    assert RiskEngineService.determine_risk_band(19.9) == "ROUTINE"
    assert RiskEngineService.determine_risk_band(20.0) == "WATCH"
    assert RiskEngineService.determine_risk_band(39.9) == "WATCH"
    assert RiskEngineService.determine_risk_band(40.0) == "REVIEW_RECOMMENDED"
    assert RiskEngineService.determine_risk_band(69.9) == "REVIEW_RECOMMENDED"
    assert RiskEngineService.determine_risk_band(70.0) == "PRIORITY_REVIEW"
    assert RiskEngineService.determine_risk_band(100.0) == "PRIORITY_REVIEW"

@pytest.mark.asyncio
async def test_risk_calculation_endpoints_and_history(async_client):
    # Log in as AICTE Admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    admin_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # 1. Fetch risk review queue
    queue_resp = await async_client.get("/api/v1/risk-queue", headers=admin_headers)
    assert queue_resp.status_code == 200
    queue_data = queue_resp.json()
    assert "items" in queue_data
    assert queue_data["total"] >= 1
    
    first_item = queue_data["items"][0]
    institution_id = first_item["institution_id"]
    assert "total_score" in first_item
    assert "risk_band" in first_item
    assert first_item["risk_band"] in ["ROUTINE", "WATCH", "REVIEW_RECOMMENDED", "PRIORITY_REVIEW"]

    # 2. Fetch institution risk profile
    profile_resp = await async_client.get(
        f"/api/v1/institutions/{institution_id}/risk-profile",
        headers=admin_headers
    )
    assert profile_resp.status_code == 200
    profile = profile_resp.json()
    assert profile["institution_id"] == institution_id
    assert "current_calculation" in profile
    calc = profile["current_calculation"]
    assert calc["calculation_version"] == "1.0.0"
    assert 0.0 <= calc["total_score"] <= 100.0
    assert "factors" in calc
    assert "capacity_discrepancy" in calc["factors"]
    assert "unresolved_conflicts" in calc["factors"]

    initial_calc_id = calc["id"]

    # 3. Recalculate risk to verify versioned history preservation
    recalc_resp = await async_client.post(
        f"/api/v1/institutions/{institution_id}/recalculate-risk",
        headers=admin_headers
    )
    assert recalc_resp.status_code == 200
    new_calc = recalc_resp.json()
    assert new_calc["id"] != initial_calc_id
    assert new_calc["calculation_version"] == "1.0.0"

    # Verify history now contains both calculations
    profile_after = (await async_client.get(
        f"/api/v1/institutions/{institution_id}/risk-profile",
        headers=admin_headers
    )).json()
    history_ids = [h["id"] for h in profile_after["history"]]
    assert initial_calc_id in history_ids

    # 4. Fetch specific calculation by ID
    calc_resp = await async_client.get(
        f"/api/v1/risk-calculations/{initial_calc_id}",
        headers=admin_headers
    )
    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()
    assert calc_data["id"] == initial_calc_id
    assert "input_snapshot" in calc_data
    assert "explanation" in calc_data

@pytest.mark.asyncio
async def test_institution_user_cannot_access_other_institution_risk_profile(async_client):
    # Log in as DIT Admin
    dit_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@dit.synthetic.edu.in", "password": "DitAdmin@2026"}
    )
    assert dit_login.status_code == 200
    dit_headers = {"Authorization": f"Bearer {dit_login.json()['access_token']}"}

    # Fetch institutions to get MTU id
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    insts = (await async_client.get("/api/v1/institutions", headers=admin_headers)).json()
    mtu = next(i for i in insts["items"] if "Mumbai" in i["name"])

    # DIT user attempts to view MTU risk profile -> must return 403 Forbidden
    resp = await async_client.get(
        f"/api/v1/institutions/{mtu['id']}/risk-profile",
        headers=dit_headers
    )
    assert resp.status_code == 403
    err_msg = resp.json().get("detail") or resp.json().get("message")
    assert "Access denied" in err_msg
