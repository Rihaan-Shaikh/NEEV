from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class AcademicYearResponse(BaseModel):
    id: str
    label: str
    start_date: date
    end_date: date
    status: str

    model_config = ConfigDict(from_attributes=True)

class ProgrammeResponse(BaseModel):
    id: str
    institution_id: str
    institution_name: Optional[str] = None
    official_programme_code: str
    programme_name: str
    qualification_level: str
    academic_discipline: str
    status: str
    created_at: datetime
    active_intake: Optional[int] = None
    active_enrolments_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class ProgrammeApprovalDetailResponse(BaseModel):
    approval_id: str
    approval_reference: str
    approval_status: str
    academic_year: str
    approved_intake: Optional[int] = None
    intake_version: Optional[int] = None
    source_reference: str
    source_type: str
    effective_from: date
    effective_until: date
    is_synthetic: bool = True
