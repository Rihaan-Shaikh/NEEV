from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.schemas.integrity import ConflictCandidate, ReconciliationResult
from app.policies.authorization import get_current_user
from app.services.conflict_service import ConflictDetectionService

router = APIRouter()

@router.get("/conflicts", response_model=List[ConflictCandidate])
async def get_conflict_candidates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    is_national_admin = "NATIONAL_ADMIN" in roles
    inst_id = current_user.scopes[0].institution_id if (not is_national_admin and current_user.scopes) else None

    # Run quick evaluation to get candidates
    reconciliation = await ConflictDetectionService.run_integrity_reconciliation(
        session=db,
        current_user_id=current_user.id,
        institution_id=inst_id
    )

    # Fetch newly generated or existing open duplicate/conflict findings
    from app.models.integrity import Finding
    from sqlalchemy import select, and_, or_
    from sqlalchemy.orm import selectinload

    query = select(Finding).where(
        and_(
            Finding.category == "DUPLICATE",
            Finding.status.in_(("OPEN", "AWAITING_INSTITUTION_RESPONSE", "RESPONSE_RECEIVED", "UNDER_REVIEW"))
        )
    )
    if inst_id:
        query = query.where(
            or_(
                Finding.primary_institution_id == inst_id,
                Finding.secondary_institution_id == inst_id
            )
        )
    res = await db.execute(query)
    findings = res.scalars().all()

    candidates = [
        ConflictCandidate(
            rule_code=f.rule_code,
            conflict_type=f.category,
            severity=f.severity,
            explanation=f.explanation,
            primary_enrolment_id=f.primary_enrolment_id or "N/A",
            secondary_enrolment_id=f.secondary_enrolment_id or "N/A",
            primary_institution_id=f.primary_institution_id,
            secondary_institution_id=f.secondary_institution_id or "N/A",
            apaar_fingerprint_masked="APAAR-***-####",
            suggested_action="Review institutional response and verify enrolment transfer documentation."
        )
        for f in findings
    ]
    return candidates

@router.post("/reconcile", response_model=ReconciliationResult)
async def trigger_reconciliation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    is_national_admin = "NATIONAL_ADMIN" in roles
    inst_id = current_user.scopes[0].institution_id if (not is_national_admin and current_user.scopes) else None

    result = await ConflictDetectionService.run_integrity_reconciliation(
        session=db,
        current_user_id=current_user.id,
        institution_id=inst_id
    )
    return ReconciliationResult(**result)
