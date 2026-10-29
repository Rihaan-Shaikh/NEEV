from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ================= Risk Calculation Schemas =================

class RiskFactorBreakdown(BaseModel):
    capacity_discrepancy: float
    unresolved_conflicts: float
    data_quality: float
    unusual_roster_changes: float
    source_reconciliation_gap: float
    repeated_prior_findings: float
    total_score: float
    risk_band: str
    completeness_state: str
    explanation: str

class RiskCalculationResponse(BaseModel):
    id: str
    institution_id: str
    institution_name: Optional[str] = None
    programme_id: Optional[str] = None
    programme_name: Optional[str] = None
    academic_year_id: Optional[str] = None
    academic_year_label: Optional[str] = None
    total_score: float
    risk_band: str
    calculation_version: str
    factors: RiskFactorBreakdown
    input_snapshot: Dict[str, Any]
    explanation: str
    completeness_state: str
    calculated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class RiskQueueItem(BaseModel):
    institution_id: str
    institution_name: str
    official_code: str
    state: Optional[str] = None
    total_score: float
    risk_band: str
    unresolved_findings_count: int
    open_cases_count: int
    last_calculated_at: datetime
    completeness_state: str

class RiskQueueResponse(BaseModel):
    items: List[RiskQueueItem]
    total: int
    page: int
    page_size: int

class InstitutionRiskProfileResponse(BaseModel):
    institution_id: str
    institution_name: str
    official_code: str
    current_calculation: Optional[RiskCalculationResponse] = None
    history: List[RiskCalculationResponse] = []
    unresolved_findings_count: int
    active_cases_count: int
    programmes_exceeding_capacity_count: int

# ================= Audit Case Schemas =================

class AuditCaseCreateRequest(BaseModel):
    institution_id: str
    programme_id: Optional[str] = None
    academic_year_id: Optional[str] = None
    case_category: str = "REGULATORY_REVIEW"  # CAPACITY_VIOLATION, CROSS_INSTITUTION_DUPLICATE, DATA_QUALITY_ANOMALY, REGULATORY_REVIEW, GENERAL
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    creation_rationale: str
    finding_ids: List[str] = []
    response_deadline: Optional[datetime] = None
    assigned_reviewer_id: Optional[str] = None

class AuditCaseAssignRequest(BaseModel):
    reviewer_id: str
    rationale: Optional[str] = None

class AuditCaseTransitionRequest(BaseModel):
    target_status: str
    rationale: str  # Mandatory for terminal states (>= 10 chars)

class AuditCaseNoteRequest(BaseModel):
    note: str
    is_internal: bool = True  # True = regulatory reviewer confidential note

class AuditCaseFindingItem(BaseModel):
    id: str
    finding_id: str
    rule_code: str
    severity: str
    status: str
    explanation: str
    linked_at: datetime

class AuditCaseEventItem(BaseModel):
    id: str
    event_type: str
    actor_name: Optional[str] = None
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    description: str
    is_internal: bool
    created_at: datetime

class ClarificationRequestCreateRequest(BaseModel):
    subject: str
    information_requested: str
    response_deadline: Optional[datetime] = None

class ClarificationResponseSubmitRequest(BaseModel):
    explanation: str

class ClarificationRequestItem(BaseModel):
    id: str
    audit_case_id: str
    case_reference: Optional[str] = None
    institution_id: str
    institution_name: Optional[str] = None
    request_reference: str
    subject: str
    information_requested: str
    response_deadline: Optional[datetime] = None
    status: str
    issuing_officer_name: Optional[str] = None
    response_explanation: Optional[str] = None
    response_evidence_id: Optional[str] = None
    responded_by_user_name: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime

class AuditCaseDecisionRequest(BaseModel):
    decision_type: str  # RESOLVED, ESCALATED, CLOSED_NO_ACTION
    decision_rationale: str
    follow_up_action: Optional[str] = None

class AuditCaseDecisionItem(BaseModel):
    id: str
    decision_type: str
    decision_rationale: str
    follow_up_action: Optional[str] = None
    reviewer_name: Optional[str] = None
    decided_at: datetime

class AuditCaseDetailResponse(BaseModel):
    id: str
    case_reference: str
    institution_id: str
    institution_name: str
    programme_id: Optional[str] = None
    programme_name: Optional[str] = None
    academic_year_id: Optional[str] = None
    academic_year_label: Optional[str] = None
    case_category: str
    priority: str
    status: str
    creation_rationale: str
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    response_deadline: Optional[datetime] = None
    created_by_user_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    closure_reason: Optional[str] = None
    
    findings: List[AuditCaseFindingItem] = []
    events: List[AuditCaseEventItem] = []
    clarification_requests: List[ClarificationRequestItem] = []
    decisions: List[AuditCaseDecisionItem] = []
    permitted_transitions: List[str] = []

    class Config:
        from_attributes = True

class AuditCaseListItem(BaseModel):
    id: str
    case_reference: str
    institution_id: str
    institution_name: str
    case_category: str
    priority: str
    status: str
    assigned_reviewer_name: Optional[str] = None
    response_deadline: Optional[datetime] = None
    findings_count: int
    created_at: datetime
    updated_at: datetime

class AuditCaseListResponse(BaseModel):
    items: List[AuditCaseListItem]
    total: int
    page: int
    page_size: int

# ================= Report Schemas =================

class ReportDefinition(BaseModel):
    report_type: str
    title: str
    description: str
    supported_formats: List[str] = ["CSV"]
    category: str

class ReportJobCreateRequest(BaseModel):
    report_type: str
    institution_id: Optional[str] = None
    academic_year_id: Optional[str] = None
    state: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class ReportJobResponse(BaseModel):
    id: str
    report_type: str
    report_title: str
    status: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    academic_year_label: Optional[str] = None
    row_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ================= Dashboard Schemas =================

class NationalDashboardMetricsResponse(BaseModel):
    covered_institutions_count: int
    programmes_with_intake_count: int
    total_submitted_enrolments: int
    total_active_enrolments: int
    submission_completion_rate_pct: float
    required_fields_complete_pct: float
    valid_format_apaar_pct: float
    unresolved_conflict_findings_count: int
    programmes_requiring_intake_review_count: int
    open_correction_requests_count: int
    open_audit_cases_count: int
    risk_band_distribution: Dict[str, int]
    findings_by_category: Dict[str, int]
    cases_by_status: Dict[str, int]
    academic_year_label: str

class InstitutionDashboardMetricsResponse(BaseModel):
    institution_id: str
    institution_name: str
    official_code: str
    submission_progress_pct: float
    total_enrolments_count: int
    active_enrolments_count: int
    programmes_count: int
    programmes_exceeding_capacity_count: int
    open_findings_count: int
    findings_awaiting_response_count: int
    responses_submitted_count: int
    resolved_findings_count: int
    open_clarification_requests_count: int
    active_audit_cases_count: int
    latest_receipt_reference: Optional[str] = None
    current_risk_band: str
    current_risk_score: float
    academic_year_label: str
