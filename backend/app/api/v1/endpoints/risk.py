from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import json

from app.db.session import get_db
from app.models.user import User
from app.models.oversight import RiskCalculation
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)
from app.schemas.oversight import (
    RiskCalculationResponse,
    RiskFactorBreakdown,
    RiskQueueResponse,
    RiskQueueItem,
    InstitutionRiskProfileResponse
)
from app.services.risk_engine_service import RiskEngineService

router = APIRouter()

def _format_calc_response(calc: RiskCalculation) -> RiskCalculationResponse:
    snapshot = json.loads(calc.input_snapshot_json) if calc.input_snapshot_json else {}
    factors = RiskFactorBreakdown(
        capacity_discrepancy=calc.factor_capacity_discrepancy,
        unresolved_conflicts=calc.factor_unresolved_conflicts,
        data_quality=calc.factor_data_quality,
        unusual_roster_changes=calc.factor_unusual_roster_changes,
        source_reconciliation_gap=calc.factor_source_reconciliation_gap,
        repeated_prior_findings=calc.factor_repeated_prior_findings,
        total_score=calc.total_score,
        risk_band=calc.risk_band,
        completeness_state=calc.completeness_state,
        explanation=calc.explanation
    )
    inst_name = calc.institution.name if ("institution" in calc.__dict__ and calc.institution) else None
    prog_name = calc.programme.programme_name if ("programme" in calc.__dict__ and calc.programme) else None
    ay_label = calc.academic_year.label if ("academic_year" in calc.__dict__ and calc.academic_year) else None

    return RiskCalculationResponse(
        id=calc.id,
        institution_id=calc.institution_id,
        institution_name=inst_name,
        programme_id=calc.programme_id,
        programme_name=prog_name,
        academic_year_id=calc.academic_year_id,
        academic_year_label=ay_label,
        total_score=calc.total_score,
        risk_band=calc.risk_band,
        calculation_version=calc.calculation_version,
        factors=factors,
        input_snapshot=snapshot,
        explanation=calc.explanation,
        completeness_state=calc.completeness_state,
        calculated_at=calc.calculated_at,
        is_active=calc.is_active
    )

@router.get("/risk-queue", response_model=RiskQueueResponse)
async def get_risk_queue(
    risk_band: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the prioritized risk review queue.
    Enforces scope: National users see all; institution users see their assigned institution.
    """
    allowed_ids = get_user_permitted_institution_ids(current_user)
    items, total = await RiskEngineService.get_risk_queue(
        session=db,
        risk_band=risk_band,
        search=search,
        allowed_institution_ids=allowed_ids,
        page=page,
        page_size=page_size
    )
    return RiskQueueResponse(
        items=[RiskQueueItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/institutions/{institution_id}/risk-profile", response_model=InstitutionRiskProfileResponse)
async def get_institution_risk_profile(
    institution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detailed risk profile and factor contributions for an institution.
    """
    enforce_institution_scope(current_user, institution_id)
    profile = await RiskEngineService.get_institution_risk_profile(session=db, institution_id=institution_id)

    formatted_curr = _format_calc_response(profile["current_calculation"]) if profile.get("current_calculation") else None
    formatted_hist = [_format_calc_response(c) for c in profile.get("history", [])]

    return InstitutionRiskProfileResponse(
        institution_id=profile["institution_id"],
        institution_name=profile["institution_name"],
        official_code=profile["official_code"],
        current_calculation=formatted_curr,
        history=formatted_hist,
        unresolved_findings_count=profile["unresolved_findings_count"],
        active_cases_count=profile["active_cases_count"],
        programmes_exceeding_capacity_count=profile["programmes_exceeding_capacity_count"]
    )

@router.get("/risk-calculations/{calculation_id}", response_model=RiskCalculationResponse)
async def get_risk_calculation(
    calculation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves an individual stored risk calculation record.
    """
    q = select(RiskCalculation).where(RiskCalculation.id == calculation_id)
    res = await db.execute(q)
    calc = res.scalar_one_or_none()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Risk calculation '{calculation_id}' not found.")

    enforce_institution_scope(current_user, calc.institution_id)
    return _format_calc_response(calc)

@router.post("/risk-calculations/recalculate/{institution_id}", response_model=RiskCalculationResponse)
@router.post("/institutions/{institution_id}/recalculate-risk", response_model=RiskCalculationResponse)
async def recalculate_risk(
    institution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers deterministic risk recalculation for an institution.
    Restricted to regulatory officers or national administrators.
    """
    roles = [r.code for r in current_user.roles]
    is_regulatory = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER") for r in roles)
    if not is_regulatory:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only regulatory officers can trigger risk recalculations.")

    calc = await RiskEngineService.calculate_institution_risk(
        session=db,
        institution_id=institution_id,
        triggered_by_user_id=current_user.id
    )
    return _format_calc_response(calc)
