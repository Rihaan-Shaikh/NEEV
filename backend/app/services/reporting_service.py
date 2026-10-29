import csv
import io
import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear, ApprovedIntakeVersion
from app.models.student import EnrolmentRecord, EnrolmentRecordVersion, StudentIdentity
from app.models.submission import SubmissionBatch
from app.models.integrity import Finding
from app.models.oversight import AuditCase, ReportJob
from app.models.audit import AuditEvent
from app.models.user import User

STORAGE_REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "reports")
os.makedirs(STORAGE_REPORTS_DIR, exist_ok=True)

class ReportingService:
    REPORT_CATALOG = [
        {
            "report_type": "ENROLMENT_RECONCILIATION",
            "title": "Institution-level enrolment reconciliation",
            "description": "Comprehensive institutional enrolment totals compared against approved intake capacities.",
            "category": "RECONCILIATION"
        },
        {
            "report_type": "PROGRAMME_INTAKE_VARIANCE",
            "title": "Programme and intake variance",
            "description": "Approved intake, active enrolments, variance counts, and over-capacity status per programme.",
            "category": "CAPACITY"
        },
        {
            "report_type": "DATA_QUALITY_SUMMARY",
            "title": "Data-quality summary",
            "description": "Validation findings breakdown across schema, date, and enumeration validation rules.",
            "category": "QUALITY"
        },
        {
            "report_type": "IDENTIFIER_COVERAGE",
            "title": "Identifier coverage and validation status",
            "description": "Coverage statistics for APAAR identifiers, including linked, unlinked, and unverified states.",
            "category": "IDENTIFIER"
        },
        {
            "report_type": "DUPLICATE_CONFLICT_FINDINGS",
            "title": "Duplicate and conflict findings",
            "description": "Active cross-institution dual active enrolments and batch duplicate discrepancies.",
            "category": "INTEGRITY"
        },
        {
            "report_type": "FINDING_RESOLUTION_PERFORMANCE",
            "title": "Finding-resolution performance",
            "description": "Lifecycle transition and resolution performance for discrepancies across institutions.",
            "category": "OPERATIONAL"
        },
        {
            "report_type": "SUBMISSION_TIMELINESS",
            "title": "Submission timeliness and batch turnaround",
            "description": "Historical submission turnaround times, row volumes, and processing outcomes.",
            "category": "SUBMISSIONS"
        },
        {
            "report_type": "AUDIT_CASE_STATUS_OUTCOMES",
            "title": "Audit case status and outcomes",
            "description": "Regulatory review cases, assignment distribution, clarification requests, and decisions.",
            "category": "REGULATORY"
        },
        {
            "report_type": "HISTORICAL_RECORD_CHANGES",
            "title": "Historical record changes",
            "description": "Auditable log of material enrolment corrections, change reasons, and updated attributes.",
            "category": "AUDIT"
        },
        {
            "report_type": "STATE_PROGRAMME_AGGREGATES",
            "title": "State and programme aggregates",
            "description": "Regional student enrolments and institution counts aggregated by state jurisdiction.",
            "category": "AGGREGATE"
        }
    ]

    @staticmethod
    def sanitize_csv_cell(value: Any) -> str:
        """
        Neutralizes spreadsheet formula injection (CSV Injection).
        Prepends a single quote if string begins with =, +, -, @, \t, or \r.
        """
        if value is None:
            return ""
        str_val = str(value)
        if str_val and str_val[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{str_val}"
        return str_val

    @classmethod
    async def create_report_job(
        cls,
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        report_type: str,
        institution_id: Optional[str] = None,
        academic_year_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ReportJob:
        now = datetime.now(timezone.utc)
        is_national = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER", "AUDITOR") for r in user_roles)

        # Validate report type in catalog
        valid_types = [r["report_type"] for r in cls.REPORT_CATALOG]
        if report_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report type '{report_type}'. Must be one of {valid_types}."
            )

        # Enforce institutional scoping
        if not is_national:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if not user_inst_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No institutional scope assigned.")
            institution_id = user_inst_id  # Force scope

        title_match = next((r["title"] for r in cls.REPORT_CATALOG if r["report_type"] == report_type), "NEEV Regulatory Report")

        job = ReportJob(
            report_type=report_type,
            report_title=title_match,
            status="QUEUED",
            requester_user_id=current_user.id,
            institution_id=institution_id,
            academic_year_id=academic_year_id,
            filter_criteria_json=json.dumps(filters or {}),
            created_at=now
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Generate report content synchronously for reliable developer/test feedback
        await cls._execute_report_generation(session, job)
        return job

    @classmethod
    async def _execute_report_generation(cls, session: AsyncSession, job: ReportJob) -> None:
        """Executes real PostgreSQL queries, formats CSV, and stores artifact safely."""
        now = datetime.now(timezone.utc)
        job.status = "RUNNING"
        await session.commit()

        try:
            headers = []
            rows = []

            # ---------------- 1. ENROLMENT_RECONCILIATION ----------------
            if job.report_type == "ENROLMENT_RECONCILIATION":
                headers = ["Institution Code", "Institution Name", "State", "Active Enrolments", "Programmes Count"]
                q = select(
                    Institution.official_institution_code,
                    Institution.name,
                    Institution.state_code,
                    func.count(EnrolmentRecord.id).label("active_enr")
                ).outerjoin(
                    EnrolmentRecord,
                    and_(EnrolmentRecord.institution_id == Institution.id, EnrolmentRecord.enrolment_status == "ACTIVE")
                ).group_by(Institution.id)
                if job.institution_id:
                    q = q.where(Institution.id == job.institution_id)
                res = await session.execute(q)
                for code, name, state, active_enr in res.all():
                    # count programmes
                    pq = select(func.count(Programme.id)).where(Programme.institution_id == Institution.id)
                    p_count = (await session.execute(pq)).scalar() or 0
                    rows.append([code, name, state or "N/A", active_enr, p_count])

            # ---------------- 2. PROGRAMME_INTAKE_VARIANCE ----------------
            elif job.report_type == "PROGRAMME_INTAKE_VARIANCE":
                from app.models.programme import ProgrammeApproval
                pq = select(Programme).options(
                    selectinload(Programme.institution),
                    selectinload(Programme.approvals).selectinload(ProgrammeApproval.intake_versions)
                )
                if job.institution_id:
                    pq = pq.where(Programme.institution_id == job.institution_id)
                programmes = (await session.execute(pq)).scalars().all()
                for p in programmes:
                    # Active enrolments
                    eq = select(func.count(EnrolmentRecord.id)).where(
                        and_(EnrolmentRecord.programme_id == p.id, EnrolmentRecord.enrolment_status == "ACTIVE")
                    )
                    active_count = (await session.execute(eq)).scalar() or 0
                    # Approved intake
                    approval = p.approvals[0] if p.approvals else None
                    intake_obj = sorted(approval.intake_versions, key=lambda v: v.version, reverse=True)[0] if approval and approval.intake_versions else None
                    approved_intake = intake_obj.approved_intake if intake_obj else "Not Configured"
                    if isinstance(approved_intake, int):
                        variance = active_count - approved_intake
                        cap_status = "EXCEEDED" if variance > 0 else "BALANCED" if variance == 0 else "UNDER_CAPACITY"
                    else:
                        variance = "N/A"
                        cap_status = "MISSING_REFERENCE"
                    rows.append([
                        p.institution.name if p.institution else "Unknown",
                        p.official_programme_code,
                        p.programme_name,
                        approved_intake,
                        active_count,
                        variance,
                        cap_status
                    ])

            # ---------------- 3. DATA_QUALITY_SUMMARY ----------------
            elif job.report_type == "DATA_QUALITY_SUMMARY":
                headers = ["Institution", "Total Enrolments", "Missing APAAR Count", "Malformed APAAR Count", "Unverified Source Count"]
                iq = select(Institution)
                if job.institution_id:
                    iq = iq.where(Institution.id == job.institution_id)
                institutions = (await session.execute(iq)).scalars().all()
                for inst in institutions:
                    tot_q = select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.institution_id == inst.id)
                    tot = (await session.execute(tot_q)).scalar() or 0
                    mis_q = select(func.count(EnrolmentRecord.id)).where(and_(EnrolmentRecord.institution_id == inst.id, EnrolmentRecord.student_identity_id.is_(None)))
                    mis = (await session.execute(mis_q)).scalar() or 0
                    mal_q = (
                        select(func.count(EnrolmentRecord.id))
                        .join(StudentIdentity, EnrolmentRecord.student_identity_id == StudentIdentity.id)
                        .where(and_(EnrolmentRecord.institution_id == inst.id, StudentIdentity.apaar_validation_status == "MALFORMED"))
                    )
                    mal = (await session.execute(mal_q)).scalar() or 0
                    unv_q = (
                        select(func.count(EnrolmentRecord.id))
                        .join(StudentIdentity, EnrolmentRecord.student_identity_id == StudentIdentity.id)
                        .where(and_(EnrolmentRecord.institution_id == inst.id, StudentIdentity.apaar_validation_status.in_(["UNAVAILABLE", "SIMULATED"])))
                    )
                    unv = (await session.execute(unv_q)).scalar() or 0
                    rows.append([inst.name, tot, mis, mal, unv])

            # ---------------- 4. IDENTIFIER_COVERAGE ----------------
            elif job.report_type == "IDENTIFIER_COVERAGE":
                headers = ["Institution", "Total Enrolments", "APAAR Linked Count", "Coverage Percentage", "Simulated Count"]
                iq = select(Institution)
                if job.institution_id:
                    iq = iq.where(Institution.id == job.institution_id)
                institutions = (await session.execute(iq)).scalars().all()
                for inst in institutions:
                    tot_q = select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.institution_id == inst.id)
                    tot = (await session.execute(tot_q)).scalar() or 0
                    linked_q = select(func.count(EnrolmentRecord.id)).where(and_(EnrolmentRecord.institution_id == inst.id, EnrolmentRecord.student_identity_id.is_not(None)))
                    linked = (await session.execute(linked_q)).scalar() or 0
                    sim_q = (
                        select(func.count(EnrolmentRecord.id))
                        .join(StudentIdentity, EnrolmentRecord.student_identity_id == StudentIdentity.id)
                        .where(and_(EnrolmentRecord.institution_id == inst.id, StudentIdentity.apaar_validation_status == "SIMULATED"))
                    )
                    sim = (await session.execute(sim_q)).scalar() or 0
                    pct = f"{(linked / tot * 100):.1f}%" if tot > 0 else "0.0%"
                    rows.append([inst.name, tot, linked, pct, sim])

            # ---------------- 5. DUPLICATE_CONFLICT_FINDINGS ----------------
            elif job.report_type == "DUPLICATE_CONFLICT_FINDINGS":
                headers = ["Finding ID", "Rule Code", "Severity", "Status", "Primary Institution", "Secondary Institution", "Detected Date"]
                fq = select(Finding).options(selectinload(Finding.primary_institution), selectinload(Finding.secondary_institution))
                if job.institution_id:
                    fq = fq.where(or_(Finding.primary_institution_id == job.institution_id, Finding.secondary_institution_id == job.institution_id))
                findings = (await session.execute(fq.order_by(Finding.created_at.desc()))).scalars().all()
                for f in findings:
                    rows.append([
                        f.id,
                        f.rule_code,
                        f.severity,
                        f.status,
                        f.primary_institution.name if f.primary_institution else "N/A",
                        f.secondary_institution.name if f.secondary_institution else "N/A",
                        f.first_detected_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])

            # ---------------- 6. FINDING_RESOLUTION_PERFORMANCE ----------------
            elif job.report_type == "FINDING_RESOLUTION_PERFORMANCE":
                headers = ["Status", "Findings Count", "Percentage of Total"]
                tot_q = select(func.count(Finding.id))
                if job.institution_id:
                    tot_q = tot_q.where(or_(Finding.primary_institution_id == job.institution_id, Finding.secondary_institution_id == job.institution_id))
                tot = (await session.execute(tot_q)).scalar() or 0
                sq = select(Finding.status, func.count(Finding.id))
                if job.institution_id:
                    sq = sq.where(or_(Finding.primary_institution_id == job.institution_id, Finding.secondary_institution_id == job.institution_id))
                counts = (await session.execute(sq.group_by(Finding.status))).all()
                for st, count in counts:
                    pct = f"{(count / tot * 100):.1f}%" if tot > 0 else "0.0%"
                    rows.append([st, count, pct])

            # ---------------- 7. SUBMISSION_TIMELINESS ----------------
            elif job.report_type == "SUBMISSION_TIMELINESS":
                headers = ["Batch Reference", "Institution", "Status", "Row Count", "Submitted At"]
                bq = select(SubmissionBatch).options(selectinload(SubmissionBatch.institution))
                if job.institution_id:
                    bq = bq.where(SubmissionBatch.institution_id == job.institution_id)
                batches = (await session.execute(bq.order_by(SubmissionBatch.created_at.desc()).limit(100))).scalars().all()
                for b in batches:
                    rows.append([
                        b.receipt_reference or b.id,
                        b.institution.name if b.institution else "N/A",
                        b.processing_status,
                        b.row_count,
                        b.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])

            # ---------------- 8. AUDIT_CASE_STATUS_OUTCOMES ----------------
            elif job.report_type == "AUDIT_CASE_STATUS_OUTCOMES":
                headers = ["Case Reference", "Institution", "Category", "Priority", "Status", "Created Date", "Closed Date"]
                cq = select(AuditCase).options(selectinload(AuditCase.institution))
                if job.institution_id:
                    cq = cq.where(AuditCase.institution_id == job.institution_id)
                cases = (await session.execute(cq.order_by(AuditCase.created_at.desc()))).scalars().all()
                for c in cases:
                    rows.append([
                        c.case_reference,
                        c.institution.name if c.institution else "N/A",
                        c.case_category,
                        c.priority,
                        c.status,
                        c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        c.closed_at.strftime("%Y-%m-%d %H:%M:%S") if c.closed_at else "Active"
                    ])

            # ---------------- 9. HISTORICAL_RECORD_CHANGES ----------------
            elif job.report_type == "HISTORICAL_RECORD_CHANGES":
                headers = ["Enrolment Record ID", "Version", "Change Reason", "Changed At"]
                vq = select(EnrolmentRecordVersion).join(EnrolmentRecord)
                if job.institution_id:
                    vq = vq.where(EnrolmentRecord.institution_id == job.institution_id)
                versions = (await session.execute(vq.order_by(EnrolmentRecordVersion.changed_at.desc()).limit(100))).scalars().all()
                for v in versions:
                    rows.append([
                        v.enrolment_record_id,
                        f"v{v.version_number}",
                        v.change_reason,
                        v.changed_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])

            # ---------------- 10. STATE_PROGRAMME_AGGREGATES ----------------
            else:
                headers = ["State", "Institutions Count", "Programmes Count"]
                sq = select(Institution.state_code, func.count(Institution.id)).group_by(Institution.state_code)
                states = (await session.execute(sq)).all()
                for st, count in states:
                    pq = select(func.count(Programme.id)).join(Institution).where(Institution.state_code == st)
                    p_count = (await session.execute(pq)).scalar() or 0
                    rows.append([st or "Unassigned", count, p_count])

            # Write sanitized CSV file
            filename = f"report_{job.id[:8]}_{now.strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(STORAGE_REPORTS_DIR, filename)

            with open(filepath, mode="w", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out)
                # Write metadata comments at top
                writer.writerow([f"# NEEV Regulatory Report: {job.report_title}"])
                writer.writerow([f"# Generated At: {now.isoformat()}"])
                writer.writerow([f"# Report Job ID: {job.id}"])
                writer.writerow([f"# Data Classification: RESTRICTED REGULATORY"])
                writer.writerow([])
                # Write header row
                writer.writerow([cls.sanitize_csv_cell(h) for h in headers])
                # Write data rows with formula injection neutralization
                for row in rows:
                    writer.writerow([cls.sanitize_csv_cell(cell) for cell in row])

            file_size = os.path.getsize(filepath)
            job.status = "COMPLETED"
            job.file_path = filepath
            job.file_size_bytes = file_size
            job.row_count = len(rows)
            job.completed_at = now

            # Audit event
            audit = AuditEvent(
                actor_user_id=job.requester_user_id,
                actor_type="SYSTEM",
                action="REPORT_GENERATION",
                target_type="REPORT_JOB",
                target_id=job.id,
                occurred_at=now,
                outcome="SUCCESS",
                metadata_json=json.dumps({
                    "report_type": job.report_type,
                    "rows_count": len(rows),
                    "file_size": file_size
                })
            )
            session.add(audit)
            await session.commit()

        except Exception as e:
            job.status = "FAILED"
            job.error_message = f"Report generation failed: {str(e)}"
            job.completed_at = now
            await session.commit()

    @classmethod
    async def get_report_download(
        cls,
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        report_id: str
    ) -> FileResponse:
        now = datetime.now(timezone.utc)
        is_national = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER", "AUDITOR") for r in user_roles)

        job_res = await session.execute(select(ReportJob).where(ReportJob.id == report_id))
        job = job_res.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report job '{report_id}' not found.")

        # Scope verification
        if not is_national:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if not job.institution_id or user_inst_id != job.institution_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not have permission to download this report.")

        if job.status != "COMPLETED" or not job.file_path or not os.path.exists(job.file_path):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report artifact is not ready or has expired.")

        # Audit download
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="REPORT_DOWNLOAD",
            target_type="REPORT_JOB",
            target_id=job.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "report_type": job.report_type,
                "report_id": job.id
            })
        )
        session.add(audit)
        await session.commit()

        clean_name = f"{job.report_type.lower()}_{job.id[:8]}.csv"
        return FileResponse(
            path=job.file_path,
            filename=clean_name,
            media_type="text/csv",
            content_disposition_type="attachment"
        )
