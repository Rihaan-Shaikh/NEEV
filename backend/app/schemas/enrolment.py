from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class EnrolmentResponse(BaseModel):
    id: str
    institution_id: str
    institution_name: str
    programme_id: str
    programme_name: str
    official_programme_code: str
    academic_year_id: str
    academic_year_label: str
    institution_student_id: str
    student_full_name: str
    masked_apaar_id: Optional[str] = None
    apaar_validation_status: str
    admission_date: date
    enrolment_status: str
    admission_category: str
    supernumerary_category: Optional[str] = None
    source_submission_batch_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EnrolmentListResponse(BaseModel):
    items: List[EnrolmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
