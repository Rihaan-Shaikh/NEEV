from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.policies.authorization import get_current_user
from app.schemas.oversight import (
    NationalDashboardMetricsResponse,
    InstitutionDashboardMetricsResponse
)
from app.services.dashboard_oversight_service import DashboardOversightService

router = APIRouter()

@router.get("/national", response_model=NationalDashboardMetricsResponse)
async def get_national_dashboard(
    academic_year_id: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves national overview metrics derived strictly from PostgreSQL.
    Requires national regulatory authority (PLATFORM_ADMIN, AICTE_ADMIN, AICTE_OFFICER, AUDITOR).
    """
    roles = [r.code for r in current_user.roles]
    return await DashboardOversightService.get_national_metrics(
        session=db,
        current_user=current_user,
        user_roles=roles,
        academic_year_id=academic_year_id,
        institution_id=institution_id
    )

@router.get("/institution/{institution_id}", response_model=InstitutionDashboardMetricsResponse)
async def get_institution_dashboard(
    institution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves institution-specific dashboard metrics with strict tenant isolation.
    """
    roles = [r.code for r in current_user.roles]
    return await DashboardOversightService.get_institution_metrics(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        institution_id=institution_id
    )

from app.models.programme import AcademicYear
from app.models.institution import Institution
from sqlalchemy import select

@router.get("/filters")
async def get_dashboard_filters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns valid filter metadata (academic years, states, risk priority bands, case categories).
    """
    ays = (await db.execute(select(AcademicYear).order_by(AcademicYear.start_date.desc()))).scalars().all()
    states_query = select(Institution.state_code).distinct()
    states = (await db.execute(states_query)).scalars().all()

    return {
        "academic_years": [{"id": ay.id, "label": ay.label, "status": ay.status} for ay in ays],
        "states": sorted([s for s in states if s]),
        "risk_bands": ["ROUTINE", "WATCH", "REVIEW_RECOMMENDED", "PRIORITY_REVIEW"],
        "case_statuses": ["OPEN", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RESPONSE_RECEIVED", "RESOLVED", "ESCALATED", "CLOSED_NO_ACTION"],
        "case_priorities": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    }
