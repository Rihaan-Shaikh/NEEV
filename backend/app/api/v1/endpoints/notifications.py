from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User
from app.schemas.integrity import NotificationRead, UnreadCountResponse
from app.policies.authorization import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("", response_model=List[NotificationRead])
async def list_notifications(
    is_read: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    items = await NotificationService.get_notifications(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        is_read=is_read,
        limit=limit,
        offset=offset
    )
    return [NotificationRead.model_validate(n) for n in items]

@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    count = await NotificationService.get_unread_count(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles
    )
    return UnreadCountResponse(unread_count=count)

@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    notif = await NotificationService.mark_read(
        session=db,
        notification_id=notification_id,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles
    )
    return NotificationRead.model_validate(notif)

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    updated_count = await NotificationService.mark_all_read(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles
    )
    return {"success": True, "marked_read_count": updated_count}
