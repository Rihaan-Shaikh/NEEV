from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class BatchCreateRequest(BaseModel):
    institution_id: str
    academic_year_id: str
    programme_id: Optional[str] = None
    submission_type: str = "REGULAR_ENROLMENT"

class BatchResponse(BaseModel):
    id: str
    institution_id: str
    institution_name: Optional[str] = None
    academic_year_id: str
    academic_year_label: Optional[str] = None
    programme_id: Optional[str] = None
    programme_name: Optional[str] = None
    submission_type: str
    source_type: str
    processing_status: str
    source_filename: Optional[str] = None
    row_count: int
    valid_count: int
    accepted_count: int
    rejected_count: int
    flagged_count: int
    ruleset_version: str
    receipt_reference: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FindingDetail(BaseModel):
    rule_code: str
    field_name: Optional[str] = None
    severity: str  # ERROR, WARNING, INFO
    explanation: str
    raw_value: Optional[str] = None

class RowPreviewItem(BaseModel):
    row_number: int
    processing_status: str  # VALID, ERROR, WARNING
    raw_data: Dict[str, Any]
    normalized_data: Optional[Dict[str, Any]] = None
    errors: List[FindingDetail] = []
    warnings: List[FindingDetail] = []

class BatchPreviewResponse(BaseModel):
    batch: BatchResponse
    total_rows: int
    valid_rows: int
    error_rows: int
    warning_rows: int
    rows: List[RowPreviewItem]
    validation_summary: Dict[str, int]

class BatchFinalizeResponse(BaseModel):
    batch_id: str
    receipt_reference: str
    status: str
    accepted_count: int
    rejected_count: int
    issued_at: datetime
    message: str

class SubmissionReceiptResponse(BaseModel):
    id: str
    batch_id: str
    receipt_reference: str
    issued_at: datetime
    receipt_status: str
    summary_snapshot: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
