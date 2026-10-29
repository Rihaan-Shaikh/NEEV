import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload

from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear, ApprovedIntakeVersion
from app.models.student import EnrolmentRecord, EnrolmentRecordVersion, StudentIdentity
from app.models.integrity import Finding
from app.models.oversight import RiskCalculation
from app.models.audit import AuditEvent

class RiskEngineService:
    CALCULATION_VERSION = "1.0.0"

    @staticmethod
    def determine_risk_band(score: float) -> str:
        """Deterministic risk band categorization based on documented thresholds."""
        if score < 20.0:
            return "ROUTINE"
        elif score < 40.0:
            return "WATCH"
        elif score < 70.0:
            return "REVIEW_RECOMMENDED"
        else:
            return "PRIORITY_REVIEW"

    @classmethod
    async def calculate_institution_risk(
        cls,
        session: AsyncSession,
        institution_id: str,
        academic_year_id: Optional[str] = None,
        triggered_by_user_id: Optional[str] = None
    ) -> RiskCalculation:
        """
        Calculates deterministic, versioned risk score for an institution.
        Stores input snapshot, factor breakdown, and plain-language explanation.
        """
        now = datetime.now(timezone.utc)

        # 1. Verify institution exists
        inst_res = await session.execute(select(Institution).where(Institution.id == institution_id))
        institution = inst_res.scalar_one_or_none()
        if not institution:
            raise ValueError(f"Institution with ID '{institution_id}' not found.")

        # 2. Get active academic year if not provided
        if not academic_year_id:
            ay_res = await session.execute(select(AcademicYear).where(AcademicYear.status == "ACTIVE").limit(1))
            ay = ay_res.scalar_one_or_none()
            academic_year_id = ay.id if ay else None

        # ---------------- Factor 1: Capacity Discrepancy (max 25) ----------------
        from app.models.programme import ProgrammeApproval
        prog_query = select(Programme).options(
            selectinload(Programme.approvals).selectinload(ProgrammeApproval.intake_versions)
        ).where(Programme.institution_id == institution_id)
        programmes = (await session.execute(prog_query)).scalars().all()

        exceeded_count = 0
        missing_intake_count = 0
        total_active_enrolments = 0
        total_approved_intake = 0

        for prog in programmes:
            # Active enrolments in programme
            enr_count_q = select(func.count(EnrolmentRecord.id)).where(
                and_(
                    EnrolmentRecord.programme_id == prog.id,
                    EnrolmentRecord.enrolment_status == "ACTIVE"
                )
            )
            if academic_year_id:
                enr_count_q = enr_count_q.where(EnrolmentRecord.academic_year_id == academic_year_id)
            active_count = (await session.execute(enr_count_q)).scalar() or 0
            total_active_enrolments += active_count

            # Approved intake via ProgrammeApproval
            approval = next((a for a in prog.approvals if not academic_year_id or a.academic_year_id == academic_year_id), None)
            approved_intake = None
            if approval and approval.intake_versions:
                sorted_versions = sorted(approval.intake_versions, key=lambda v: v.version, reverse=True)
                approved_intake = sorted_versions[0].approved_intake

            if approved_intake is not None:
                total_approved_intake += approved_intake
                if active_count > approved_intake:
                    exceeded_count += 1
            else:
                if active_count > 0:
                    missing_intake_count += 1

        if exceeded_count > 0:
            factor_capacity = min(25.0, 10.0 + (exceeded_count * 7.5))
        elif missing_intake_count > 0:
            factor_capacity = min(15.0, missing_intake_count * 5.0)
        else:
            factor_capacity = 0.0

        # ---------------- Factor 2: Unresolved Cross-Institution Conflict (max 25) ----------------
        dup_query = select(func.count(Finding.id)).where(
            and_(
                or_(
                    Finding.primary_institution_id == institution_id,
                    Finding.secondary_institution_id == institution_id
                ),
                Finding.status.in_(["OPEN", "AWAITING_INSTITUTION_RESPONSE", "RESPONSE_RECEIVED", "UNDER_REVIEW"]),
                Finding.rule_code.in_(["DUP-001", "DUP-002", "DUP-003"])
            )
        )
        unresolved_conflicts_count = (await session.execute(dup_query)).scalar() or 0
        factor_conflicts = min(25.0, unresolved_conflicts_count * 12.5)

        # ---------------- Factor 3: Identifier & Data Quality Problems (max 15) ----------------
        total_enr_q = select(func.count(EnrolmentRecord.id)).where(EnrolmentRecord.institution_id == institution_id)
        if academic_year_id:
            total_enr_q = total_enr_q.where(EnrolmentRecord.academic_year_id == academic_year_id)
        total_enr_count = (await session.execute(total_enr_q)).scalar() or 0

        flagged_enr_q = (
            select(func.count(EnrolmentRecord.id))
            .outerjoin(StudentIdentity, EnrolmentRecord.student_identity_id == StudentIdentity.id)
            .where(
                and_(
                    EnrolmentRecord.institution_id == institution_id,
                    or_(
                        EnrolmentRecord.student_identity_id.is_(None),
                        StudentIdentity.apaar_validation_status == "MALFORMED"
                    )
                )
            )
        )
        if academic_year_id:
            flagged_enr_q = flagged_enr_q.where(EnrolmentRecord.academic_year_id == academic_year_id)
        flagged_enr_count = (await session.execute(flagged_enr_q)).scalar() or 0

        if total_enr_count > 0:
            quality_ratio = flagged_enr_count / total_enr_count
            factor_data_quality = min(15.0, round(quality_ratio * 30.0, 1))
        else:
            factor_data_quality = 0.0

        # ---------------- Factor 4: Unusual Roster Changes / Corrections (max 15) ----------------
        ver_q = select(func.count(EnrolmentRecordVersion.id)).join(
            EnrolmentRecord, EnrolmentRecordVersion.enrolment_record_id == EnrolmentRecord.id
        ).where(EnrolmentRecord.institution_id == institution_id)
        corrections_count = (await session.execute(ver_q)).scalar() or 0
        factor_roster_changes = min(15.0, corrections_count * 5.0)

        # ---------------- Factor 5: Source-Reconciliation Gap (max 10) ----------------
        unavail_q = (
            select(func.count(EnrolmentRecord.id))
            .join(StudentIdentity, EnrolmentRecord.student_identity_id == StudentIdentity.id)
            .where(
                and_(
                    EnrolmentRecord.institution_id == institution_id,
                    StudentIdentity.apaar_validation_status.in_(["UNAVAILABLE", "SIMULATED"])
                )
            )
        )
        unavail_count = (await session.execute(unavail_q)).scalar() or 0
        factor_source_gap = min(10.0, unavail_count * 2.0)

        # ---------------- Factor 6: Repeated Unresolved Prior Findings (max 10) ----------------
        prior_findings_q = select(func.count(Finding.id)).where(
            and_(
                Finding.primary_institution_id == institution_id,
                Finding.status == "AWAITING_INSTITUTION_RESPONSE"
            )
        )
        prior_findings_count = (await session.execute(prior_findings_q)).scalar() or 0
        factor_prior_findings = min(10.0, prior_findings_count * 5.0)

        # ---------------- Total & Completeness ----------------
        raw_total = (
            factor_capacity + 
            factor_conflicts + 
            factor_data_quality + 
            factor_roster_changes + 
            factor_source_gap + 
            factor_prior_findings
        )
        total_score = round(min(100.0, max(0.0, raw_total)), 1)
        risk_band = cls.determine_risk_band(total_score)

        if missing_intake_count > 0 and len(programmes) > 0 and total_approved_intake == 0:
            completeness_state = "PARTIAL_NO_INTAKE"
        elif unavail_count > 0:
            completeness_state = "PARTIAL_MISSING_EXTERNAL"
        else:
            completeness_state = "COMPLETE"

        # Structured input snapshot
        input_snapshot = {
            "institution_code": institution.official_institution_code,
            "programmes_count": len(programmes),
            "exceeded_programmes_count": exceeded_count,
            "missing_intake_programmes_count": missing_intake_count,
            "total_active_enrolments": total_active_enrolments,
            "total_approved_intake": total_approved_intake,
            "unresolved_conflicts_count": unresolved_conflicts_count,
            "total_enrolments_count": total_enr_count,
            "flagged_enrolments_count": flagged_enr_count,
            "corrections_count": corrections_count,
            "unverified_source_count": unavail_count,
            "awaiting_response_findings_count": prior_findings_count,
            "calculation_timestamp": now.isoformat()
        }

        # Plain-language explainable rationale
        explanation_parts = []
        if factor_capacity > 0:
            explanation_parts.append(f"Capacity discrepancy factor contributes {factor_capacity:.1f}/25 ({exceeded_count} programmes exceed approved intake).")
        if factor_conflicts > 0:
            explanation_parts.append(f"Cross-institution conflicts contribute {factor_conflicts:.1f}/25 ({unresolved_conflicts_count} active duplicate findings).")
        if factor_data_quality > 0:
            explanation_parts.append(f"Data quality problems contribute {factor_data_quality:.1f}/15 ({flagged_enr_count} records missing or malformed identifier).")
        if factor_roster_changes > 0:
            explanation_parts.append(f"Roster corrections contribute {factor_roster_changes:.1f}/15 ({corrections_count} material record version corrections).")
        if factor_source_gap > 0:
            explanation_parts.append(f"Source reconciliation gap contributes {factor_source_gap:.1f}/10 ({unavail_count} records pending external source corroboration).")
        if factor_prior_findings > 0:
            explanation_parts.append(f"Prior unresponded findings contribute {factor_prior_findings:.1f}/10 ({prior_findings_count} findings awaiting response).")
        
        if not explanation_parts:
            explanation = "Routine profile: Zero active cross-institution conflicts, approved intake verified, and clean data-quality metrics."
        else:
            explanation = " ".join(explanation_parts)

        # Deactivate previous active calculation for this institution
        await session.execute(
            update(RiskCalculation)
            .where(
                and_(
                    RiskCalculation.institution_id == institution_id,
                    RiskCalculation.is_active.is_(True)
                )
            )
            .values(is_active=False)
        )

        # Persist new risk calculation
        calc = RiskCalculation(
            institution_id=institution_id,
            academic_year_id=academic_year_id,
            total_score=total_score,
            risk_band=risk_band,
            calculation_version=cls.CALCULATION_VERSION,
            factor_capacity_discrepancy=factor_capacity,
            factor_unresolved_conflicts=factor_conflicts,
            factor_data_quality=factor_data_quality,
            factor_unusual_roster_changes=factor_roster_changes,
            factor_source_reconciliation_gap=factor_source_gap,
            factor_repeated_prior_findings=factor_prior_findings,
            input_snapshot_json=json.dumps(input_snapshot),
            explanation=explanation,
            completeness_state=completeness_state,
            calculated_at=now,
            triggered_by_user_id=triggered_by_user_id,
            is_active=True
        )
        session.add(calc)

        # Audit Event
        audit = AuditEvent(
            actor_user_id=triggered_by_user_id,
            actor_type="USER" if triggered_by_user_id else "SYSTEM",
            action="RISK_CALCULATION_RUN",
            target_type="INSTITUTION",
            target_id=institution_id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "institution_id": institution_id,
                "score": total_score,
                "band": risk_band,
                "version": cls.CALCULATION_VERSION
            })
        )
        session.add(audit)
        await session.commit()
        await session.refresh(calc)
        return calc

    @classmethod
    async def get_institution_risk_profile(
        cls,
        session: AsyncSession,
        institution_id: str
    ) -> Dict[str, Any]:
        """Returns the current risk calculation, calculation history, and summary counters."""
        inst_res = await session.execute(select(Institution).where(Institution.id == institution_id))
        institution = inst_res.scalar_one_or_none()
        if not institution:
            raise ValueError(f"Institution with ID '{institution_id}' not found.")

        # Latest active calculation (or run fresh if none)
        calc_res = await session.execute(
            select(RiskCalculation)
            .where(
                and_(
                    RiskCalculation.institution_id == institution_id,
                    RiskCalculation.is_active.is_(True)
                )
            )
            .order_by(RiskCalculation.calculated_at.desc())
            .limit(1)
        )
        current_calc = calc_res.scalar_one_or_none()
        if not current_calc:
            current_calc = await cls.calculate_institution_risk(session, institution_id)

        # History of calculations (up to 10)
        hist_res = await session.execute(
            select(RiskCalculation)
            .where(RiskCalculation.institution_id == institution_id)
            .order_by(RiskCalculation.calculated_at.desc())
            .limit(10)
        )
        history = hist_res.scalars().all()

        # Unresolved findings count
        find_q = select(func.count(Finding.id)).where(
            and_(
                or_(
                    Finding.primary_institution_id == institution_id,
                    Finding.secondary_institution_id == institution_id
                ),
                Finding.status.in_(["OPEN", "AWAITING_INSTITUTION_RESPONSE", "RESPONSE_RECEIVED", "UNDER_REVIEW"])
            )
        )
        unresolved_findings = (await session.execute(find_q)).scalar() or 0

        # Import AuditCase dynamically to avoid circular dependencies
        from app.models.oversight import AuditCase
        cases_q = select(func.count(AuditCase.id)).where(
            and_(
                AuditCase.institution_id == institution_id,
                AuditCase.status.in_(["OPEN", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RESPONSE_RECEIVED"])
            )
        )
        active_cases = (await session.execute(cases_q)).scalar() or 0

        return {
            "institution_id": institution.id,
            "institution_name": institution.name,
            "official_code": institution.official_institution_code,
            "current_calculation": current_calc,
            "history": history,
            "unresolved_findings_count": unresolved_findings,
            "active_cases_count": active_cases,
            "programmes_exceeding_capacity_count": json.loads(current_calc.input_snapshot_json).get("exceeded_programmes_count", 0)
        }

    @classmethod
    async def get_risk_queue(
        cls,
        session: AsyncSession,
        risk_band: Optional[str] = None,
        search: Optional[str] = None,
        allowed_institution_ids: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves the prioritized institutional review queue.
        Calculates risk for institutions if missing.
        """
        from app.models.oversight import AuditCase

        # 1. Base query for institutions
        inst_query = select(Institution)
        if allowed_institution_ids is not None:
            inst_query = inst_query.where(Institution.id.in_(allowed_institution_ids))
        if search:
            inst_query = inst_query.where(
                or_(
                    Institution.name.ilike(f"%{search}%"),
                    Institution.official_institution_code.ilike(f"%{search}%")
                )
            )

        institutions = (await session.execute(inst_query)).scalars().all()
        queue_items = []

        for inst in institutions:
            calc_res = await session.execute(
                select(RiskCalculation)
                .where(
                    and_(
                        RiskCalculation.institution_id == inst.id,
                        RiskCalculation.is_active.is_(True)
                    )
                )
                .order_by(RiskCalculation.calculated_at.desc())
                .limit(1)
            )
            calc = calc_res.scalar_one_or_none()
            if not calc:
                calc = await cls.calculate_institution_risk(session, inst.id)

            if risk_band and calc.risk_band != risk_band:
                continue

            # Unresolved findings
            find_q = select(func.count(Finding.id)).where(
                and_(
                    or_(
                        Finding.primary_institution_id == inst.id,
                        Finding.secondary_institution_id == inst.id
                    ),
                    Finding.status.in_(["OPEN", "AWAITING_INSTITUTION_RESPONSE", "RESPONSE_RECEIVED", "UNDER_REVIEW"])
                )
            )
            unresolved_count = (await session.execute(find_q)).scalar() or 0

            # Open cases
            case_q = select(func.count(AuditCase.id)).where(
                and_(
                    AuditCase.institution_id == inst.id,
                    AuditCase.status.in_(["OPEN", "ASSIGNED", "UNDER_REVIEW", "CLARIFICATION_REQUESTED", "RESPONSE_RECEIVED"])
                )
            )
            open_cases = (await session.execute(case_q)).scalar() or 0

            queue_items.append({
                "institution_id": inst.id,
                "institution_name": inst.name,
                "official_code": inst.official_institution_code,
                "state": inst.state_code,
                "total_score": calc.total_score,
                "risk_band": calc.risk_band,
                "unresolved_findings_count": unresolved_count,
                "open_cases_count": open_cases,
                "last_calculated_at": calc.calculated_at,
                "completeness_state": calc.completeness_state
            })

        # Sort queue by priority: PRIORITY_REVIEW > REVIEW_RECOMMENDED > WATCH > ROUTINE, then total_score desc
        band_weight = {
            "PRIORITY_REVIEW": 4,
            "REVIEW_RECOMMENDED": 3,
            "WATCH": 2,
            "ROUTINE": 1
        }
        queue_items.sort(key=lambda x: (band_weight.get(x["risk_band"], 0), x["total_score"]), reverse=True)

        total = len(queue_items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = queue_items[start:end]

        return paginated_items, total
