from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# ================= Finding Schemas =================

class FindingResponseCreate(BaseModel):
    response_type: str = Field(..., description="EXPLANATION, CORRECTION_REQUEST, TRANSFER_DOCUMENTATION, DISPUTE")
    explanation: str = Field(..., min_length=10, description="Detailed explanation of the discrepancy")
    related_correction_id: Optional[str] = None

class FindingResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    finding_id: str
    submitting_user_id: str
    submitting_user_name: Optional[str] = None
    institution_id: str
    institution_name: Optional[str] = None
    response_type: str
    explanation: str
    related_correction_id: Optional[str] = None
    review_status: str
    reviewer_notes: Optional[str] = None
    submitted_at: datetime

class FindingTransitionRequest(BaseModel):
    target_status: str = Field(..., description="Target lifecycle status: AWAITING_INSTITUTION_RESPONSE, RESPONSE_RECEIVED, UNDER_REVIEW, RESOLVED, DISMISSED, ESCALATED")
    rationale: Optional[str] = Field(None, description="Required rationale for RESOLVED, DISMISSED, ESCALATED")

class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_code: str
    rule_version: str
    category: str
    severity: str
    status: str
    explanation: str
    structured_evidence_json: Optional[str] = None
    
    primary_institution_id: str
    primary_institution_name: Optional[str] = None
    secondary_institution_id: Optional[str] = None
    secondary_institution_name: Optional[str] = None
    
    programme_id: Optional[str] = None
    programme_name: Optional[str] = None
    academic_year_id: Optional[str] = None
    academic_year_label: Optional[str] = None
    
    primary_enrolment_id: Optional[str] = None
    primary_student_name: Optional[str] = None
    primary_institution_student_id: Optional[str] = None
    primary_masked_apaar: Optional[str] = None
    
    secondary_enrolment_id: Optional[str] = None
    secondary_student_name: Optional[str] = None
    secondary_institution_student_id: Optional[str] = None
    secondary_masked_apaar: Optional[str] = None
    
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    resolution_rationale: Optional[str] = None
    resolved_by_user_id: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    first_detected_at: datetime
    last_detected_at: datetime
    created_at: datetime
    updated_at: datetime
    
    responses_count: int = 0
    evidence_count: int = 0

class FindingDetailRead(FindingRead):
    responses: List[FindingResponseRead] = []
    evidence_attachments: List["EvidenceMetadataRead"] = []
    permitted_transitions: List[str] = []

class FindingListResponse(BaseModel):
    items: List[FindingRead]
    total: int
    page: int
    page_size: int

# ================= Enrolment Version & Correction Schemas =================

class EnrolmentVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    enrolment_record_id: str
    version_number: int
    snapshot_json: str
    change_reason: str
    changed_by: str
    changed_at: datetime

class EnrolmentHistoryResponse(BaseModel):
    current_version: int
    enrolment_id: str
    student_full_name: str
    institution_student_id: str
    masked_apaar_id: Optional[str] = None
    versions: List[EnrolmentVersionRead]

class EnrolmentCorrectionRequest(BaseModel):
    expected_version: int = Field(..., description="Current version of the record for optimistic concurrency")
    correction_reason: str = Field(..., description="Mandatory reason explaining the correction")
    admission_date: Optional[str] = Field(None, description="Updated admission date (YYYY-MM-DD)")
    enrolment_status: Optional[str] = Field(None, description="ACTIVE, TRANSFERRED, WITHDRAWN, COMPLETED, SUSPENDED")
    admission_category: Optional[str] = Field(None, description="OPEN, OBC, SC, ST, EWS, etc.")
    supernumerary_category: Optional[str] = None

class EnrolmentCorrectionResponse(BaseModel):
    success: bool
    enrolment_id: str
    new_version: int
    message: str
    revalidation_findings: List[str] = []

# ================= Evidence Metadata Schemas =================

class EvidenceMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    finding_id: Optional[str] = None
    enrolment_record_id: Optional[str] = None
    original_filename: str
    media_type: str
    file_size_bytes: int
    sha256_checksum: str
    uploader_user_id: str
    uploader_name: Optional[str] = None
    institution_id: str
    institution_name: Optional[str] = None
    evidence_category: str
    source_provenance: str
    scanning_status: str
    uploaded_at: datetime

# ================= Notification Schemas =================

class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient_user_id: Optional[str] = None
    target_institution_id: Optional[str] = None
    role_target: Optional[str] = None
    title: str
    message: str
    event_type: str
    related_resource_type: str
    related_resource_id: str
    is_read: bool
    created_at: datetime

class UnreadCountResponse(BaseModel):
    unread_count: int

# ================= Integrity Reconciliation Schemas =================

class ConflictCandidate(BaseModel):
    rule_code: str
    conflict_type: str
    severity: str
    explanation: str
    primary_enrolment_id: str
    secondary_enrolment_id: str
    primary_institution_id: str
    secondary_institution_id: str
    apaar_fingerprint_masked: str
    suggested_action: str

class ReconciliationResult(BaseModel):
    status: str
    timestamp: datetime
    enrolments_inspected: int
    conflicts_detected: int
    new_findings_created: int
    existing_findings_updated: int
    message: str
