from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.models.institution import Institution
from app.models.programme import Programme
from app.models.student import EnrolmentRecord
from app.models.user import User
from app.schemas.institution import (
    InstitutionResponse,
    InstitutionListResponse,
    InstitutionCreate,
    InstitutionUpdate
)
from app.schemas.programme import ProgrammeResponse
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope,
    check_permission
)
from app.services.audit_service import log_audit_event

router = APIRouter()

@router.get("", response_model=InstitutionListResponse)
async def list_institutions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    state_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_ids = get_user_permitted_institution_ids(current_user)
    
    query = select(Institution)
    if allowed_ids is not None:
        query = query.where(Institution.id.in_(allowed_ids))

    if search:
        s = f"%{search.strip()}%"
        query = query.where(or_(Institution.name.ilike(s), Institution.official_institution_code.ilike(s)))
    if status:
        query = query.where(Institution.status == status.upper())
    if state_code:
        query = query.where(Institution.state_code == state_code.upper())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Institution.name.asc()).offset(offset).limit(page_size)
    results = (await db.execute(query)).scalars().all()

    items = []
    for inst in results:
        # Get counts
        prog_cnt = (await db.execute(
            select(func.count(Programme.id)).where(Programme.institution_id == inst.id)
        )).scalar() or 0
        enr_cnt = (await db.execute(
            select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.institution_id == inst.id)
        )).scalar() or 0

        items.append(InstitutionResponse(
            id=inst.id,
            official_institution_code=inst.official_institution_code,
            name=inst.name,
            institution_type=inst.institution_type,
            state_code=inst.state_code,
            district_code=inst.district_code,
            address=inst.address,
            status=inst.status,
            source_reference=inst.source_reference,
            is_synthetic=inst.is_synthetic,
            created_at=inst.created_at,
            updated_at=inst.updated_at,
            programmes_count=prog_cnt,
            enrolments_count=enr_cnt
        ))

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return InstitutionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(
    institution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    enforce_institution_scope(current_user, institution_id)
    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    prog_cnt = (await db.execute(
        select(func.count(Programme.id)).where(Programme.institution_id == inst.id)
    )).scalar() or 0
    enr_cnt = (await db.execute(
        select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.institution_id == inst.id)
    )).scalar() or 0

    return InstitutionResponse(
        id=inst.id,
        official_institution_code=inst.official_institution_code,
        name=inst.name,
        institution_type=inst.institution_type,
        state_code=inst.state_code,
        district_code=inst.district_code,
        address=inst.address,
        status=inst.status,
        source_reference=inst.source_reference,
        is_synthetic=inst.is_synthetic,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
        programmes_count=prog_cnt,
        enrolments_count=enr_cnt
    )

@router.post("", response_model=InstitutionResponse, dependencies=[Depends(check_permission("institution.manage"))])
async def create_institution(
    req: InstitutionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Check duplicate code
    existing = await db.execute(
        select(Institution).where(Institution.official_institution_code == req.official_institution_code)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Institution code already registered")

    inst = Institution(
        official_institution_code=req.official_institution_code,
        name=req.name,
        institution_type=req.institution_type,
        state_code=req.state_code,
        district_code=req.district_code,
        address=req.address,
        status=req.status,
        is_synthetic=req.is_synthetic,
        source_reference="ADMINISTRATIVE_ENTRY"
    )
    db.add(inst)
    await db.flush()

    await log_audit_event(
        db,
        action="INSTITUTION_CREATED",
        target_type="INSTITUTION",
        target_id=inst.id,
        actor_user_id=current_user.id,
        actor_email=current_user.email_normalized,
        metadata={"code": inst.official_institution_code, "name": inst.name}
    )

    return InstitutionResponse(
        id=inst.id,
        official_institution_code=inst.official_institution_code,
        name=inst.name,
        institution_type=inst.institution_type,
        state_code=inst.state_code,
        district_code=inst.district_code,
        address=inst.address,
        status=inst.status,
        source_reference=inst.source_reference,
        is_synthetic=inst.is_synthetic,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
        programmes_count=0,
        enrolments_count=0
    )

@router.patch("/{institution_id}", response_model=InstitutionResponse, dependencies=[Depends(check_permission("institution.manage"))])
async def update_institution(
    institution_id: str,
    req: InstitutionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    enforce_institution_scope(current_user, institution_id)
    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    if req.name is not None:
        inst.name = req.name
    if req.institution_type is not None:
        inst.institution_type = req.institution_type
    if req.state_code is not None:
        inst.state_code = req.state_code
    if req.district_code is not None:
        inst.district_code = req.district_code
    if req.address is not None:
        inst.address = req.address
    if req.status is not None:
        inst.status = req.status

    await db.flush()

    await log_audit_event(
        db,
        action="INSTITUTION_UPDATED",
        target_type="INSTITUTION",
        target_id=inst.id,
        actor_user_id=current_user.id,
        actor_email=current_user.email_normalized
    )

    prog_cnt = (await db.execute(
        select(func.count(Programme.id)).where(Programme.institution_id == inst.id)
    )).scalar() or 0
    enr_cnt = (await db.execute(
        select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.institution_id == inst.id)
    )).scalar() or 0

    return InstitutionResponse(
        id=inst.id,
        official_institution_code=inst.official_institution_code,
        name=inst.name,
        institution_type=inst.institution_type,
        state_code=inst.state_code,
        district_code=inst.district_code,
        address=inst.address,
        status=inst.status,
        source_reference=inst.source_reference,
        is_synthetic=inst.is_synthetic,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
        programmes_count=prog_cnt,
        enrolments_count=enr_cnt
    )

@router.get("/{institution_id}/programmes", response_model=List[ProgrammeResponse])
async def list_institution_programmes(
    institution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    enforce_institution_scope(current_user, institution_id)
    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    progs = (await db.execute(
        select(Programme).where(Programme.institution_id == institution_id).order_by(Programme.programme_name.asc())
    )).scalars().all()

    items = []
    for p in progs:
        enr_cnt = (await db.execute(
            select(func.count(EnrolmentRecord.id)).where(
                EnrolmentRecord.programme_id == p.id,
                EnrolmentRecord.enrolment_status == "ACTIVE"
            )
        )).scalar() or 0

        items.append(ProgrammeResponse(
            id=p.id,
            institution_id=p.institution_id,
            institution_name=inst.name,
            official_programme_code=p.official_programme_code,
            programme_name=p.programme_name,
            qualification_level=p.qualification_level,
            academic_discipline=p.academic_discipline,
            status=p.status,
            created_at=p.created_at,
            active_enrolments_count=enr_cnt
        ))

    return items
