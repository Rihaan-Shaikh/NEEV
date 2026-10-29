from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any

from app.db.session import get_db
from app.models.submission import SubmissionBatch, SubmissionReceipt
from app.models.user import User
from app.schemas.submission import (
    BatchCreateRequest,
    BatchResponse,
    BatchPreviewResponse,
    BatchFinalizeResponse,
    SubmissionReceiptResponse
)
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)
from app.services.submission_service import (
    create_submission_batch,
    process_batch_csv,
    get_batch_preview,
    finalize_submission_batch
)
from app.core.config import settings

router = APIRouter()

def build_batch_response(batch: SubmissionBatch) -> BatchResponse:
    return BatchResponse(
        id=batch.id,
        institution_id=batch.institution_id,
        institution_name=batch.institution.name if batch.institution else None,
        academic_year_id=batch.academic_year_id,
        academic_year_label=batch.academic_year.label if batch.academic_year else None,
        programme_id=batch.programme_id,
        programme_name=batch.programme.programme_name if batch.programme else None,
        submission_type=batch.submission_type,
        source_type=batch.source_type,
        processing_status=batch.processing_status,
        source_filename=batch.source_filename,
        row_count=batch.row_count,
        valid_count=batch.valid_count,
        accepted_count=batch.accepted_count,
        rejected_count=batch.rejected_count,
        flagged_count=batch.flagged_count,
        ruleset_version=batch.ruleset_version,
        receipt_reference=batch.receipt_reference,
        created_at=batch.created_at
    )

@router.get("", response_model=List[BatchResponse])
async def list_batches(
    institution_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    allowed_ids = get_user_permitted_institution_ids(current_user)

    query = select(SubmissionBatch).options(
        selectinload(SubmissionBatch.institution),
        selectinload(SubmissionBatch.academic_year),
        selectinload(SubmissionBatch.programme)
    )

    if allowed_ids is not None:
        query = query.where(SubmissionBatch.institution_id.in_(allowed_ids))

    if institution_id:
        enforce_institution_scope(current_user, institution_id)
        query = query.where(SubmissionBatch.institution_id == institution_id)

    if status:
        query = query.where(SubmissionBatch.processing_status == status.upper())

    batches = (await db.execute(query.order_by(SubmissionBatch.created_at.desc()).limit(limit))).scalars().all()
    return [build_batch_response(b) for b in batches]

@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    req: BatchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    batch = await create_submission_batch(
        db=db,
        user=current_user,
        institution_id=req.institution_id,
        academic_year_id=req.academic_year_id,
        programme_id=req.programme_id,
        submission_type=req.submission_type
    )

    # Reload with relationships
    res = await db.execute(
        select(SubmissionBatch)
        .options(
            selectinload(SubmissionBatch.institution),
            selectinload(SubmissionBatch.academic_year),
            selectinload(SubmissionBatch.programme)
        )
        .where(SubmissionBatch.id == batch.id)
    )
    loaded_batch = res.scalars().first()
    return build_batch_response(loaded_batch)

@router.post("/{batch_id}/file", response_model=BatchResponse)
async def upload_batch_file(
    batch_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only .csv roster files are permitted in Phase 1."
        )

    # Read bytes with size protection
    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    batch, total_rows, valid_rows, error_rows = await process_batch_csv(
        db=db,
        user=current_user,
        batch_id=batch_id,
        file_bytes=file_bytes,
        filename=file.filename
    )

    # Reload relationships
    res = await db.execute(
        select(SubmissionBatch)
        .options(
            selectinload(SubmissionBatch.institution),
            selectinload(SubmissionBatch.academic_year),
            selectinload(SubmissionBatch.programme)
        )
        .where(SubmissionBatch.id == batch.id)
    )
    loaded = res.scalars().first()
    return build_batch_response(loaded)

@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(SubmissionBatch)
        .options(
            selectinload(SubmissionBatch.institution),
            selectinload(SubmissionBatch.academic_year),
            selectinload(SubmissionBatch.programme)
        )
        .where(SubmissionBatch.id == batch_id)
    )
    batch = res.scalars().first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    enforce_institution_scope(current_user, batch.institution_id)
    return build_batch_response(batch)

@router.get("/{batch_id}/preview", response_model=BatchPreviewResponse)
async def get_preview(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_batch_preview(db=db, user=current_user, batch_id=batch_id)

@router.post("/{batch_id}/finalize", response_model=BatchFinalizeResponse)
async def finalize_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await finalize_submission_batch(db=db, user=current_user, batch_id=batch_id)

@router.get("/{batch_id}/receipt", response_model=SubmissionReceiptResponse)
async def get_receipt(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    batch = await db.get(SubmissionBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    enforce_institution_scope(current_user, batch.institution_id)

    receipt_res = await db.execute(
        select(SubmissionReceipt).where(SubmissionReceipt.batch_id == batch_id)
    )
    receipt = receipt_res.scalars().first()
    if not receipt:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found. The batch has not yet been finalized."
        )

    import json
    return SubmissionReceiptResponse(
        id=receipt.id,
        batch_id=receipt.batch_id,
        receipt_reference=receipt.receipt_reference,
        issued_at=receipt.issued_at,
        receipt_status=receipt.receipt_status,
        summary_snapshot=json.loads(receipt.summary_snapshot_json)
    )
