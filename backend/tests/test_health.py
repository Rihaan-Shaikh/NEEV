import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_live_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "live"

    v1_resp = await async_client.get("/api/v1/health/live")
    assert v1_resp.status_code == 200
    assert v1_resp.json()["status"] == "live"

@pytest.mark.asyncio
async def test_health_ready_postgresql_connected(async_client: AsyncClient):
    resp = await async_client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"

    v1_resp = await async_client.get("/api/v1/health/ready")
    assert v1_resp.status_code == 200
    assert v1_resp.json()["database"] == "connected"

@pytest.mark.asyncio
async def test_unknown_api_route_structured_json_404(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/unknown-endpoint-route")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error_code"] == "HTTP_404"
    assert "Not Found" in data["message"]
