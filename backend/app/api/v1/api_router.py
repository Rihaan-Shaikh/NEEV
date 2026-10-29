from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    institutions,
    programmes,
    academic_years,
    batches,
    enrolments,
    dashboard,
    health,
    findings,
    evidence,
    integrity,
    notifications,
    audit,
    oversight_dashboard,
    risk,
    cases,
    reports,
    verification,
    integrations
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["Institutions"])
api_router.include_router(programmes.router, prefix="/programmes", tags=["Programmes"])
api_router.include_router(academic_years.router, prefix="/academic-years", tags=["Academic Years"])
api_router.include_router(batches.router, prefix="/batches", tags=["Submissions"])
api_router.include_router(enrolments.router, prefix="/enrolments", tags=["Enrolments"])
api_router.include_router(findings.router, prefix="/findings", tags=["Findings & Discrepancies"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence Metadata & Storage"])
api_router.include_router(integrity.router, prefix="/integrity", tags=["Integrity Ledger & Conflicts"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(audit.router, prefix="/audit-events", tags=["Audit Events"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(oversight_dashboard.router, prefix="/dashboard", tags=["Oversight Dashboard"])
api_router.include_router(risk.router, prefix="", tags=["Risk Engine & Queue"])
api_router.include_router(cases.router, prefix="", tags=["Audit Case Management & Clarifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reporting & Exports"])
api_router.include_router(verification.router, prefix="", tags=["Verification References & Resolver"])
api_router.include_router(integrations.router, prefix="", tags=["External Integrations Status"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])

