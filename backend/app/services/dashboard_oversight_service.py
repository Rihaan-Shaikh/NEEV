from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear, ApprovedIntakeVersion, ProgrammeApproval
from app.models.student import EnrolmentRecord, StudentIdentity
from app.models.submission import SubmissionBatch
from app.models.integrity import Finding, FindingResponse
from app.models.oversight import AuditCase, ClarificationRequest, RiskCalculation
from app.models.user import User
from app.services.risk_engine_service import RiskEngineService

class DashboardOversightService:

    @classmethod
    async def get_national_metrics(
        cls,
        session: AsyncSession,
        current_user: User,
        user_roles: List[str],
        academic_year_id: Optional[str] = None,
        institution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates national oversight metrics strictly from PostgreSQL data."""
        is_national = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER", "AUDITOR") for r in user_roles)
        if not is_national:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only authorized national regulatory officers can inspect national oversight dashboard."
            )

        # 1. Academic year context
        if not academic_year_id:
            ay_res = await session.execute(select(AcademicYear).where(AcademicYear.status == "ACTIVE").limit(1))
            ay = ay_res.scalar_one_or_none()
            academic_year_id = ay.id if ay else None
            ay_label = ay.label if ay else "2026-2027"
        else:
            ay_res = await session.execute(select(AcademicYear).where(AcademicYear.id == academic_year_id))
            ay = ay_res.scalar_one_or_none()
            ay_label = ay.label if ay else "2026-2027"

        # 2. Covered institutions
        inst_q = select(func.count(Institution.id))
        if institution_id:
            inst_q = inst_q.where(Institution.id == institution_id)
        covered_institutions = (await session.execute(inst_q)).scalar() or 0

        # 3. Programmes with usable approved intake
        from app.models.programme import ProgrammeApproval
        prog_intake_q = select(func.count(func.distinct(ProgrammeApproval.programme_id)))
        if academic_year_id:
            prog_intake_q = prog_intake_q.where(ProgrammeApproval.academic_year_id == academic_year_id)
        programmes_with_intake = (await session.execute(prog_intake_q)).scalar() or 0

        # 4. Enrolment counts
        tot_enr_q = select(func.count(EnrolmentRecord.id))
        if academic_year_id:
            tot_enr_q = tot_enr_q.where(EnrolmentRecord.academic_year_id == academic_year_id)
        if institution_id:
            tot_enr_q = tot_enr_q.where(EnrolmentRecord.institution_id == institution_id)
        total_submitted_enrolments = (await session.execute(tot_enr_q)).scalar() or 0

        act_enr_q = select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.enrolment_status == "ACTIVE")
        if academic_year_id:
            act_enr_q = act_enr_q.where(EnrolmentRecord.academic_year_id == academic_year_id)
        if institution_id:
            act_enr_q = act_enr_q.where(EnrolmentRecord.institution_id == institution_id)
        total_active_enrolments = (await session.execute(act_enr_q)).scalar() or 0

        # 5. Submission completion rate
        tot_insts_q = select(func.count(Institution.id))
        tot_insts = (await session.execute(tot_insts_q)).scalar() or 1
        fin_batches_q = select(func.count(func.distinct(SubmissionBatch.institution_id))).where(SubmissionBatch.processing_status == "COMPLETED")
        if academic_year_id:
            fin_batches_q = fin_batches_q.where(SubmissionBatch.academic_year_id == academic_year_id)
        finished_insts = (await session.execute(fin_batches_q)).scalar() or 0
        submission_completion_rate_pct = round((finished_insts / tot_insts) * 100, 1)

        # 6. Quality percentages
        if total_submitted_enrolments > 0:
            complete_fields_q = select(func.count(EnrolmentRecord.id)).where(
                and_(
                    EnrolmentRecord.admission_date.is_not(None),
                    EnrolmentRecord.admission_category.is_not(None),
                    EnrolmentRecord.programme_id.is_not(None)
                )
            )
            if academic_year_id:
                complete_fields_q = complete_fields_q.where(EnrolmentRecord.academic_year_id == academic_year_id)
            if institution_id:
                complete_fields_q = complete_fields_q.where(EnrolmentRecord.institution_id == institution_id)
            complete_fields_count = (await session.execute(complete_fields_q)).scalar() or 0
            required_fields_complete_pct = round((complete_fields_count / total_submitted_enrolments) * 100, 1)

            valid_apaar_q = (
                select(func.count(EnrolmentRecord.id))
                .join(StudentIdentity, EnrolmentRecord.student_identity_id == StudentIdentity.id)
                .where(
                    and_(
                        EnrolmentRecord.student_identity_id.is_not(None),
                        StudentIdentity.apaar_validation_status != "MALFORMED"
                    )
                )
            )
            if academic_year_id:
                valid_apaar_q = valid_apaar_q.where(EnrolmentRecord.academic_year_id == academic_year_id)
            if institution_id:
                valid_apaar_q = valid_apaar_q.where(EnrolmentRecord.institution_id == institution_id)
            valid_apaar_count = (await session.execute(valid_apaar_q)).scalar() or 0
            valid_format_apaar_pct = round((valid_apaar_count / total_submitted_enrolments) * 100, 1)
        else:
            required_fields_complete_pct = 100.0
            valid_format_apaar_pct = 100.0

        # 7. Unresolved conflict findings
        unres_conf_q = select(func.count(Finding.id)).where(
            and_(
                Finding.status.in_(["OPEN", "AWAITING_INSTITUTION_RESPONSE", "RESPONSE_RECEIVED", "UNDER_REVIEW"]),
                Finding.rule_code.in_(["DUP-001", "DUP-002", "DUP-003"])
            )
        )
        if institution_id:
            unres_conf_q = unres_conf_q.where(or_(Finding.primary_institution_id == institution_id, Finding.secondary_institution_id == institution_id))
        unresolved_conflict_findings_count = (await session.execute(unres_conf_q)).scalar() or 0

        # 8. Programmes requiring intake review
        all_progs_q = select(Programme).options(
            selectinload(Programme.approvals).selectinload(ProgrammeApproval.intake_versions)
        )
        all_progs = (await session.execute(all_progs_q)).scalars().all()
        exceeded_progs_count = 0
        for p in all_progs:
            act_q = select(func.count(EnrolmentRecord.id)).where(
                and_(EnrolmentRecord.programme_id == p.id, EnrolmentRecord.enrolment_status == "ACTIVE")
            )
            p_act = (await session.execute(act_q)).scalar() or 0
            approval = p.approvals[0] if p.approvals else None
            intake_obj = sorted(approval.intake_versions, key=lambda v: v.version, reverse=True)[0] if approval and approval.intake_versions else None
            p_int = intake_obj.approved_intake if intake_obj else None
            if p_int is not None and p_act > p_int:
                exceeded_progs_count += 1
            elif p_int is None and p_act > 0:
                exceeded_progs_count += 1

        # 9. Open correction requests
        open_corr_q = select(func.count(FindingResponse.id)).where(
            and_(FindingResponse.response_type == "CORRECTION_REQUEST", FindingResponse.review_status == "PENDING")
        )
        open_correction_requests_count = (await session.execute(open_corr_q)).scalar() or 0

        # 10. Open audit cases
        open_cases_q = select(func.count(AuditCase.id)).where(
            AuditCase.status.in_(["OPEN", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RESPONSE_RECEIVED"])
        )
        if institution_id:
            open_cases_q = open_cases_q.where(AuditCase.institution_id == institution_id)
        open_audit_cases_count = (await session.execute(open_cases_q)).scalar() or 0

        # 11. Distributions
        rb_dist = {"ROUTINE": 0, "WATCH": 0, "REVIEW_RECOMMENDED": 0, "PRIORITY_REVIEW": 0}
        rb_q = select(RiskCalculation.risk_band, func.count(RiskCalculation.id)).where(RiskCalculation.is_active.is_(True)).group_by(RiskCalculation.risk_band)
        for band, count in (await session.execute(rb_q)).all():
            if band in rb_dist:
                rb_dist[band] = count

        f_cat_dist = {}
        f_cat_q = select(Finding.category, func.count(Finding.id)).group_by(Finding.category)
        for cat, count in (await session.execute(f_cat_q)).all():
            f_cat_dist[cat] = count

        cases_st_dist = {}
        c_st_q = select(AuditCase.status, func.count(AuditCase.id)).group_by(AuditCase.status)
        for st, count in (await session.execute(c_st_q)).all():
            cases_st_dist[st] = count

        return {
            "covered_institutions_count": covered_institutions,
            "programmes_with_intake_count": programmes_with_intake,
            "total_submitted_enrolments": total_submitted_enrolments,
            "total_active_enrolments": total_active_enrolments,
            "submission_completion_rate_pct": submission_completion_rate_pct,
            "required_fields_complete_pct": required_fields_complete_pct,
            "valid_format_apaar_pct": valid_format_apaar_pct,
            "unresolved_conflict_findings_count": unresolved_conflict_findings_count,
            "programmes_requiring_intake_review_count": exceeded_progs_count,
            "open_correction_requests_count": open_correction_requests_count,
            "open_audit_cases_count": open_audit_cases_count,
            "risk_band_distribution": rb_dist,
            "findings_by_category": f_cat_dist,
            "cases_by_status": cases_st_dist,
            "academic_year_label": ay_label
        }

    @classmethod
    async def get_institution_metrics(
        cls,
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        institution_id: str
    ) -> Dict[str, Any]:
        """Calculates institution-scoped metrics with strict tenant isolation."""
        is_national = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER", "AUDITOR") for r in user_roles)
        if not is_national:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if user_inst_id != institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You cannot access metrics for another institution."
                )

        inst_res = await session.execute(select(Institution).where(Institution.id == institution_id))
        institution = inst_res.scalar_one_or_none()
        if not institution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Institution '{institution_id}' not found.")

        # Academic year
        ay_res = await session.execute(select(AcademicYear).where(AcademicYear.status == "ACTIVE").limit(1))
        ay = ay_res.scalar_one_or_none()
        ay_label = ay.label if ay else "2026-2027"

        # Totals
        tot_enr = (await session.execute(select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.institution_id == institution_id))).scalar() or 0
        act_enr = (await session.execute(select(func.count(EnrolmentRecord.id)).where(and_(EnrolmentRecord.institution_id == institution_id, EnrolmentRecord.enrolment_status == "ACTIVE")))).scalar() or 0

        progs = (await session.execute(
            select(Programme).options(
                selectinload(Programme.approvals).selectinload(ProgrammeApproval.intake_versions)
            ).where(Programme.institution_id == institution_id)
        )).scalars().all()
        programmes_count = len(progs)

        exceeded_count = 0
        for p in progs:
            p_act = (await session.execute(select(func.count(EnrolmentRecord.id)).where(and_(EnrolmentRecord.programme_id == p.id, EnrolmentRecord.enrolment_status == "ACTIVE")))).scalar() or 0
            approval = p.approvals[0] if p.approvals else None
            intake_obj = sorted(approval.intake_versions, key=lambda v: v.version, reverse=True)[0] if approval and approval.intake_versions else None
            p_int = intake_obj.approved_intake if intake_obj else None
            if p_int is not None and p_act > p_int:
                exceeded_count += 1

        open_f = (await session.execute(select(func.count(Finding.id)).where(and_(Finding.primary_institution_id == institution_id, Finding.status == "OPEN")))).scalar() or 0
        awaiting_f = (await session.execute(select(func.count(Finding.id)).where(and_(Finding.primary_institution_id == institution_id, Finding.status == "AWAITING_INSTITUTION_RESPONSE")))).scalar() or 0
        resp_f = (await session.execute(select(func.count(Finding.id)).where(and_(Finding.primary_institution_id == institution_id, Finding.status == "RESPONSE_RECEIVED")))).scalar() or 0
        resolved_f = (await session.execute(select(func.count(Finding.id)).where(and_(Finding.primary_institution_id == institution_id, Finding.status == "RESOLVED")))).scalar() or 0

        # Clarifications and Cases
        open_clrs = (await session.execute(select(func.count(ClarificationRequest.id)).where(and_(ClarificationRequest.institution_id == institution_id, ClarificationRequest.status == "PENDING_RESPONSE")))).scalar() or 0
        active_cases = (await session.execute(select(func.count(AuditCase.id)).where(and_(AuditCase.institution_id == institution_id, AuditCase.status.in_(["OPEN", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RESPONSE_RECEIVED"]))))).scalar() or 0

        # Latest receipt
        rec_batch = (await session.execute(select(SubmissionBatch).where(and_(SubmissionBatch.institution_id == institution_id, SubmissionBatch.receipt_reference.is_not(None))).order_by(SubmissionBatch.created_at.desc()).limit(1))).scalar_one_or_none()
        latest_receipt = rec_batch.receipt_reference if rec_batch else None

        # Risk calculation
        calc = (await session.execute(select(RiskCalculation).where(and_(RiskCalculation.institution_id == institution_id, RiskCalculation.is_active.is_(True))).order_by(RiskCalculation.calculated_at.desc()).limit(1))).scalar_one_or_none()
        if not calc:
            calc = await RiskEngineService.calculate_institution_risk(session, institution_id)

        submission_pct = 100.0 if (rec_batch and rec_batch.processing_status == "COMPLETED") else 0.0

        return {
            "institution_id": institution.id,
            "institution_name": institution.name,
            "official_code": institution.official_institution_code,
            "submission_progress_pct": submission_pct,
            "total_enrolments_count": tot_enr,
            "active_enrolments_count": act_enr,
            "programmes_count": programmes_count,
            "programmes_exceeding_capacity_count": exceeded_count,
            "open_findings_count": open_f,
            "findings_awaiting_response_count": awaiting_f,
            "responses_submitted_count": resp_f,
            "resolved_findings_count": resolved_f,
            "open_clarification_requests_count": open_clrs,
            "active_audit_cases_count": active_cases,
            "latest_receipt_reference": latest_receipt,
            "current_risk_band": calc.risk_band,
            "current_risk_score": calc.total_score,
            "academic_year_label": ay_label
        }
