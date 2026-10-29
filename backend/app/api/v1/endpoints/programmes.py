from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.models.programme import Programme, ProgrammeApproval, ApprovedIntakeVersion, AcademicYear
from app.models.student import EnrolmentRecord
from app.models.institution import Institution
from app.models.user import User
from app.schemas.programme import ProgrammeResponse, ProgrammeApprovalDetailResponse
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)

router = APIRouter()

@router.get("", response_model=List[ProgrammeResponse])
async def list_programmes(
    institution_id: Optional[str] = None,
    academic_discipline: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_ids = get_user_permitted_institution_ids(current_user)
    
    query = select(Programme).options(
        selectinload(Programme.institution),
        selectinload(Programme.approvals).selectinload(ProgrammeApproval.intake_versions)
    )

    if allowed_ids is not None:
        query = query.where(Programme.institution_id.in_(allowed_ids))

    if institution_id:
        enforce_institution_scope(current_user, institution_id)
        query = query.where(Programme.institution_id == institution_id)

    if academic_discipline:
        query = query.where(Programme.academic_discipline == academic_discipline)

    progs = (await db.execute(query.order_by(Programme.programme_name.asc()))).scalars().all()

    # Active academic year
    ay_res = await db.execute(select(AcademicYear).where(AcademicYear.status == "ACTIVE").limit(1))
    active_ay = ay_res.scalars().first()
    active_ay_id = active_ay.id if active_ay else None

    items = []
    for p in progs:
        # Find approved intake for active year
        intake_val = None
        if active_ay_id:
            approval = next((a for a in p.approvals if a.academic_year_id == active_ay_id), None)
            if approval and approval.intake_versions:
                sorted_vers = sorted(approval.intake_versions, key=lambda v: v.version, reverse=True)
                intake_val = sorted_vers[0].approved_intake

        enr_cnt = (await db.execute(
            select(func.count(EnrolmentRecord.id)).where(
                EnrolmentRecord.programme_id == p.id,
                EnrolmentRecord.enrolment_status == "ACTIVE"
            )
        )).scalar() or 0

        items.append(ProgrammeResponse(
            id=p.id,
            institution_id=p.institution_id,
            institution_name=p.institution.name if p.institution else "Unknown",
            official_programme_code=p.official_programme_code,
            programme_name=p.programme_name,
            qualification_level=p.qualification_level,
            academic_discipline=p.academic_discipline,
            status=p.status,
            created_at=p.created_at,
            active_intake=intake_val,
            active_enrolments_count=enr_cnt
        ))

    return items

@router.get("/{programme_id}", response_model=ProgrammeResponse)
async def get_programme(
    programme_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Programme)
        .options(
            selectinload(Programme.institution),
            selectinload(Programme.approvals).selectinload(ProgrammeApproval.intake_versions)
        )
        .where(Programme.id == programme_id)
    )
    p = result.scalars().first()
    if not p:
        raise HTTPException(status_code=404, detail="Programme not found")

    enforce_institution_scope(current_user, p.institution_id)

    ay_res = await db.execute(select(AcademicYear).where(AcademicYear.status == "ACTIVE").limit(1))
    active_ay = ay_res.scalars().first()
    active_ay_id = active_ay.id if active_ay else None

    intake_val = None
    if active_ay_id:
        approval = next((a for a in p.approvals if a.academic_year_id == active_ay_id), None)
        if approval and approval.intake_versions:
            sorted_vers = sorted(approval.intake_versions, key=lambda v: v.version, reverse=True)
            intake_val = sorted_vers[0].approved_intake

    enr_cnt = (await db.execute(
        select(func.count(EnrolmentRecord.id)).where(
            EnrolmentRecord.programme_id == p.id,
            EnrolmentRecord.enrolment_status == "ACTIVE"
        )
    )).scalar() or 0

    return ProgrammeResponse(
        id=p.id,
        institution_id=p.institution_id,
        institution_name=p.institution.name if p.institution else "Unknown",
        official_programme_code=p.official_programme_code,
        programme_name=p.programme_name,
        qualification_level=p.qualification_level,
        academic_discipline=p.academic_discipline,
        status=p.status,
        created_at=p.created_at,
        active_intake=intake_val,
        active_enrolments_count=enr_cnt
    )

@router.get("/{programme_id}/intake", response_model=List[ProgrammeApprovalDetailResponse])
async def get_programme_intake_history(
    programme_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    p = await db.get(Programme, programme_id)
    if not p:
        raise HTTPException(status_code=404, detail="Programme not found")

    enforce_institution_scope(current_user, p.institution_id)

    approvals = (await db.execute(
        select(ProgrammeApproval)
        .options(
            selectinload(ProgrammeApproval.academic_year),
            selectinload(ProgrammeApproval.intake_versions)
        )
        .where(ProgrammeApproval.programme_id == programme_id)
        .order_by(ProgrammeApproval.effective_from.desc())
    )).scalars().all()

    items = []
    for app in approvals:
        intake_num = None
        intake_ver = None
        source_type = "AICTE_APPROVAL_LETTER"
        if app.intake_versions:
            sorted_v = sorted(app.intake_versions, key=lambda x: x.version, reverse=True)
            intake_num = sorted_v[0].approved_intake
            intake_ver = sorted_v[0].version
            source_type = sorted_v[0].source_type

        items.append(ProgrammeApprovalDetailResponse(
            approval_id=app.id,
            approval_reference=app.approval_reference,
            approval_status=app.approval_status,
            academic_year=app.academic_year.label if app.academic_year else "Unknown",
            approved_intake=intake_num,
            intake_version=intake_ver,
            source_reference=app.source_reference,
            source_type=source_type,
            effective_from=app.effective_from,
            effective_until=app.effective_until,
            is_synthetic=app.is_synthetic
        ))

    return items
