from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.db.session import get_db
from app.models.user import User
from app.models.audit import AuditEvent
from app.policies.authorization import get_current_user, get_user_permitted_institution_ids

router = APIRouter()

class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: Optional[str] = None
    actor_email: Optional[str] = None
    actor_type: str
    action: str
    target_type: str
    target_id: Optional[str] = None
    occurred_at: datetime
    request_id: Optional[str] = None
    outcome: str
    metadata_json: Optional[str] = None

class AuditEventListResponse(BaseModel):
    items: List[AuditEventRead]
    total: int
    page: int
    page_size: int

@router.get("", response_model=AuditEventListResponse)
async def list_audit_events(
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_inst_ids = get_user_permitted_institution_ids(current_user)
    roles = [r.code for r in current_user.roles]
    is_national_admin = "NATIONAL_ADMIN" in roles

    query = select(AuditEvent)

    # Scoping: If not national admin, user can only view their own actions or events for their institution
    if not is_national_admin and allowed_inst_ids:
        query = query.where(
            or_(
                AuditEvent.actor_user_id == current_user.id,
                and_(
                    AuditEvent.target_type == "INSTITUTION",
                    AuditEvent.target_id.in_(allowed_inst_ids)
                )
            )
        )

    if action:
        query = query.where(AuditEvent.action == action.upper())
    if target_type:
        query = query.where(AuditEvent.target_type == target_type.upper())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(AuditEvent.occurred_at.desc()).offset(offset).limit(page_size)
    events = (await db.execute(query)).scalars().all()

    return AuditEventListResponse(
        items=[AuditEventRead.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size
    )
