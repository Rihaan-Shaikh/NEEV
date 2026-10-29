from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear, ProgrammeApproval, ApprovedIntakeVersion
from app.models.student import EnrolmentRecord
from app.schemas.dashboard import IntakeReconciliationItem
from app.policies.authorization import enforce_institution_scope

async def calculate_intake_reconciliation(
    db: AsyncSession,
    institution_id: Optional[str] = None,
    academic_year_id: Optional[str] = None
) -> List[IntakeReconciliationItem]:
    """
    Performs database-backed intake reconciliation for programmes.
    Calculates active enrolments vs approved intake.
    """
    # 1. Fetch active academic year if not specified
    if not academic_year_id:
        ay_res = await db.execute(select(AcademicYear).where(AcademicYear.status == "ACTIVE").limit(1))
        active_ay = ay_res.scalars().first()
        if not active_ay:
            # Fallback to any academic year
            ay_res = await db.execute(select(AcademicYear).limit(1))
            active_ay = ay_res.scalars().first()
        academic_year_id = active_ay.id if active_ay else None

    ay_label = "2024-2025"
    if academic_year_id:
        ay_obj = await db.get(AcademicYear, academic_year_id)
        if ay_obj:
            ay_label = ay_obj.label

    # 2. Query programmes with approval and intake for this year
    query = select(Programme).options(
        selectinload(Programme.institution),
        selectinload(Programme.approvals).selectinload(ProgrammeApproval.intake_versions)
    )
    if institution_id:
        query = query.where(Programme.institution_id == institution_id)

    programmes = (await db.execute(query)).scalars().all()

    items: List[IntakeReconciliationItem] = []

    for prog in programmes:
        # Find approval for this academic year
        approval = next((a for a in prog.approvals if a.academic_year_id == academic_year_id), None)
        
        approved_intake = None
        is_synthetic = True
        if approval and approval.intake_versions:
            # Get latest version
            sorted_versions = sorted(approval.intake_versions, key=lambda v: v.version, reverse=True)
            approved_intake = sorted_versions[0].approved_intake
            is_synthetic = approval.is_synthetic

        # Query active enrolments count from DB
        count_query = select(func.count(EnrolmentRecord.id)).where(
            EnrolmentRecord.programme_id == prog.id,
            EnrolmentRecord.academic_year_id == academic_year_id,
            EnrolmentRecord.enrolment_status == "ACTIVE"
        )
        active_count = (await db.execute(count_query)).scalar() or 0

        # Evaluate reconciliation status & rules
        if approved_intake is None:
            # INT-001: Missing intake reference
            status = "MISSING_REFERENCE"
            variance = None
            rule_basis = "INT-001: Approved-intake reference missing for this academic year; reconciliation incomplete."
            is_exceeded = False
        elif active_count > approved_intake:
            # INT-002: Active count exceeds permitted capacity
            status = "CAPACITY_EXCEEDED"
            variance = active_count - approved_intake
            rule_basis = f"INT-002: Active count ({active_count}) exceeds configured approved intake ({approved_intake}) by {variance} seats."
            is_exceeded = True
        elif active_count == approved_intake:
            status = "BALANCED"
            variance = 0
            rule_basis = f"Active enrolment matches approved capacity ({approved_intake}/{approved_intake})."
            is_exceeded = False
        else:
            status = "UNDER_CAPACITY"
            variance = active_count - approved_intake  # negative
            rule_basis = f"Active enrolment ({active_count}) is within approved capacity ({approved_intake}). Remaining seats: {approved_intake - active_count}."
            is_exceeded = False

        items.append(IntakeReconciliationItem(
            programme_id=prog.id,
            programme_name=prog.programme_name,
            official_programme_code=prog.official_programme_code,
            academic_year_label=ay_label,
            approved_intake=approved_intake,
            calculated_active_enrolments=active_count,
            variance=variance,
            reconciliation_status=status,
            rule_basis=rule_basis,
            is_capacity_exceeded=is_exceeded,
            is_synthetic=is_synthetic
        ))

    return items
