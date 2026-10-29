from datetime import datetime, timezone
from typing import List, Optional, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update

from app.models.integrity import Notification
from app.models.user import User

class NotificationService:
    @staticmethod
    def _get_access_filter(current_user: User, user_scopes: List[Any], user_roles: List[str]):
        is_national_admin = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in user_roles)
        user_inst_id = user_scopes[0].institution_id if user_scopes else None

        conditions = [Notification.recipient_user_id == current_user.id]
        if is_national_admin:
            conditions.append(Notification.role_target.in_(("NATIONAL_ADMIN", "AICTE_ADMIN", "PLATFORM_ADMIN")))
        if user_inst_id:
            conditions.append(
                and_(
                    Notification.target_institution_id == user_inst_id,
                    or_(
                        Notification.role_target == "INSTITUTION_ADMIN",
                        Notification.role_target.is_(None)
                    )
                )
            )
        return or_(*conditions)

    @staticmethod
    async def get_notifications(
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        access_filter = NotificationService._get_access_filter(current_user, user_scopes, user_roles)
        query = select(Notification).where(access_filter)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_unread_count(
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str]
    ) -> int:
        access_filter = NotificationService._get_access_filter(current_user, user_scopes, user_roles)
        query = select(func.count(Notification.id)).where(
            and_(access_filter, Notification.is_read == False)
        )
        result = await session.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def mark_read(
        session: AsyncSession,
        notification_id: str,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str]
    ) -> Notification:
        access_filter = NotificationService._get_access_filter(current_user, user_scopes, user_roles)
        query = select(Notification).where(and_(Notification.id == notification_id, access_filter))
        result = await session.execute(query)
        notif = result.scalar_one_or_none()
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification '{notification_id}' not found."
            )
        notif.is_read = True
        await session.commit()
        return notif

    @staticmethod
    async def mark_all_read(
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str]
    ) -> int:
        access_filter = NotificationService._get_access_filter(current_user, user_scopes, user_roles)
        stmt = (
            update(Notification)
            .where(and_(access_filter, Notification.is_read == False))
            .values(is_read=True)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount
