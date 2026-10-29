from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ProvisionUserRequest(BaseModel):
    email: EmailStr
    display_name: str
    role_code: str
    institution_id: Optional[str] = None
    initial_password: Optional[str] = None

class UserScopeResponse(BaseModel):
    id: str
    scope_type: str  # NATIONAL or INSTITUTION
    institution_id: Optional[str] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: str
    email_normalized: str
    display_name: str
    account_status: str
    roles: List[str]
    scopes: List[UserScopeResponse]
    permissions: List[str]

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserResponse
