import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_institutional_isolation_enforced(async_client: AsyncClient):
    # 1. Login as DIT Admin (Institution 1)
    dit_login = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@dit.synthetic.edu.in",
        "password": "DitAdmin@2026"
    })
    assert dit_login.status_code == 200
    dit_token = dit_login.json()["access_token"]
    dit_headers = {"Authorization": f"Bearer {dit_token}"}

    # 2. Login as MTU Admin (Institution 2)
    mtu_login = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@mtu.synthetic.edu.in",
        "password": "MtuAdmin@2026"
    })
    assert mtu_login.status_code == 200
    mtu_token = mtu_login.json()["access_token"]
    mtu_headers = {"Authorization": f"Bearer {mtu_token}"}

    # 3. DIT Admin lists institutions - must ONLY see their own institution
    inst_resp = await async_client.get("/api/v1/institutions", headers=dit_headers)
    assert inst_resp.status_code == 200
    inst_data = inst_resp.json()
    assert inst_data["total"] == 1
    assert inst_data["items"][0]["official_institution_code"] == "AICTE-SYNTH-1001"
    dit_inst_id = inst_data["items"][0]["id"]

    # MTU Admin lists institutions - must ONLY see MTU
    mtu_inst_resp = await async_client.get("/api/v1/institutions", headers=mtu_headers)
    assert mtu_inst_resp.status_code == 200
    mtu_inst_data = mtu_inst_resp.json()
    assert mtu_inst_data["total"] == 1
    assert mtu_inst_data["items"][0]["official_institution_code"] == "AICTE-SYNTH-2002"
    mtu_inst_id = mtu_inst_data["items"][0]["id"]

    # 4. CROSS-INSTITUTION OBJECT ACCESS ATTEMPT:
    # DIT Admin attempts to directly access MTU institution detail by ID -> MUST BE REJECTED 403!
    cross_access_resp = await async_client.get(f"/api/v1/institutions/{mtu_inst_id}", headers=dit_headers)
    assert cross_access_resp.status_code == 403
    assert "outside your authorized institutional scope" in cross_access_resp.json()["message"]

    # 5. DIT Admin attempts to access MTU programmes -> MUST BE REJECTED 403!
    cross_progs_resp = await async_client.get(f"/api/v1/institutions/{mtu_inst_id}/programmes", headers=dit_headers)
    assert cross_progs_resp.status_code == 403

    # 6. AICTE Admin with National scope can access both institutions
    aicte_login = await async_client.post("/api/v1/auth/login", json={
        "email": "aicte.admin@neev.aicte.gov.in",
        "password": "NeevAdmin@2026"
    })
    aicte_token = aicte_login.json()["access_token"]
    aicte_headers = {"Authorization": f"Bearer {aicte_token}"}

    national_inst_resp = await async_client.get("/api/v1/institutions", headers=aicte_headers)
    assert national_inst_resp.status_code == 200
    assert national_inst_resp.json()["total"] >= 2
