import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_forgot_password_generic_response(async_client: AsyncClient):
    # Valid user
    resp = await async_client.post("/api/v1/auth/forgot-password", json={
        "email": "aicte.admin@neev.aicte.gov.in"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "instructions have been initiated" in data["message"]
    assert "dev_reset_token" in data

    # Non-existent user gets identical message
    resp_nonexistent = await async_client.post("/api/v1/auth/forgot-password", json={
        "email": "ghost.user@unknown.org"
    })
    assert resp_nonexistent.status_code == 200
    assert resp_nonexistent.json()["message"] == data["message"]
    assert "dev_reset_token" not in resp_nonexistent.json()

@pytest.mark.asyncio
async def test_password_reset_flow_and_session_invalidation(async_client: AsyncClient):
    # 1. Login first to establish an active refresh session
    login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@mtu.synthetic.edu.in",
        "password": "MtuAdmin@2026"
    })
    assert login_resp.status_code == 200
    old_cookies = login_resp.cookies

    # 2. Request password reset
    forgot_resp = await async_client.post("/api/v1/auth/forgot-password", json={
        "email": "admin@mtu.synthetic.edu.in"
    })
    assert forgot_resp.status_code == 200
    reset_token = forgot_resp.json().get("dev_reset_token")
    assert reset_token is not None

    # 3. Reset password with new password
    new_password = "BrandNewPassword@2026!"
    reset_resp = await async_client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": new_password
    })
    assert reset_resp.status_code == 200
    assert "successfully updated" in reset_resp.json()["message"]

    # 4. Old refresh session should now be invalidated/revoked
    old_refresh_resp = await async_client.post("/api/v1/auth/refresh", cookies=old_cookies)
    assert old_refresh_resp.status_code == 401

    # 5. Old password should fail
    old_login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@mtu.synthetic.edu.in",
        "password": "MtuAdmin@2026"
    })
    assert old_login_resp.status_code == 401

    # 6. New password should succeed
    new_login_resp = await async_client.post("/api/v1/auth/login", json={
        "email": "admin@mtu.synthetic.edu.in",
        "password": new_password
    })
    assert new_login_resp.status_code == 200

    # 7. Reusing reset token must fail
    reuse_token_resp = await async_client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "YetAnotherPassword@2026!"
    })
    assert reuse_token_resp.status_code == 400
    assert "Invalid or already used" in reuse_token_resp.json()["message"]

@pytest.mark.asyncio
async def test_password_reset_short_password_rejected(async_client: AsyncClient):
    resp = await async_client.post("/api/v1/auth/reset-password", json={
        "token": "fake-token-12345",
        "new_password": "short"
    })
    assert resp.status_code == 400
    assert "at least 8 characters" in resp.json()["message"]
