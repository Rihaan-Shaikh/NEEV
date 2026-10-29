import json
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.student import EnrolmentRecord, StudentIdentity
from app.models.institution import Institution
from app.models.programme import AcademicYear, Programme
from app.models.integrity import Finding, Notification
from app.models.audit import AuditEvent

logger = logging.getLogger("neev.conflict_service")

class ConflictDetectionService:
    @staticmethod
    async def run_integrity_reconciliation(
        session: AsyncSession, 
        current_user_id: str = "SYSTEM",
        institution_id: str = None
    ) -> Dict[str, Any]:
        """
        Runs deterministic cross-institution and status-aware conflict detection.
        Idempotent: Never creates duplicate open findings for the same underlying conflict.
        """
        now = datetime.now(timezone.utc)
        
        # 1. Fetch enrolments with valid student identities and APAAR fingerprints
        query = (
            select(EnrolmentRecord)
            .join(StudentIdentity, EnrolmentRecord.student_identity_id == StudentIdentity.id)
            .where(StudentIdentity.apaar_id_fingerprint.isnot(None))
            .options(
                selectinload(EnrolmentRecord.student_identity),
                selectinload(EnrolmentRecord.institution),
                selectinload(EnrolmentRecord.programme),
                selectinload(EnrolmentRecord.academic_year)
            )
        )
        if institution_id:
            query = query.where(EnrolmentRecord.institution_id == institution_id)

        result = await session.execute(query)
        enrolments = result.scalars().all()
        
        # Group enrolments by APAAR fingerprint
        fingerprint_map: Dict[str, List[EnrolmentRecord]] = {}
        for enr in enrolments:
            fp = enr.student_identity.apaar_id_fingerprint
            if fp:
                fingerprint_map.setdefault(fp, []).append(enr)

        conflicts_detected = 0
        new_findings_created = 0
        existing_findings_updated = 0

        # 2. Evaluate pairs with matching fingerprints
        for fp, records in fingerprint_map.items():
            if len(records) < 2:
                continue

            # Compare all pairs (order-independent)
            for i in range(len(records)):
                for j in range(i + 1, len(records)):
                    rec_a = records[i]
                    rec_b = records[j]

                    # Standardize ordering so rec_a has smaller ID
                    if rec_a.id > rec_b.id:
                        rec_a, rec_b = rec_b, rec_a

                    is_same_institution = rec_a.institution_id == rec_b.institution_id
                    same_academic_year = rec_a.academic_year_id == rec_b.academic_year_id
                    both_active = (rec_a.enrolment_status == "ACTIVE" and rec_b.enrolment_status == "ACTIVE")
                    one_transferred = ("TRANSFERRED" in (rec_a.enrolment_status, rec_b.enrolment_status) or
                                       "WITHDRAWN" in (rec_a.enrolment_status, rec_b.enrolment_status))

                    # Rule evaluation logic:
                    if is_same_institution and both_active and same_academic_year:
                        rule_code = "DUP-001"
                        category = "DUPLICATE"
                        severity = "ERROR"
                        explanation = (
                            f"Intra-institution duplicate active enrolment: Student '{rec_a.student_full_name}' "
                            f"is enrolled in multiple active programmes ({rec_a.programme.official_programme_code} and {rec_b.programme.official_programme_code}) "
                            f"at {rec_a.institution.name} during the same academic year."
                        )
                    elif not is_same_institution and both_active and same_academic_year:
                        rule_code = "DUP-002"
                        category = "DUPLICATE"
                        severity = "CRITICAL"
                        explanation = (
                            f"Cross-institution dual active enrolment: The same APAAR identity is currently reported as ACTIVE "
                            f"at both {rec_a.institution.name} ({rec_a.institution_student_id}) and "
                            f"{rec_b.institution.name} ({rec_b.institution_student_id}) in academic year {rec_a.academic_year.label}."
                        )
                    elif not is_same_institution and one_transferred:
                        rule_code = "DUP-004"
                        category = "DUPLICATE"
                        severity = "INFO"
                        transferred_from = rec_a.institution.name if rec_a.enrolment_status in ("TRANSFERRED", "WITHDRAWN") else rec_b.institution.name
                        enrolled_at = rec_b.institution.name if rec_a.enrolment_status in ("TRANSFERRED", "WITHDRAWN") else rec_a.institution.name
                        explanation = (
                            f"Documented student transfer: Student transferred from {transferred_from} to {enrolled_at}. "
                            f"Historical record is preserved without conflict."
                        )
                    elif not is_same_institution and not same_academic_year:
                        rule_code = "DUP-004"
                        category = "DUPLICATE"
                        severity = "INFO"
                        explanation = (
                            f"Non-overlapping historical records: Same APAAR identity appears across different academic years "
                            f"({rec_a.academic_year.label} at {rec_a.institution.name} and {rec_b.academic_year.label} at {rec_b.institution.name})."
                        )
                    else:
                        rule_code = "DUP-003"
                        category = "DUPLICATE"
                        severity = "WARNING"
                        explanation = (
                            f"Potential duplicate requiring administrative review: Identity match between "
                            f"{rec_a.institution.name} (status: {rec_a.enrolment_status}) and "
                            f"{rec_b.institution.name} (status: {rec_b.enrolment_status})."
                        )

                    conflicts_detected += 1

                    # Check for existing finding with this rule and pair
                    existing_finding_res = await session.execute(
                        select(Finding).where(
                            and_(
                                Finding.rule_code == rule_code,
                                Finding.primary_enrolment_id == rec_a.id,
                                Finding.secondary_enrolment_id == rec_b.id
                            )
                        )
                    )
                    existing_finding = existing_finding_res.scalar_one_or_none()

                    structured_evidence = json.dumps({
                        "apaar_masked": rec_a.student_identity.masked_apaar_id or "APAAR-***-####",
                        "primary": {
                            "institution_id": rec_a.institution_id,
                            "institution_name": rec_a.institution.name,
                            "student_id": rec_a.institution_student_id,
                            "programme": rec_a.programme.official_programme_code,
                            "status": rec_a.enrolment_status,
                            "academic_year": rec_a.academic_year.label,
                            "admission_date": rec_a.admission_date.isoformat()
                        },
                        "secondary": {
                            "institution_id": rec_b.institution_id,
                            "institution_name": rec_b.institution.name,
                            "student_id": rec_b.institution_student_id,
                            "programme": rec_b.programme.official_programme_code,
                            "status": rec_b.enrolment_status,
                            "academic_year": rec_b.academic_year.label,
                            "admission_date": rec_b.admission_date.isoformat()
                        }
                    })


                    if existing_finding:
                        existing_finding.last_detected_at = now
                        existing_finding.explanation = explanation
                        existing_finding.structured_evidence_json = structured_evidence
                        existing_findings_updated += 1
                    else:
                        initial_status = "RESOLVED" if rule_code == "DUP-004" else "OPEN"
                        new_finding = Finding(
                            rule_code=rule_code,
                            rule_version="1.0.0",
                            category=category,
                            severity=severity,
                            status=initial_status,
                            explanation=explanation,
                            structured_evidence_json=structured_evidence,
                            primary_institution_id=rec_a.institution_id,
                            secondary_institution_id=rec_b.institution_id,
                            programme_id=rec_a.programme_id,
                            academic_year_id=rec_a.academic_year_id,
                            primary_enrolment_id=rec_a.id,
                            secondary_enrolment_id=rec_b.id,
                            first_detected_at=now,
                            last_detected_at=now
                        )
                        session.add(new_finding)
                        await session.flush()
                        new_findings_created += 1

                        # Generate notifications for institutions if severity is WARNING, ERROR, or CRITICAL
                        if severity in ("WARNING", "ERROR", "CRITICAL"):
                            notif_a = Notification(
                                target_institution_id=rec_a.institution_id,
                                role_target="INSTITUTION_ADMIN",
                                title=f"Discrepancy Detected ({rule_code})",
                                message=f"A {severity.lower()} discrepancy requires your response: {explanation}",
                                event_type="FINDING_CREATED",
                                related_resource_type="FINDING",
                                related_resource_id=new_finding.id,
                                is_read=False,
                                created_at=now
                            )
                            session.add(notif_a)

                            if rec_b.institution_id != rec_a.institution_id:
                                notif_b = Notification(
                                    target_institution_id=rec_b.institution_id,
                                    role_target="INSTITUTION_ADMIN",
                                    title=f"Discrepancy Detected ({rule_code})",
                                    message=f"A {severity.lower()} discrepancy requires your response: {explanation}",
                                    event_type="FINDING_CREATED",
                                    related_resource_type="FINDING",
                                    related_resource_id=new_finding.id,
                                    is_read=False,
                                    created_at=now
                                )
                                session.add(notif_b)

        # Audit the reconciliation job
        audit_event = AuditEvent(
            actor_user_id=current_user_id,
            actor_type="USER" if current_user_id != "SYSTEM" else "SYSTEM",
            action="INTEGRITY_RECONCILIATION_RUN",
            target_type="INTEGRITY_LEDGER",
            target_id=None,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "enrolments_inspected": len(enrolments),
                "conflicts_detected": conflicts_detected,
                "new_findings_created": new_findings_created,
                "existing_findings_updated": existing_findings_updated
            })
        )
        session.add(audit_event)
        await session.commit()

        return {
            "status": "COMPLETED",
            "timestamp": now,
            "enrolments_inspected": len(enrolments),
            "conflicts_detected": conflicts_detected,
            "new_findings_created": new_findings_created,
            "existing_findings_updated": existing_findings_updated,
            "message": f"Integrity reconciliation completed: {conflicts_detected} conflicts evaluated ({new_findings_created} new findings, {existing_findings_updated} updated)."
        }
