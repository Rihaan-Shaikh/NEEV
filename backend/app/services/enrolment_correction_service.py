import json
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.student import EnrolmentRecord, EnrolmentRecordVersion, StudentIdentity
from app.models.user import User
from app.models.audit import AuditEvent
from app.models.integrity import Finding, Notification
from app.services.conflict_service import ConflictDetectionService

class EnrolmentCorrectionService:
    @staticmethod
    async def apply_correction(
        session: AsyncSession,
        record_id: str,
        expected_version: int,
        correction_reason: str,
        updates: Dict[str, Any],
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str]
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        is_national_admin = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in user_roles)

        # 1. HIS-001: Mandatory correction reason check
        if not correction_reason or len(correction_reason.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="HIS-001: Material record change requires a documented correction reason of at least 10 characters."
            )

        # 2. Fetch record
        query = (
            select(EnrolmentRecord)
            .where(EnrolmentRecord.id == record_id)
            .options(
                selectinload(EnrolmentRecord.student_identity),
                selectinload(EnrolmentRecord.institution),
                selectinload(EnrolmentRecord.programme),
                selectinload(EnrolmentRecord.academic_year)
            )
        )
        res = await session.execute(query)
        record = res.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrolment record with ID '{record_id}' not found."
            )

        # 3. Tenant authorization check
        if not is_national_admin:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if user_inst_id != record.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not authorized to correct enrolment records of another institution."
                )

        # 4. HIS-002: Optimistic concurrency control
        if record.current_record_version != expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"HIS-002: Record version mismatch. Expected version {expected_version}, "
                    f"but record is currently at version {record.current_record_version}. "
                    f"Please refresh the record before applying corrections."
                )
            )

        # 5. Capture snapshot of existing version
        snapshot = {
            "version": record.current_record_version,
            "institution_student_id": record.institution_student_id,
            "student_full_name": record.student_full_name,
            "admission_date": record.admission_date.isoformat(),
            "enrolment_status": record.enrolment_status,
            "admission_category": record.admission_category,
            "supernumerary_category": record.supernumerary_category,
            "programme_id": record.programme_id,
            "academic_year_id": record.academic_year_id,
            "captured_at": now.isoformat()
        }

        old_version_entry = EnrolmentRecordVersion(
            enrolment_record_id=record.id,
            version_number=record.current_record_version,
            snapshot_json=json.dumps(snapshot),
            change_reason=correction_reason,
            changed_by=current_user.email_normalized,
            changed_at=now
        )
        session.add(old_version_entry)

        # 6. Apply validated updates
        allowed_fields = ["admission_date", "enrolment_status", "admission_category", "supernumerary_category"]
        applied_changes = {}

        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                if field == "admission_date" and isinstance(value, str):
                    try:
                        parsed_date = date.fromisoformat(value)
                        setattr(record, field, parsed_date)
                        applied_changes[field] = value
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Invalid admission date format. Use YYYY-MM-DD."
                        )
                elif field == "enrolment_status":
                    valid_statuses = ("ACTIVE", "TRANSFERRED", "WITHDRAWN", "COMPLETED", "SUSPENDED")
                    if value.upper() not in valid_statuses:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Invalid enrolment status '{value}'. Allowed: {valid_statuses}."
                        )
                    setattr(record, field, value.upper())
                    applied_changes[field] = value.upper()
                else:
                    setattr(record, field, value)
                    applied_changes[field] = value

        # Increment version number
        record.current_record_version += 1
        record.updated_at = now

        # 7. Record audit event
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="ENROLMENT_RECORD_CORRECTION",
            target_type="ENROLMENT",
            target_id=record.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "from_version": expected_version,
                "to_version": record.current_record_version,
                "reason": correction_reason,
                "changes": applied_changes
            })
        )
        session.add(audit)

        # 8. Re-evaluate conflict findings for this student
        revalidation_findings = []
        if record.student_identity_id:
            # Check if this student had an open DUP-002 finding and status became TRANSFERRED or WITHDRAWN
            findings_query = select(Finding).where(
                and_(
                    or_(
                        Finding.primary_enrolment_id == record.id,
                        Finding.secondary_enrolment_id == record.id
                    ),
                    Finding.status.in_(("OPEN", "AWAITING_INSTITUTION_RESPONSE", "RESPONSE_RECEIVED", "UNDER_REVIEW"))
                )
            )
            f_res = await session.execute(findings_query)
            active_findings = f_res.scalars().all()

            for f in active_findings:
                if f.rule_code == "DUP-002" and record.enrolment_status in ("TRANSFERRED", "WITHDRAWN"):
                    # Legitimate transfer resolved
                    f.rule_code = "DUP-004"
                    f.severity = "INFO"
                    f.status = "RESOLVED"
                    f.resolution_rationale = f"Discrepancy resolved by documented correction: Student enrolment marked as {record.enrolment_status}."
                    f.resolved_by_user_id = current_user.id
                    f.resolved_at = now
                    f.last_detected_at = now
                    revalidation_findings.append(f"Finding {f.id} automatically resolved as DUP-004 transfer.")

        await session.commit()

        return {
            "success": True,
            "enrolment_id": record.id,
            "new_version": record.current_record_version,
            "message": f"Enrolment record successfully corrected to version {record.current_record_version}.",
            "revalidation_findings": revalidation_findings
        }
