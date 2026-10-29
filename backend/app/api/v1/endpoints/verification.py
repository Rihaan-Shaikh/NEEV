from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List
import json

from app.db.session import get_db
from app.models.user import User
from app.models.verification import VerificationReference, VerificationAccessLog
from app.models.student import EnrolmentRecord
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)
from app.schemas.verification import (
    VerificationReferenceCreateRequest,
    VerificationReferenceRevokeRequest,
    VerificationResolveRequest,
    VerificationReferenceItem,
    VerificationReferenceCreatedResponse,
    VerificationReferenceListResponse,
    VerificationResultResponse
)
from app.services.verification_service import VerificationService

router = APIRouter()

@router.post("/verification-references", response_model=VerificationReferenceCreatedResponse, status_code=status.HTTP_201_CREATED)
async def issue_verification_reference(
    payload: VerificationReferenceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Issues a limited-purpose verification reference for an eligible student enrolment record.
    The raw bearer token is returned strictly once in this response and hashed at rest in PostgreSQL.
    """
    vrf, raw_token, enrolment = await VerificationService.issue_reference(
        session=db,
        current_user=current_user,
        enrolment_record_id=payload.enrolment_record_id,
        purpose=payload.purpose,
        disclosure_profile=payload.disclosure_profile,
        expires_in_days=payload.expires_in_days,
        max_uses=payload.max_uses
    )
    return VerificationReferenceCreatedResponse(
        id=vrf.id,
        public_reference_code=vrf.public_reference_code,
        enrolment_record_id=vrf.enrolment_record_id,
        student_full_name=enrolment.student_full_name if enrolment else "Unknown",
        institution_id=vrf.institution_id,
        institution_name=vrf.institution.name if vrf.institution else "Delhi Institute of Technology",
        programme_name=enrolment.programme.programme_name if enrolment and enrolment.programme else None,
        academic_year_label=enrolment.academic_year.label if enrolment and enrolment.academic_year else None,
        purpose=vrf.purpose,
        disclosure_profile=json.loads(vrf.disclosure_profile),
        status=vrf.status,
        max_uses=vrf.max_uses,
        use_count=vrf.use_count,
        expires_at=vrf.expires_at,
        revoked_at=vrf.revoked_at,
        revocation_reason=vrf.revocation_reason,
        created_at=vrf.created_at,
        access_logs_count=0,
        raw_bearer_token=raw_token
    )

@router.get("/verification-references", response_model=VerificationReferenceListResponse)
async def list_verification_references(
    institution_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists verification references issued within the user's permitted institutional scope.
    """
    allowed_ids = get_user_permitted_institution_ids(current_user)
    q = select(VerificationReference).options(
        selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.programme),
        selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.academic_year),
        selectinload(VerificationReference.institution),
        selectinload(VerificationReference.access_logs)
    )

    if allowed_ids is not None:
        q = q.where(VerificationReference.institution_id.in_(allowed_ids))
    elif institution_id:
        q = q.where(VerificationReference.institution_id == institution_id)

    if status_filter:
        q = q.where(VerificationReference.status == status_filter.upper())

    if search:
        s = f"%{search.strip()}%"
        q = q.where(
            (VerificationReference.public_reference_code.ilike(s)) |
            (VerificationReference.purpose.ilike(s))
        )

    # Count
    count_q = select(func.count(VerificationReference.id))
    if allowed_ids is not None:
        count_q = count_q.where(VerificationReference.institution_id.in_(allowed_ids))
    elif institution_id:
        count_q = count_q.where(VerificationReference.institution_id == institution_id)
    if status_filter:
        count_q = count_q.where(VerificationReference.status == status_filter.upper())

    total = (await db.execute(count_q)).scalar() or 0

    rows = (
        await db.execute(
            q.order_by(desc(VerificationReference.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    items = []
    for vrf in rows:
        enrolment = vrf.enrolment_record
        items.append(VerificationReferenceItem(
            id=vrf.id,
            public_reference_code=vrf.public_reference_code,
            enrolment_record_id=vrf.enrolment_record_id,
            student_full_name=enrolment.student_full_name if enrolment else "Unknown",
            institution_id=vrf.institution_id,
            institution_name=vrf.institution.name if vrf.institution else "Delhi Institute of Technology",
            programme_name=enrolment.programme.programme_name if enrolment and enrolment.programme else None,
            academic_year_label=enrolment.academic_year.label if enrolment and enrolment.academic_year else None,
            purpose=vrf.purpose,
            disclosure_profile=json.loads(vrf.disclosure_profile),
            status=vrf.status,
            max_uses=vrf.max_uses,
            use_count=vrf.use_count,
            expires_at=vrf.expires_at,
            revoked_at=vrf.revoked_at,
            revocation_reason=vrf.revocation_reason,
            created_at=vrf.created_at,
            access_logs_count=len(vrf.access_logs) if vrf.access_logs else 0
        ))

    return VerificationReferenceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/verification-references/{reference_id}", response_model=VerificationReferenceItem)
async def get_verification_reference(
    reference_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves details and status of a specific verification reference.
    """
    q = select(VerificationReference).options(
        selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.programme),
        selectinload(VerificationReference.enrolment_record).selectinload(EnrolmentRecord.academic_year),
        selectinload(VerificationReference.institution),
        selectinload(VerificationReference.access_logs)
    ).where(VerificationReference.id == reference_id)

    vrf = (await db.execute(q)).scalar_one_or_none()
    if not vrf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification reference '{reference_id}' not found."
        )

    enforce_institution_scope(current_user, vrf.institution_id)
    enrolment = vrf.enrolment_record

    return VerificationReferenceItem(
        id=vrf.id,
        public_reference_code=vrf.public_reference_code,
        enrolment_record_id=vrf.enrolment_record_id,
        student_full_name=enrolment.student_full_name if enrolment else "Unknown",
        institution_id=vrf.institution_id,
        institution_name=vrf.institution.name if vrf.institution else "Delhi Institute of Technology",
        programme_name=enrolment.programme.programme_name if enrolment and enrolment.programme else None,
        academic_year_label=enrolment.academic_year.label if enrolment and enrolment.academic_year else None,
        purpose=vrf.purpose,
        disclosure_profile=json.loads(vrf.disclosure_profile),
        status=vrf.status,
        max_uses=vrf.max_uses,
        use_count=vrf.use_count,
        expires_at=vrf.expires_at,
        revoked_at=vrf.revoked_at,
        revocation_reason=vrf.revocation_reason,
        created_at=vrf.created_at,
        access_logs_count=len(vrf.access_logs) if vrf.access_logs else 0
    )

@router.post("/verification-references/{reference_id}/revoke", response_model=VerificationReferenceItem)
async def revoke_verification_reference(
    reference_id: str,
    payload: VerificationReferenceRevokeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revokes an active verification reference with an immutable audit event.
    """
    vrf = await VerificationService.revoke_reference(
        session=db,
        current_user=current_user,
        reference_id=reference_id,
        revocation_reason=payload.revocation_reason
    )
    enrolment = vrf.enrolment_record
    return VerificationReferenceItem(
        id=vrf.id,
        public_reference_code=vrf.public_reference_code,
        enrolment_record_id=vrf.enrolment_record_id,
        student_full_name=enrolment.student_full_name if enrolment else "Unknown",
        institution_id=vrf.institution_id,
        institution_name=vrf.institution.name if vrf.institution else "Delhi Institute of Technology",
        programme_name=enrolment.programme.programme_name if enrolment and enrolment.programme else None,
        academic_year_label=enrolment.academic_year.label if enrolment and enrolment.academic_year else None,
        purpose=vrf.purpose,
        disclosure_profile=json.loads(vrf.disclosure_profile),
        status=vrf.status,
        max_uses=vrf.max_uses,
        use_count=vrf.use_count,
        expires_at=vrf.expires_at,
        revoked_at=vrf.revoked_at,
        revocation_reason=vrf.revocation_reason,
        created_at=vrf.created_at,
        access_logs_count=0
    )

@router.post("/verify", response_model=VerificationResultResponse)
async def verify_reference_token(
    payload: VerificationResolveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Public / authorized verification resolver endpoint.
    Validates token hash, checks expiry/revocation/use limits under transaction,
    and returns minimal permitted disclosed claims with synthetic disclaimer.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    res = await VerificationService.verify_reference_token(
        session=db,
        raw_token=payload.reference_token,
        client_ip=client_ip,
        user_agent=user_agent
    )
    return VerificationResultResponse(**res)
