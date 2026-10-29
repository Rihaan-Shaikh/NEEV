from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Dict, Any

from app.db.session import get_db
from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear
from app.models.student import EnrolmentRecord
from app.models.submission import SubmissionBatch
from app.models.validation import ValidationFinding
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.submission import BatchResponse
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids
)
from app.services.reconciliation_service import calculate_intake_reconciliation

router = APIRouter()

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_ids = get_user_permitted_institution_ids(current_user)

    # 1. Institutions count
    inst_query = select(func.count(Institution.id))
    if allowed_ids is not None:
        inst_query = inst_query.where(Institution.id.in_(allowed_ids))
    inst_count = (await db.execute(inst_query)).scalar() or 0

    # 2. Programmes count
    prog_query = select(func.count(Programme.id))
    if allowed_ids is not None:
        prog_query = prog_query.where(Programme.institution_id.in_(allowed_ids))
    prog_count = (await db.execute(prog_query)).scalar() or 0

    # 3. Selected academic year
    ay_res = await db.execute(select(AcademicYear).where(AcademicYear.status == "ACTIVE").limit(1))
    active_ay = ay_res.scalars().first()
    ay_label = active_ay.label if active_ay else "2024-2025"
    ay_id = active_ay.id if active_ay else None

    # 4. Total and active student enrolments in scope
    enr_total_query = select(func.count(EnrolmentRecord.id))
    if allowed_ids is not None:
        enr_total_query = enr_total_query.where(EnrolmentRecord.institution_id.in_(allowed_ids))
    total_students = (await db.execute(enr_total_query)).scalar() or 0

    enr_active_query = select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.enrolment_status == "ACTIVE")
    if allowed_ids is not None:
        enr_active_query = enr_active_query.where(EnrolmentRecord.institution_id.in_(allowed_ids))
    active_students = (await db.execute(enr_active_query)).scalar() or 0

    # 5. Batches by status
    batch_base_query = select(SubmissionBatch.processing_status, func.count(SubmissionBatch.id))
    if allowed_ids is not None:
        batch_base_query = batch_base_query.where(SubmissionBatch.institution_id.in_(allowed_ids))
    batch_status_counts = (await db.execute(batch_base_query.group_by(SubmissionBatch.processing_status))).all()
    batches_dict = {status: count for status, count in batch_status_counts}

    # 6. Recent submission batches (last 5)
    rec_query = select(SubmissionBatch).options(
        selectinload(SubmissionBatch.institution),
        selectinload(SubmissionBatch.academic_year),
        selectinload(SubmissionBatch.programme)
    )
    if allowed_ids is not None:
        rec_query = rec_query.where(SubmissionBatch.institution_id.in_(allowed_ids))
    recent_batches = (await db.execute(rec_query.order_by(SubmissionBatch.created_at.desc()).limit(5))).scalars().all()

    recent_batch_responses = [
        BatchResponse(
            id=b.id,
            institution_id=b.institution_id,
            institution_name=b.institution.name if b.institution else "Unknown",
            academic_year_id=b.academic_year_id,
            academic_year_label=b.academic_year.label if b.academic_year else "Unknown",
            programme_id=b.programme_id,
            programme_name=b.programme.programme_name if b.programme else None,
            submission_type=b.submission_type,
            source_type=b.source_type,
            processing_status=b.processing_status,
            source_filename=b.source_filename,
            row_count=b.row_count,
            valid_count=b.valid_count,
            accepted_count=b.accepted_count,
            rejected_count=b.rejected_count,
            flagged_count=b.flagged_count,
            ruleset_version=b.ruleset_version,
            receipt_reference=b.receipt_reference,
            created_at=b.created_at
        )
        for b in recent_batches
    ]

    # 7. Validation issues count
    val_query = select(func.count(ValidationFinding.id)).where(ValidationFinding.status == "OPEN")
    val_issues = (await db.execute(val_query)).scalar() or 0

    # 8. Intake reconciliation items
    first_inst_id = allowed_ids[0] if (allowed_ids and len(allowed_ids) == 1) else None
    reconciliation_items = await calculate_intake_reconciliation(
        db=db,
        institution_id=first_inst_id,
        academic_year_id=ay_id
    )

    exceeded_count = sum(1 for item in reconciliation_items if item.is_capacity_exceeded)

    return DashboardSummaryResponse(
        institutions_count=inst_count,
        programmes_count=prog_count,
        selected_academic_year=ay_label,
        batches_by_status=batches_dict,
        total_students_count=total_students,
        active_students_count=active_students,
        recent_submissions=recent_batch_responses,
        validation_issues_count=val_issues,
        programmes_exceeding_capacity=exceeded_count,
        reconciliation_items=reconciliation_items
    )
