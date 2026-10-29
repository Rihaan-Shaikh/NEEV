from fastapi import APIRouter, Depends, HTTPException, Query, Form, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.models.integrity import Finding, FindingResponse, EvidenceMetadata
from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear
from app.models.student import EnrolmentRecord
from app.models.user import User
from app.schemas.integrity import (
    FindingRead,
    FindingDetailRead,
    FindingListResponse,
    FindingResponseCreate,
    FindingResponseRead,
    FindingTransitionRequest,
    EvidenceMetadataRead
)
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)
from app.services.finding_service import FindingService
from app.services.evidence_service import EvidenceService

router = APIRouter()

def build_finding_read(f: Finding) -> FindingRead:
    return FindingRead(
        id=f.id,
        rule_code=f.rule_code,
        rule_version=f.rule_version,
        category=f.category,
        severity=f.severity,
        status=f.status,
        explanation=f.explanation,
        structured_evidence_json=f.structured_evidence_json,
        primary_institution_id=f.primary_institution_id,
        primary_institution_name=f.primary_institution.name if f.primary_institution else "Unknown",
        secondary_institution_id=f.secondary_institution_id,
        secondary_institution_name=f.secondary_institution.name if f.secondary_institution else None,
        programme_id=f.programme_id,
        programme_name=f.programme.programme_name if f.programme else None,
        academic_year_id=f.academic_year_id,
        academic_year_label=f.academic_year.label if f.academic_year else None,
        primary_enrolment_id=f.primary_enrolment_id,
        primary_student_name=f.primary_enrolment.student_full_name if f.primary_enrolment else None,
        primary_institution_student_id=f.primary_enrolment.institution_student_id if f.primary_enrolment else None,
        primary_masked_apaar=f.primary_enrolment.student_identity.masked_apaar_id if (f.primary_enrolment and f.primary_enrolment.student_identity) else None,
        secondary_enrolment_id=f.secondary_enrolment_id,
        secondary_student_name=f.secondary_enrolment.student_full_name if f.secondary_enrolment else None,
        secondary_institution_student_id=f.secondary_enrolment.institution_student_id if f.secondary_enrolment else None,
        secondary_masked_apaar=f.secondary_enrolment.student_identity.masked_apaar_id if (f.secondary_enrolment and f.secondary_enrolment.student_identity) else None,
        assigned_reviewer_id=f.assigned_reviewer_id,
        assigned_reviewer_name=f.assigned_reviewer.display_name if f.assigned_reviewer else None,
        resolution_rationale=f.resolution_rationale,
        resolved_by_user_id=f.resolved_by_user_id,
        resolved_at=f.resolved_at,
        first_detected_at=f.first_detected_at,
        last_detected_at=f.last_detected_at,
        created_at=f.created_at,
        updated_at=f.updated_at,
        responses_count=len(f.responses) if f.responses else 0,
        evidence_count=len(f.evidence_attachments) if f.evidence_attachments else 0
    )

@router.get("", response_model=FindingListResponse)
async def list_findings(
    status: Optional[str] = None,
    institution_id: Optional[str] = None,
    programme_id: Optional[str] = None,
    academic_year_id: Optional[str] = None,
    rule_code: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_ids = get_user_permitted_institution_ids(current_user)

    query = select(Finding).options(
        selectinload(Finding.primary_institution),
        selectinload(Finding.secondary_institution),
        selectinload(Finding.programme),
        selectinload(Finding.academic_year),
        selectinload(Finding.primary_enrolment).selectinload(EnrolmentRecord.student_identity),
        selectinload(Finding.secondary_enrolment).selectinload(EnrolmentRecord.student_identity),
        selectinload(Finding.assigned_reviewer),
        selectinload(Finding.responses),
        selectinload(Finding.evidence_attachments)
    )

    # Scoping: if user has restricted institution scope, only show findings where their institution is primary or secondary
    if allowed_ids is not None:
        query = query.where(
            or_(
                Finding.primary_institution_id.in_(allowed_ids),
                Finding.secondary_institution_id.in_(allowed_ids)
            )
        )

    if institution_id:
        enforce_institution_scope(current_user, institution_id)
        query = query.where(
            or_(
                Finding.primary_institution_id == institution_id,
                Finding.secondary_institution_id == institution_id
            )
        )

    if status:
        query = query.where(Finding.status == status.upper())
    if programme_id:
        query = query.where(Finding.programme_id == programme_id)
    if academic_year_id:
        query = query.where(Finding.academic_year_id == academic_year_id)
    if rule_code:
        query = query.where(Finding.rule_code == rule_code.upper())
    if category:
        query = query.where(Finding.category == category.upper())
    if severity:
        query = query.where(Finding.severity == severity.upper())

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Finding.last_detected_at.desc()).offset(offset).limit(page_size)
    records = (await db.execute(query)).scalars().all()

    items = [build_finding_read(f) for f in records]
    return FindingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{finding_id}", response_model=FindingDetailRead)
async def get_finding_detail(
    finding_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Finding)
        .where(Finding.id == finding_id)
        .options(
            selectinload(Finding.primary_institution),
            selectinload(Finding.secondary_institution),
            selectinload(Finding.programme),
            selectinload(Finding.academic_year),
            selectinload(Finding.primary_enrolment).selectinload(EnrolmentRecord.student_identity),
            selectinload(Finding.secondary_enrolment).selectinload(EnrolmentRecord.student_identity),
            selectinload(Finding.assigned_reviewer),
            selectinload(Finding.responses).selectinload(FindingResponse.submitting_user),
            selectinload(Finding.responses).selectinload(FindingResponse.institution),
            selectinload(Finding.evidence_attachments).selectinload(EvidenceMetadata.uploader),
            selectinload(Finding.evidence_attachments).selectinload(EvidenceMetadata.institution)
        )
    )
    res = await db.execute(query)
    finding = res.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    allowed_ids = get_user_permitted_institution_ids(current_user)
    if allowed_ids is not None:
        if (finding.primary_institution_id not in allowed_ids and 
            finding.secondary_institution_id not in allowed_ids):
            raise HTTPException(status_code=403, detail="Access denied: You do not have permission to view this finding.")

    is_national_admin = any(r.code in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in current_user.roles)
    permitted = FindingService.get_permitted_transitions_for_user(finding.status, is_national_admin)

    base = build_finding_read(finding)

    responses_read = [
        FindingResponseRead(
            id=r.id,
            finding_id=r.finding_id,
            submitting_user_id=r.submitting_user_id,
            submitting_user_name=r.submitting_user.display_name if r.submitting_user else None,
            institution_id=r.institution_id,
            institution_name=r.institution.name if r.institution else None,
            response_type=r.response_type,
            explanation=r.explanation,
            related_correction_id=r.related_correction_id,
            review_status=r.review_status,
            reviewer_notes=r.reviewer_notes,
            submitted_at=r.submitted_at
        )
        for r in (finding.responses or [])
    ]

    evidence_read = [
        EvidenceMetadataRead(
            id=e.id,
            finding_id=e.finding_id,
            enrolment_record_id=e.enrolment_record_id,
            original_filename=e.original_filename,
            media_type=e.media_type,
            file_size_bytes=e.file_size_bytes,
            sha256_checksum=e.sha256_checksum,
            uploader_user_id=e.uploader_user_id,
            uploader_name=e.uploader.display_name if e.uploader else None,
            institution_id=e.institution_id,
            institution_name=e.institution.name if e.institution else None,
            evidence_category=e.evidence_category,
            source_provenance=e.source_provenance,
            scanning_status=e.scanning_status,
            uploaded_at=e.uploaded_at
        )
        for e in (finding.evidence_attachments or [])
    ]

    return FindingDetailRead(
        **base.model_dump(),
        responses=responses_read,
        evidence_attachments=evidence_read,
        permitted_transitions=permitted
    )

@router.post("/{finding_id}/responses", response_model=FindingResponseRead)
async def submit_finding_response(
    finding_id: str,
    body: FindingResponseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    resp = await FindingService.submit_response(
        session=db,
        finding_id=finding_id,
        response_type=body.response_type,
        explanation=body.explanation,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        related_correction_id=body.related_correction_id
    )

    # Reload response with submitting_user and institution
    res = await db.execute(
        select(FindingResponse)
        .where(FindingResponse.id == resp.id)
        .options(
            selectinload(FindingResponse.submitting_user),
            selectinload(FindingResponse.institution)
        )
    )
    loaded_resp = res.scalar_one()

    return FindingResponseRead(
        id=loaded_resp.id,
        finding_id=loaded_resp.finding_id,
        submitting_user_id=loaded_resp.submitting_user_id,
        submitting_user_name=loaded_resp.submitting_user.display_name if loaded_resp.submitting_user else None,
        institution_id=loaded_resp.institution_id,
        institution_name=loaded_resp.institution.name if loaded_resp.institution else None,
        response_type=loaded_resp.response_type,
        explanation=loaded_resp.explanation,
        related_correction_id=loaded_resp.related_correction_id,
        review_status=loaded_resp.review_status,
        reviewer_notes=loaded_resp.reviewer_notes,
        submitted_at=loaded_resp.submitted_at
    )

@router.get("/{finding_id}/responses", response_model=List[FindingResponseRead])
async def list_finding_responses(
    finding_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(FindingResponse)
        .where(FindingResponse.finding_id == finding_id)
        .options(
            selectinload(FindingResponse.submitting_user),
            selectinload(FindingResponse.institution)
        )
        .order_by(FindingResponse.submitted_at.desc())
    )
    res = await db.execute(query)
    items = res.scalars().all()

    return [
        FindingResponseRead(
            id=r.id,
            finding_id=r.finding_id,
            submitting_user_id=r.submitting_user_id,
            submitting_user_name=r.submitting_user.display_name if r.submitting_user else None,
            institution_id=r.institution_id,
            institution_name=r.institution.name if r.institution else None,
            response_type=r.response_type,
            explanation=r.explanation,
            related_correction_id=r.related_correction_id,
            review_status=r.review_status,
            reviewer_notes=r.reviewer_notes,
            submitted_at=r.submitted_at
        )
        for r in items
    ]

@router.post("/{finding_id}/transition", response_model=FindingRead)
async def transition_finding(
    finding_id: str,
    body: FindingTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    updated_finding = await FindingService.transition_finding_status(
        session=db,
        finding_id=finding_id,
        target_status=body.target_status,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        rationale=body.rationale
    )

    # Reload finding
    res = await db.execute(
        select(Finding)
        .where(Finding.id == updated_finding.id)
        .options(
            selectinload(Finding.primary_institution),
            selectinload(Finding.secondary_institution),
            selectinload(Finding.programme),
            selectinload(Finding.academic_year),
            selectinload(Finding.primary_enrolment).selectinload(EnrolmentRecord.student_identity),
            selectinload(Finding.secondary_enrolment).selectinload(EnrolmentRecord.student_identity),
            selectinload(Finding.assigned_reviewer),
            selectinload(Finding.responses),
            selectinload(Finding.evidence_attachments)
        )
    )
    loaded = res.scalar_one()
    return build_finding_read(loaded)

@router.post("/{finding_id}/evidence", response_model=EvidenceMetadataRead)
async def upload_finding_evidence(
    finding_id: str,
    file: UploadFile = File(...),
    evidence_category: str = Form("OTHER"),
    source_provenance: str = Form("INSTITUTION_SUBMISSION"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    evidence = await EvidenceService.upload_evidence(
        session=db,
        file=file,
        evidence_category=evidence_category,
        source_provenance=source_provenance,
        finding_id=finding_id,
        enrolment_record_id=None,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles
    )

    # Load uploader & institution
    res = await db.execute(
        select(EvidenceMetadata)
        .where(EvidenceMetadata.id == evidence.id)
        .options(
            selectinload(EvidenceMetadata.uploader),
            selectinload(EvidenceMetadata.institution)
        )
    )
    loaded = res.scalar_one()

    return EvidenceMetadataRead(
        id=loaded.id,
        finding_id=loaded.finding_id,
        enrolment_record_id=loaded.enrolment_record_id,
        original_filename=loaded.original_filename,
        media_type=loaded.media_type,
        file_size_bytes=loaded.file_size_bytes,
        sha256_checksum=loaded.sha256_checksum,
        uploader_user_id=loaded.uploader_user_id,
        uploader_name=loaded.uploader.display_name if loaded.uploader else None,
        institution_id=loaded.institution_id,
        institution_name=loaded.institution.name if loaded.institution else None,
        evidence_category=loaded.evidence_category,
        source_provenance=loaded.source_provenance,
        scanning_status=loaded.scanning_status,
        uploaded_at=loaded.uploaded_at
    )
