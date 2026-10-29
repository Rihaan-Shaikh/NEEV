import os
import hashlib
import uuid
import re
import json
from datetime import datetime, timezone
from typing import Optional, List, Any, Tuple
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.integrity import EvidenceMetadata, Finding
from app.models.user import User
from app.models.audit import AuditEvent

# Private storage location outside public static folders
STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage", "evidence"))
os.makedirs(STORAGE_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_MEDIA_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}

def sanitize_filename(filename: str) -> str:
    # Strip paths, null bytes, and non-printable characters
    cleaned = os.path.basename(filename)
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', cleaned)
    return cleaned[:100]

class EvidenceService:
    @staticmethod
    async def upload_evidence(
        session: AsyncSession,
        file: UploadFile,
        evidence_category: str,
        source_provenance: str,
        finding_id: Optional[str],
        enrolment_record_id: Optional[str],
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str]
    ) -> EvidenceMetadata:
        now = datetime.now(timezone.utc)
        is_national_admin = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in user_roles)

        # 1. Validate MIME type
        content_type = file.content_type or "application/octet-stream"
        if content_type.lower() not in ALLOWED_MEDIA_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type '{content_type}'. Allowed types: {list(ALLOWED_MEDIA_TYPES.keys())}."
            )

        # 2. Read and enforce size limit
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of 10 MB ({len(file_bytes)} bytes uploaded)."
            )
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded. Please upload a valid document."
            )

        # 3. Determine institution ownership and check finding authorization
        if finding_id:
            f_res = await session.execute(select(Finding).where(Finding.id == finding_id))
            finding = f_res.scalar_one_or_none()
            if not finding:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Finding with ID '{finding_id}' not found."
                )
            if not is_national_admin:
                user_inst_id = user_scopes[0].institution_id if user_scopes else None
                if user_inst_id not in (finding.primary_institution_id, finding.secondary_institution_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: You cannot attach evidence to another institution's finding."
                    )
                institution_id = user_inst_id
            else:
                institution_id = finding.primary_institution_id
        else:
            institution_id = user_scopes[0].institution_id if user_scopes else None
            if not institution_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Institution context required for evidence attachment."
                )

        # 4. Compute SHA-256 and generate safe private filename
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        sanitized_name = sanitize_filename(file.filename or "evidence_document.pdf")
        storage_filename = f"{uuid.uuid4().hex}_{sha256[:16]}.bin"
        absolute_storage_path = os.path.join(STORAGE_DIR, storage_filename)

        with open(absolute_storage_path, "wb") as f_out:
            f_out.write(file_bytes)

        # 5. Persist metadata
        evidence = EvidenceMetadata(
            finding_id=finding_id,
            enrolment_record_id=enrolment_record_id,
            original_filename=sanitized_name,
            media_type=content_type,
            file_size_bytes=len(file_bytes),
            sha256_checksum=sha256,
            storage_path=absolute_storage_path,
            uploader_user_id=current_user.id,
            institution_id=institution_id,
            evidence_category=evidence_category,
            source_provenance=source_provenance,
            scanning_status="CLEARED_LOCAL",
            uploaded_at=now
        )
        session.add(evidence)

        # 6. Audit event
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="EVIDENCE_UPLOAD",
            target_type="EVIDENCE",
            target_id=evidence.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "original_filename": sanitized_name,
                "file_size": len(file_bytes),
                "sha256": sha256,
                "finding_id": finding_id,
                "institution_id": institution_id
            })
        )
        session.add(audit)
        await session.commit()
        return evidence

    @staticmethod
    async def get_evidence_file_response(
        session: AsyncSession,
        evidence_id: str,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str]
    ) -> FileResponse:
        now = datetime.now(timezone.utc)
        is_national_admin = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in user_roles)

        query = select(EvidenceMetadata).where(EvidenceMetadata.id == evidence_id)
        res = await session.execute(query)
        evidence = res.scalar_one_or_none()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence with ID '{evidence_id}' not found."
            )

        # Authorization check: National admin or matching institution scope
        if not is_national_admin:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if user_inst_id != evidence.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have permission to download this evidence file."
                )

        if not os.path.exists(evidence.storage_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence file content is missing or unavailable from private storage."
            )

        # Record download audit event
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="EVIDENCE_DOWNLOAD",
            target_type="EVIDENCE",
            target_id=evidence.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "evidence_id": evidence.id,
                "filename": evidence.original_filename
            })
        )
        session.add(audit)
        await session.commit()

        return FileResponse(
            path=evidence.storage_path,
            filename=evidence.original_filename,
            media_type=evidence.media_type,
            content_disposition_type="attachment"
        )
