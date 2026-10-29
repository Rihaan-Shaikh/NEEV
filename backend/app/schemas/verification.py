from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class VerificationReferenceCreateRequest(BaseModel):
    enrolment_record_id: str
    purpose: str = Field(default="GENERAL_VERIFICATION", min_length=3, max_length=100)
    disclosure_profile: Dict[str, bool] = Field(default_factory=lambda: {
        "disclose_student_name": True,
        "disclose_programme": True,
        "disclose_enrolment_status": True,
        "disclose_academic_year": True,
        "disclose_institution": True,
        "disclose_admission_date": False
    })
    expires_in_days: int = Field(default=30, ge=1, le=180)
    max_uses: Optional[int] = Field(default=None, ge=1, le=100)

class VerificationReferenceRevokeRequest(BaseModel):
    revocation_reason: str = Field(min_length=5, max_length=255)

class VerificationResolveRequest(BaseModel):
    reference_token: str = Field(min_length=10, max_length=128)

class VerificationAccessLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    outcome: str
    disclosed_claims_json: Optional[str] = None
    created_at: datetime

class VerificationReferenceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_reference_code: str
    enrolment_record_id: str
    student_full_name: str
    institution_id: str
    institution_name: str
    programme_name: Optional[str] = None
    academic_year_label: Optional[str] = None
    purpose: str
    disclosure_profile: Dict[str, bool]
    status: str
    max_uses: Optional[int] = None
    use_count: int
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    created_at: datetime
    access_logs_count: int = 0

class VerificationReferenceCreatedResponse(VerificationReferenceItem):
    raw_bearer_token: str  # Disclosed strictly once at generation time

class VerificationReferenceListResponse(BaseModel):
    items: List[VerificationReferenceItem]
    total: int
    page: int
    page_size: int

class VerificationResultResponse(BaseModel):
    outcome: str  # SUCCESS, INVALID_TOKEN, EXPIRED, REVOKED, USE_LIMIT_EXCEEDED, RECORD_INELIGIBLE
    public_reference_code: Optional[str] = None
    verified_at: datetime
    purpose: Optional[str] = None
    disclosed_claims: Optional[Dict[str, Any]] = None
    synthetic_disclaimer: str = "Synthetic demonstration — not an official APAAR verification."
    message: str

class IntegrationStatusItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    adapter_code: str
    adapter_name: str
    status: str
    is_simulated: bool
    last_checked_at: datetime
    latency_ms: Optional[float] = None
    supported_claims: List[str]
    known_limitations: str
    contract_test_status: str
    error_code: Optional[str] = None

class IntegrationTestResponse(BaseModel):
    adapter_code: str
    contract_test_status: str
    latency_ms: float
    checked_at: datetime
    message: str
