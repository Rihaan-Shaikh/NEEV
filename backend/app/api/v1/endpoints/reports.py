from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.models.user import User
from app.models.oversight import ReportJob
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)
from app.schemas.oversight import (
    ReportDefinition,
    ReportJobCreateRequest,
    ReportJobResponse
)
from app.services.reporting_service import ReportingService

router = APIRouter()

@router.get("", response_model=List[ReportDefinition])
async def list_report_catalog(
    current_user: User = Depends(get_current_user)
):
    """
    Returns available regulatory report definitions.
    """
    return [ReportDefinition(**item) for item in ReportingService.REPORT_CATALOG]

@router.post("", response_model=ReportJobResponse)
async def create_report_job(
    payload: ReportJobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiates report generation job using real PostgreSQL data.
    """
    roles = [r.code for r in current_user.roles]
    job = await ReportingService.create_report_job(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        report_type=payload.report_type,
        institution_id=payload.institution_id,
        academic_year_id=payload.academic_year_id,
        filters={"state": payload.state, "date_from": payload.date_from, "date_to": payload.date_to}
    )
    return ReportJobResponse.model_validate(job)

@router.get("/jobs", response_model=List[ReportJobResponse])
async def list_report_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists recent report generation jobs for the current user and permitted scope.
    """
    allowed_ids = get_user_permitted_institution_ids(current_user)
    q = (
        select(ReportJob)
        .options(selectinload(ReportJob.institution), selectinload(ReportJob.academic_year))
        .order_by(ReportJob.created_at.desc())
        .limit(30)
    )
    if allowed_ids is not None:
        q = q.where(ReportJob.institution_id.in_(allowed_ids))

    jobs = (await db.execute(q)).scalars().all()
    return [
        ReportJobResponse(
            id=j.id,
            report_type=j.report_type,
            report_title=j.report_title,
            status=j.status,
            institution_id=j.institution_id,
            institution_name=j.institution.name if j.institution else None,
            academic_year_label=j.academic_year.label if j.academic_year else None,
            row_count=j.row_count,
            file_size_bytes=j.file_size_bytes,
            error_message=j.error_message,
            created_at=j.created_at,
            completed_at=j.completed_at
        )
        for j in jobs
    ]

@router.get("/{report_id}", response_model=ReportJobResponse)
async def get_report_job(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves status and metadata of a report job.
    """
    q = (
        select(ReportJob)
        .options(selectinload(ReportJob.institution), selectinload(ReportJob.academic_year))
        .where(ReportJob.id == report_id)
    )
    job = (await db.execute(q)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report job '{report_id}' not found.")

    enforce_institution_scope(current_user, job.institution_id)
    return ReportJobResponse(
        id=job.id,
        report_type=job.report_type,
        report_title=job.report_title,
        status=job.status,
        institution_id=job.institution_id,
        institution_name=job.institution.name if job.institution else None,
        academic_year_label=job.academic_year.label if job.academic_year else None,
        row_count=job.row_count,
        file_size_bytes=job.file_size_bytes,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at
    )

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Downloads generated CSV report with formula-injection neutralization and scope checking.
    """
    roles = [r.code for r in current_user.roles]
    return await ReportingService.get_report_download(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        report_id=report_id
    )
