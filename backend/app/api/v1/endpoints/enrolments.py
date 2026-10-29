from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.models.student import EnrolmentRecord, StudentIdentity
from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear
from app.models.user import User
from app.schemas.enrolment import EnrolmentResponse, EnrolmentListResponse
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)

router = APIRouter()

def build_enrolment_response(enr: EnrolmentRecord) -> EnrolmentResponse:
    masked_id = enr.student_identity.masked_apaar_id if enr.student_identity else None
    val_status = enr.student_identity.apaar_validation_status if enr.student_identity else "UNAVAILABLE"

    return EnrolmentResponse(
        id=enr.id,
        institution_id=enr.institution_id,
        institution_name=enr.institution.name if enr.institution else "Unknown",
        programme_id=enr.programme_id,
        programme_name=enr.programme.programme_name if enr.programme else "Unknown",
        official_programme_code=enr.programme.official_programme_code if enr.programme else "N/A",
        academic_year_id=enr.academic_year_id,
        academic_year_label=enr.academic_year.label if enr.academic_year else "Unknown",
        institution_student_id=enr.institution_student_id,
        student_full_name=enr.student_full_name,
        masked_apaar_id=masked_id,
        apaar_validation_status=val_status,
        admission_date=enr.admission_date,
        enrolment_status=enr.enrolment_status,
        admission_category=enr.admission_category,
        supernumerary_category=enr.supernumerary_category,
        source_submission_batch_id=enr.source_submission_batch_id,
        created_at=enr.created_at
    )

@router.get("", response_model=EnrolmentListResponse)
async def list_enrolments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    institution_id: Optional[str] = None,
    programme_id: Optional[str] = None,
    academic_year_id: Optional[str] = None,
    enrolment_status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_ids = get_user_permitted_institution_ids(current_user)

    query = select(EnrolmentRecord).options(
        selectinload(EnrolmentRecord.student_identity),
        selectinload(EnrolmentRecord.institution),
        selectinload(EnrolmentRecord.programme),
        selectinload(EnrolmentRecord.academic_year)
    )

    if allowed_ids is not None:
        query = query.where(EnrolmentRecord.institution_id.in_(allowed_ids))

    if institution_id:
        enforce_institution_scope(current_user, institution_id)
        query = query.where(EnrolmentRecord.institution_id == institution_id)

    if programme_id:
        query = query.where(EnrolmentRecord.programme_id == programme_id)

    if academic_year_id:
        query = query.where(EnrolmentRecord.academic_year_id == academic_year_id)

    if enrolment_status:
        query = query.where(EnrolmentRecord.enrolment_status == enrolment_status.upper())

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                EnrolmentRecord.institution_student_id.ilike(s),
                EnrolmentRecord.student_full_name.ilike(s)
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(EnrolmentRecord.created_at.desc()).offset(offset).limit(page_size)
    records = (await db.execute(query)).scalars().all()

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return EnrolmentListResponse(
        items=[build_enrolment_response(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{record_id}", response_model=EnrolmentResponse)
async def get_enrolment(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(EnrolmentRecord)
        .options(
            selectinload(EnrolmentRecord.student_identity),
            selectinload(EnrolmentRecord.institution),
            selectinload(EnrolmentRecord.programme),
            selectinload(EnrolmentRecord.academic_year)
        )
        .where(EnrolmentRecord.id == record_id)
    )
    enr = res.scalars().first()
    if not enr:
        raise HTTPException(status_code=404, detail="Enrolment record not found")

    enforce_institution_scope(current_user, enr.institution_id)
    return build_enrolment_response(enr)

from app.schemas.integrity import (
    EnrolmentHistoryResponse,
    EnrolmentVersionRead,
    EnrolmentCorrectionRequest,
    EnrolmentCorrectionResponse,
    EvidenceMetadataRead
)
from app.models.integrity import EvidenceMetadata
from app.services.enrolment_correction_service import EnrolmentCorrectionService

@router.get("/{record_id}/history", response_model=EnrolmentHistoryResponse)
async def get_enrolment_history(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(EnrolmentRecord)
        .options(
            selectinload(EnrolmentRecord.versions),
            selectinload(EnrolmentRecord.student_identity)
        )
        .where(EnrolmentRecord.id == record_id)
    )
    enr = res.scalars().first()
    if not enr:
        raise HTTPException(status_code=404, detail="Enrolment record not found")

    enforce_institution_scope(current_user, enr.institution_id)

    versions = [
        EnrolmentVersionRead.model_validate(v)
        for v in enr.versions
    ]
    # Sort versions ascending
    versions.sort(key=lambda x: x.version_number)

    return EnrolmentHistoryResponse(
        current_version=enr.current_record_version,
        enrolment_id=enr.id,
        student_full_name=enr.student_full_name,
        institution_student_id=enr.institution_student_id,
        masked_apaar_id=enr.student_identity.masked_apaar_id if enr.student_identity else None,
        versions=versions
    )

@router.post("/{record_id}/corrections", response_model=EnrolmentCorrectionResponse)
async def correct_enrolment(
    record_id: str,
    body: EnrolmentCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    result = await EnrolmentCorrectionService.apply_correction(
        session=db,
        record_id=record_id,
        expected_version=body.expected_version,
        correction_reason=body.correction_reason,
        updates=body.model_dump(exclude={"expected_version", "correction_reason"}, exclude_unset=True),
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles
    )
    return EnrolmentCorrectionResponse(**result)

@router.get("/{record_id}/evidence", response_model=List[EvidenceMetadataRead])
async def get_enrolment_evidence(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(EnrolmentRecord).where(EnrolmentRecord.id == record_id))
    enr = res.scalars().first()
    if not enr:
        raise HTTPException(status_code=404, detail="Enrolment record not found")

    enforce_institution_scope(current_user, enr.institution_id)

    evidence_res = await db.execute(
        select(EvidenceMetadata).where(EvidenceMetadata.enrolment_record_id == record_id).order_by(EvidenceMetadata.uploaded_at.desc())
    )
    evidence_items = evidence_res.scalars().all()
    return [EvidenceMetadataRead.model_validate(e) for e in evidence_items]

