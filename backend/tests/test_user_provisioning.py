import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_user_provisioning_and_login(async_client: AsyncClient):
    # 1. Login as AICTE Admin
    admin_login = await async_client.post("/api/v1/auth/login", json={
        "email": "aicte.admin@neev.aicte.gov.in",
        "password": "NeevAdmin@2026"
    })
    assert admin_login.status_code == 200
    token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get an institution ID
    inst_resp = await async_client.get("/api/v1/institutions", headers=headers)
    assert inst_resp.status_code == 200
    inst_id = inst_resp.json()["items"][0]["id"]

    # 3. Provision new institutional admin
    new_email = "nodal.officer@dit.synthetic.edu.in"
    prov_resp = await async_client.post(
        "/api/v1/auth/provision-user",
        headers=headers,
        json={
            "email": new_email,
            "display_name": "Prof. Nodal Officer",
            "role_code": "INSTITUTION_ADMIN",
            "institution_id": inst_id,
            "initial_password": "InitialSecurePass@2026"
        }
    )
    assert prov_resp.status_code == 200
    user_data = prov_resp.json()
    assert user_data["email_normalized"] == new_email
    assert "INSTITUTION_ADMIN" in user_data["roles"]
    assert user_data["scopes"][0]["institution_id"] == inst_id

    # 4. Login with newly provisioned user
    new_login = await async_client.post("/api/v1/auth/login", json={
        "email": new_email,
        "password": "InitialSecurePass@2026"
    })
    assert new_login.status_code == 200
    assert new_login.json()["user"]["email_normalized"] == new_email

    # 5. Duplicate email provisioning rejected
    dup_resp = await async_client.post(
        "/api/v1/auth/provision-user",
        headers=headers,
        json={
            "email": new_email,
            "display_name": "Duplicate Attempt",
            "role_code": "INSTITUTION_ADMIN",
            "institution_id": inst_id,
            "initial_password": "InitialSecurePass@2026"
        }
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["message"]

@pytest.mark.asyncio
async def test_non_admin_cannot_provision_user(async_client: AsyncClient):
    # Login as Institution Admin
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@dit.synthetic.edu.in",
        "password": "DitAdmin@2026"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to provision user
    resp = await async_client.post(
        "/api/v1/auth/provision-user",
        headers=headers,
        json={
            "email": "illegal.user@dit.edu.in",
            "display_name": "Unauthorized User",
            "role_code": "INSTITUTION_ADMIN",
            "initial_password": "SomePassword@2026"
        }
    )
    assert resp.status_code == 403
    assert "Permission denied" in resp.json()["message"]
