import csv
import io
import hashlib
import json
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models.submission import SubmissionBatch, SubmissionRow, SubmissionReceipt
from app.models.programme import Programme, AcademicYear
from app.models.institution import Institution
from app.models.student import StudentIdentity, EnrolmentRecord, EnrolmentRecordVersion
from app.models.validation import ValidationRun, ValidationFinding
from app.models.user import User
from app.rules.validation_engine import DeterministicValidationEngine
from app.core.security import generate_apaar_fingerprint, mask_apaar_id
from app.services.audit_service import log_audit_event
from app.policies.authorization import enforce_institution_scope

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

async def create_submission_batch(
    db: AsyncSession,
    user: User,
    institution_id: str,
    academic_year_id: str,
    programme_id: Optional[str] = None,
    submission_type: str = "REGULAR_ENROLMENT"
) -> SubmissionBatch:
    # 1. Enforce scope
    enforce_institution_scope(user, institution_id)

    # 2. Verify institution exists
    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # 3. Verify academic year exists
    ay = await db.get(AcademicYear, academic_year_id)
    if not ay:
        raise HTTPException(status_code=404, detail="Academic year not found")

    # 4. Verify programme if provided
    if programme_id:
        prog = await db.get(Programme, programme_id)
        if not prog or prog.institution_id != institution_id:
            raise HTTPException(status_code=400, detail="Invalid programme for selected institution")

    batch = SubmissionBatch(
        institution_id=institution_id,
        academic_year_id=academic_year_id,
        programme_id=programme_id,
        submission_type=submission_type,
        source_type="CSV_UPLOAD",
        submitted_by_user_id=user.id,
        processing_status="CREATED",
        ruleset_version=DeterministicValidationEngine.RULESET_VERSION,
    )
    db.add(batch)
    await db.flush()

    await log_audit_event(
        db,
        action="BATCH_CREATED",
        target_type="SUBMISSION_BATCH",
        target_id=batch.id,
        actor_user_id=user.id,
        actor_email=user.email_normalized,
        metadata={"institution_id": institution_id, "academic_year_id": academic_year_id}
    )

    return batch

async def process_batch_csv(
    db: AsyncSession,
    user: User,
    batch_id: str,
    file_bytes: bytes,
    filename: str
) -> Tuple[SubmissionBatch, int, int, int]:
    # 1. Retrieve batch with relationships
    result = await db.execute(
        select(SubmissionBatch)
        .options(selectinload(SubmissionBatch.institution), selectinload(SubmissionBatch.academic_year))
        .where(SubmissionBatch.id == batch_id)
    )
    batch = result.scalars().first()
    if not batch:
        raise HTTPException(status_code=404, detail="Submission batch not found")

    enforce_institution_scope(user, batch.institution_id)

    if batch.processing_status == "FINALIZED":
        raise HTTPException(status_code=400, detail="Batch has already been finalized and cannot be modified")

    # 2. Checksum calculation
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # 3. Decode CSV
    try:
        content_str = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            content_str = file_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode file. Please upload a valid UTF-8 CSV.")

    # 4. Parse CSV
    reader = csv.DictReader(io.StringIO(content_str))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty or missing headers")

    # Fetch valid programmes for this institution
    progs_res = await db.execute(select(Programme).where(Programme.institution_id == batch.institution_id))
    valid_programmes = {p.official_programme_code: p.id for p in progs_res.scalars().all()}
    
    selected_prog_code = None
    if batch.programme_id:
        p_res = await db.get(Programme, batch.programme_id)
        if p_res:
            selected_prog_code = p_res.official_programme_code

    # Delete any previous rows/findings for this batch on re-upload
    await db.execute(delete(SubmissionRow).where(SubmissionRow.batch_id == batch_id))
    await db.execute(delete(ValidationFinding).where(ValidationFinding.batch_id == batch_id))
    await db.execute(delete(ValidationRun).where(ValidationRun.batch_id == batch_id))

    # Initialize ValidationRun
    val_run = ValidationRun(
        batch_id=batch.id,
        institution_id=batch.institution_id,
        programme_id=batch.programme_id,
        academic_year_id=batch.academic_year_id,
        ruleset_version=DeterministicValidationEngine.RULESET_VERSION,
        status="RUNNING"
    )
    db.add(val_run)
    await db.flush()

    seen_student_ids = set()
    total_rows = 0
    valid_count = 0
    error_count = 0
    warning_count = 0

    rule_summary_counts: Dict[str, int] = {}

    for row_idx, raw_dict in enumerate(reader, start=1):
        total_rows += 1
        clean_dict = {str(k).strip(): v for k, v in raw_dict.items() if k is not None}
        
        row_res = DeterministicValidationEngine.validate_row(
            row_number=row_idx,
            raw_row=clean_dict,
            seen_student_ids=seen_student_ids,
            valid_programme_codes=set(valid_programmes.keys()),
            selected_programme_code=selected_prog_code
        )

        row_status = "VALID"
        if row_res.errors:
            row_status = "ERROR"
            error_count += 1
        elif row_res.warnings:
            row_status = "WARNING"
            warning_count += 1
            valid_count += 1
        else:
            valid_count += 1

        errors_payload = [e.to_dict() for e in row_res.errors]
        warnings_payload = [w.to_dict() for w in row_res.warnings]

        # Record findings
        for finding in row_res.errors + row_res.warnings:
            rule_summary_counts[finding.rule_code] = rule_summary_counts.get(finding.rule_code, 0) + 1
            db_finding = ValidationFinding(
                rule_code=finding.rule_code,
                validation_run_id=val_run.id,
                batch_id=batch.id,
                row_number=row_idx,
                field_name=finding.field_name,
                severity=finding.severity,
                explanation=finding.explanation,
                raw_value=finding.raw_value,
                status="OPEN"
            )
            db.add(db_finding)

        sub_row = SubmissionRow(
            batch_id=batch.id,
            row_number=row_idx,
            processing_status=row_status,
            raw_data_json=json.dumps(clean_dict),
            normalized_data_json=json.dumps(row_res.normalized_data),
            errors_json=json.dumps(errors_payload),
            warnings_json=json.dumps(warnings_payload),
        )
        db.add(sub_row)

    # Complete validation run
    val_run.completed_at = utc_now()
    val_run.status = "COMPLETED"
    val_run.summary_json = json.dumps(rule_summary_counts)

    # Update batch metadata
    batch.source_filename = filename
    batch.source_checksum = sha256_hash
    batch.row_count = total_rows
    batch.valid_count = valid_count
    batch.rejected_count = error_count
    batch.flagged_count = warning_count
    batch.processing_status = "VALIDATED"

    await db.flush()

    await log_audit_event(
        db,
        action="BATCH_VALIDATED",
        target_type="SUBMISSION_BATCH",
        target_id=batch.id,
        actor_user_id=user.id,
        actor_email=user.email_normalized,
        metadata={
            "filename": filename,
            "total_rows": total_rows,
            "valid_count": valid_count,
            "error_count": error_count,
            "warning_count": warning_count
        }
    )

    return batch, total_rows, valid_count, error_count

async def get_batch_preview(db: AsyncSession, user: User, batch_id: str) -> Dict[str, Any]:
    result = await db.execute(
        select(SubmissionBatch)
        .options(
            selectinload(SubmissionBatch.institution),
            selectinload(SubmissionBatch.academic_year),
            selectinload(SubmissionBatch.programme)
        )
        .where(SubmissionBatch.id == batch_id)
    )
    batch = result.scalars().first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    enforce_institution_scope(user, batch.institution_id)

    # Get rows (limit to bounded set for preview performance, e.g. first 500)
    rows_res = await db.execute(
        select(SubmissionRow)
        .where(SubmissionRow.batch_id == batch_id)
        .order_by(SubmissionRow.row_number.asc())
        .limit(500)
    )
    rows = rows_res.scalars().all()

    # Get summary from validation run
    val_run_res = await db.execute(
        select(ValidationRun).where(ValidationRun.batch_id == batch_id).order_by(ValidationRun.started_at.desc())
    )
    val_run = val_run_res.scalars().first()
    val_summary = json.loads(val_run.summary_json) if (val_run and val_run.summary_json) else {}

    row_items = []
    for r in rows:
        row_items.append({
            "row_number": r.row_number,
            "processing_status": r.processing_status,
            "raw_data": json.loads(r.raw_data_json),
            "normalized_data": json.loads(r.normalized_data_json) if r.normalized_data_json else None,
            "errors": json.loads(r.errors_json) if r.errors_json else [],
            "warnings": json.loads(r.warnings_json) if r.warnings_json else [],
        })

    return {
        "batch": {
            "id": batch.id,
            "institution_id": batch.institution_id,
            "institution_name": batch.institution.name if batch.institution else None,
            "academic_year_id": batch.academic_year_id,
            "academic_year_label": batch.academic_year.label if batch.academic_year else None,
            "programme_id": batch.programme_id,
            "programme_name": batch.programme.programme_name if batch.programme else None,
            "submission_type": batch.submission_type,
            "source_type": batch.source_type,
            "processing_status": batch.processing_status,
            "source_filename": batch.source_filename,
            "row_count": batch.row_count,
            "valid_count": batch.valid_count,
            "accepted_count": batch.accepted_count,
            "rejected_count": batch.rejected_count,
            "flagged_count": batch.flagged_count,
            "ruleset_version": batch.ruleset_version,
            "receipt_reference": batch.receipt_reference,
            "created_at": batch.created_at
        },
        "total_rows": batch.row_count,
        "valid_rows": batch.valid_count,
        "error_rows": batch.rejected_count,
        "warning_rows": batch.flagged_count,
        "rows": row_items,
        "validation_summary": val_summary
    }

async def finalize_submission_batch(db: AsyncSession, user: User, batch_id: str) -> Dict[str, Any]:
    # 1. Scope and state check
    result = await db.execute(
        select(SubmissionBatch)
        .options(
            selectinload(SubmissionBatch.institution),
            selectinload(SubmissionBatch.academic_year),
            selectinload(SubmissionBatch.programme)
        )
        .where(SubmissionBatch.id == batch_id)
    )
    batch = result.scalars().first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    enforce_institution_scope(user, batch.institution_id)

    # Idempotency check: if already finalized, return existing receipt
    if batch.processing_status == "FINALIZED" and batch.receipt_reference:
        receipt_res = await db.execute(
            select(SubmissionReceipt).where(SubmissionReceipt.batch_id == batch_id)
        )
        receipt = receipt_res.scalars().first()
        return {
            "batch_id": batch.id,
            "receipt_reference": batch.receipt_reference,
            "status": "FINALIZED",
            "accepted_count": batch.accepted_count,
            "rejected_count": batch.rejected_count,
            "issued_at": receipt.issued_at if receipt else batch.created_at,
            "message": "Batch was already finalized (idempotent result)."
        }

    if batch.processing_status != "VALIDATED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot finalize batch with status '{batch.processing_status}'. Batch must be VALIDATED first."
        )

    # 2. Fetch rows
    rows_res = await db.execute(
        select(SubmissionRow)
        .where(SubmissionRow.batch_id == batch_id)
        .order_by(SubmissionRow.row_number.asc())
    )
    rows = rows_res.scalars().all()

    # Preload programmes for this institution
    progs_res = await db.execute(select(Programme).where(Programme.institution_id == batch.institution_id))
    prog_map = {p.official_programme_code: p.id for p in progs_res.scalars().all()}

    accepted_count = 0
    rejected_count = 0

    for r in rows:
        if r.processing_status in ["VALID", "WARNING"]:
            norm = json.loads(r.normalized_data_json) if r.normalized_data_json else {}
            apaar_id = norm.get("apaar_id")
            
            # Create StudentIdentity
            apaar_fp = generate_apaar_fingerprint(apaar_id) if apaar_id else None
            identity = StudentIdentity(
                apaar_id_ciphertext=apaar_id,
                apaar_id_fingerprint=apaar_fp,
                apaar_validation_status=norm.get("apaar_validation_status", "UNAVAILABLE"),
                apaar_validation_source="SIMULATED_INTEGRATION_ADAPTER" if apaar_id else "NONE",
                apaar_validation_checked_at=utc_now() if apaar_id else None,
                masked_apaar_id=mask_apaar_id(apaar_id)
            )
            db.add(identity)
            await db.flush()

            # Determine programme
            p_code = norm.get("programme_code")
            p_id = prog_map.get(p_code) or batch.programme_id
            if not p_id:
                p_id = list(prog_map.values())[0] if prog_map else None

            # Create EnrolmentRecord
            enrolment = EnrolmentRecord(
                student_identity_id=identity.id,
                institution_id=batch.institution_id,
                programme_id=p_id,
                academic_year_id=batch.academic_year_id,
                institution_student_id=norm.get("institution_student_id"),
                student_full_name=norm.get("student_full_name"),
                admission_date=datetime.fromisoformat(norm.get("admission_date")).date(),
                enrolment_status=norm.get("enrolment_status", "ACTIVE"),
                admission_category=norm.get("admission_category", "OPEN"),
                supernumerary_category=norm.get("supernumerary_category"),
                source_submission_batch_id=batch.id,
                current_record_version=1
            )
            db.add(enrolment)
            await db.flush()

            # Create initial version snapshot
            version = EnrolmentRecordVersion(
                enrolment_record_id=enrolment.id,
                version_number=1,
                snapshot_json=json.dumps(norm),
                change_reason="INITIAL_BATCH_INGESTION",
                changed_by=user.email_normalized
            )
            db.add(version)

            r.processing_status = "ACCEPTED"
            r.linked_enrolment_record_id = enrolment.id
            accepted_count += 1
        else:
            r.processing_status = "REJECTED"
            rejected_count += 1

    # 3. Generate receipt
    receipt_ref = f"NEEV-RCPT-{batch.academic_year.label[:4] if batch.academic_year else '2026'}-{uuid.uuid4().hex[:8].upper()}"
    now = utc_now()

    summary_snapshot = {
        "batch_id": batch.id,
        "receipt_reference": receipt_ref,
        "institution_id": batch.institution_id,
        "institution_name": batch.institution.name if batch.institution else "Unknown",
        "academic_year": batch.academic_year.label if batch.academic_year else "Unknown",
        "total_rows": batch.row_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "finalized_by": user.email_normalized,
        "issued_at": now.isoformat(),
        "ruleset_version": batch.ruleset_version,
    }

    receipt = SubmissionReceipt(
        batch_id=batch.id,
        receipt_reference=receipt_ref,
        issued_at=now,
        receipt_status="ISSUED",
        summary_snapshot_json=json.dumps(summary_snapshot)
    )
    db.add(receipt)

    # 4. Update batch
    batch.processing_status = "FINALIZED"
    batch.accepted_count = accepted_count
    batch.rejected_count = rejected_count
    batch.receipt_reference = receipt_ref

    await db.flush()

    await log_audit_event(
        db,
        action="BATCH_FINALIZED",
        target_type="SUBMISSION_BATCH",
        target_id=batch.id,
        actor_user_id=user.id,
        actor_email=user.email_normalized,
        metadata={
            "receipt_reference": receipt_ref,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count
        }
    )

    return {
        "batch_id": batch.id,
        "receipt_reference": receipt_ref,
        "status": "FINALIZED",
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "issued_at": now,
        "message": f"Successfully finalized batch. {accepted_count} canonical enrolments recorded, {rejected_count} rejected rows quarantined."
    }
