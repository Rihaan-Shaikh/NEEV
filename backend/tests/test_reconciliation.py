import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_intake_reconciliation_logic(async_client: AsyncClient):
    # Login as AICTE Admin
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "aicte.admin@neev.aicte.gov.in",
        "password": "NeevAdmin@2026"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch dashboard summary which includes reconciliation items
    dash_resp = await async_client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_resp.status_code == 200
    data = dash_resp.json()

    assert data["institutions_count"] >= 2
    assert data["programmes_count"] >= 5
    assert len(data["reconciliation_items"]) > 0

    items_by_code = {item["official_programme_code"]: item for item in data["reconciliation_items"]}

    # 1. BTECH-CSE: Approved intake 120, active enrolments ~5-7, must be UNDER_CAPACITY
    if "BTECH-CSE" in items_by_code:
        cse_item = items_by_code["BTECH-CSE"]
        assert cse_item["approved_intake"] == 120
        assert not cse_item["is_capacity_exceeded"]
        assert cse_item["reconciliation_status"] in ["UNDER_CAPACITY", "BALANCED"]

    # 2. BTECH-ECE: Approved intake 60, seeded active enrolments 63 -> CAPACITY_EXCEEDED (INT-002)!
    if "BTECH-ECE" in items_by_code:
        ece_item = items_by_code["BTECH-ECE"]
        assert ece_item["approved_intake"] == 60
        assert ece_item["is_capacity_exceeded"]
        assert ece_item["reconciliation_status"] == "CAPACITY_EXCEEDED"
        assert ece_item["variance"] > 0
        assert "INT-002" in ece_item["rule_basis"]

    # 3. MTECH-AI: Missing approved intake reference -> MISSING_REFERENCE (INT-001)!
    if "MTECH-AI" in items_by_code:
        ai_item = items_by_code["MTECH-AI"]
        assert ai_item["approved_intake"] is None
        assert ai_item["reconciliation_status"] == "MISSING_REFERENCE"
        assert "INT-001" in ai_item["rule_basis"]
