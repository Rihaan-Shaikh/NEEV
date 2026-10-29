from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class InstitutionBase(BaseModel):
    official_institution_code: str
    name: str
    institution_type: str
    state_code: str
    district_code: str
    address: Optional[str] = None
    status: str = "ACTIVE"
    is_synthetic: bool = True

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    institution_type: Optional[str] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None

class InstitutionResponse(InstitutionBase):
    id: str
    source_reference: str
    created_at: datetime
    updated_at: datetime
    programmes_count: int = 0
    enrolments_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class InstitutionListResponse(BaseModel):
    items: List[InstitutionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
