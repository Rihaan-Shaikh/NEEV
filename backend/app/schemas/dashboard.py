from pydantic import BaseModel
from typing import Optional, List, Dict
from app.schemas.submission import BatchResponse

class IntakeReconciliationItem(BaseModel):
    programme_id: str
    programme_name: str
    official_programme_code: str
    academic_year_label: str
    approved_intake: Optional[int] = None
    calculated_active_enrolments: int
    variance: Optional[int] = None
    reconciliation_status: str  # BALANCED, UNDER_CAPACITY, CAPACITY_EXCEEDED, MISSING_REFERENCE
    rule_basis: str
    is_capacity_exceeded: bool
    is_synthetic: bool = True

class DashboardSummaryResponse(BaseModel):
    institutions_count: int
    programmes_count: int
    selected_academic_year: str
    batches_by_status: Dict[str, int]
    total_students_count: int
    active_students_count: int
    recent_submissions: List[BatchResponse]
    validation_issues_count: int
    programmes_exceeding_capacity: int
    reconciliation_items: List[IntakeReconciliationItem]
