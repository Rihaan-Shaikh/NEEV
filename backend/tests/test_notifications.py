import pytest

@pytest.mark.asyncio
async def test_notifications_workflow(async_client):
    # Log in as National Admin
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "aicte.admin@neev.aicte.gov.in", "password": "NeevAdmin@2026"}
    )
    assert login_resp.status_code == 200
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    # Run reconciliation to generate notifications
    await async_client.post("/api/v1/integrity/reconcile", headers=headers)

    # 1. Check unread count
    count_resp = await async_client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_resp.status_code == 200
    assert "unread_count" in count_resp.json()

    # 2. List notifications
    list_resp = await async_client.get("/api/v1/notifications?limit=10", headers=headers)
    assert list_resp.status_code == 200
    notifs = list_resp.json()
    assert isinstance(notifs, list)

    if notifs:
        target_notif = notifs[0]
        notif_id = target_notif["id"]

        # 3. Mark single notification as read
        mark_resp = await async_client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
        assert mark_resp.status_code == 200
        assert mark_resp.json()["is_read"] is True

    # 4. Mark all as read
    mark_all_resp = await async_client.post("/api/v1/notifications/mark-all-read", headers=headers)
    assert mark_all_resp.status_code == 200
    assert mark_all_resp.json()["success"] is True

    # Unread count should now be 0
    final_count = (await async_client.get("/api/v1/notifications/unread-count", headers=headers)).json()
    assert final_count["unread_count"] == 0
