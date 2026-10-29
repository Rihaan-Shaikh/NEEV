from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    rule_code: Optional[str] = None

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
