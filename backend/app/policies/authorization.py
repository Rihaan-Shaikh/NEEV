from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import jwt

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Validate access token and retrieve current active user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not user_id or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.account_status}. Please contact administrator.",
        )

    return user

def user_has_permission(user: User, permission_code: str) -> bool:
    """Check if the user has a specific granular permission via any assigned role."""
    for role in user.roles:
        # Platform and AICTE admins have all management permissions
        if role.code in ["PLATFORM_ADMIN", "AICTE_ADMIN"]:
            return True
        for perm in role.permissions:
            if perm.code == permission_code:
                return True
    return False

def check_permission(permission_code: str):
    """Dependency factory to enforce specific permission."""
    async def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not user_has_permission(current_user, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: missing '{permission_code}' capability",
            )
        return current_user
    return permission_dependency

def get_user_permitted_institution_ids(user: User) -> Optional[List[str]]:
    """
    Returns list of institution IDs user has access to, or None if user has unrestricted national scope.
    """
    # Check if user has national scope
    for role in user.roles:
        if role.code in ["PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER", "AUDITOR"]:
            return None
            
    for scope in user.scopes:
        if scope.scope_type == "NATIONAL":
            return None

    # Institution-scoped user
    allowed_ids = [s.institution_id for s in user.scopes if s.scope_type == "INSTITUTION" and s.institution_id]
    return allowed_ids

def enforce_institution_scope(user: User, target_institution_id: str) -> None:
    """
    Enforces that target_institution_id is within user's permitted institutional scope.
    Raises 403 Forbidden on boundary violation.
    """
    allowed_ids = get_user_permitted_institution_ids(user)
    if allowed_ids is None:
        return  # National scope permitted

    if target_institution_id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: target institution is outside your authorized institutional scope",
        )
