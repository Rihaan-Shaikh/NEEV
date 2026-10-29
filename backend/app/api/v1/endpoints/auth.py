from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import secrets
import hashlib
import logging

from app.db.session import get_db
from app.models.user import User, Role, UserScope, RefreshSession, PasswordResetToken
from app.models.institution import Institution
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserScopeResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ProvisionUserRequest
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)
from app.core.config import settings
from app.policies.authorization import get_current_user, check_permission
from app.services.audit_service import log_audit_event

logger = logging.getLogger("neev.auth")
router = APIRouter()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def get_refresh_cookie_settings(request: Request) -> dict:
    """
    Returns cookie configuration based on deployment environment and protocol.
    Cross-origin deployments (e.g. Vercel frontend + cloud backend) over HTTPS
    require SameSite="None" and Secure=True to transmit HttpOnly credentials.
    Local HTTP development uses SameSite="Lax" and Secure=False.
    """
    is_https = (
        request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto", "").lower() == "https"
        or settings.ENVIRONMENT.lower() in ("production", "prod", "staging")
    )
    if is_https:
        return {
            "httponly": True,
            "secure": True,
            "samesite": "none",
            "path": "/",
            "max_age": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        }
    return {
        "httponly": True,
        "secure": False,
        "samesite": "lax",
        "path": "/",
        "max_age": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    }

def build_user_response(user: User) -> UserResponse:
    role_codes = [r.code for r in user.roles]
    all_perms = set()
    for r in user.roles:
        for p in r.permissions:
            all_perms.add(p.code)
        if r.code in ["PLATFORM_ADMIN", "AICTE_ADMIN"]:
            all_perms.update([
                "institution.manage", "institution.read", "enrolment.read",
                "enrolment.write", "batch.submit", "rules.configure", "user.manage"
            ])

    scopes_resp = [
        UserScopeResponse(
            id=s.id,
            scope_type=s.scope_type,
            institution_id=s.institution_id,
            valid_from=s.valid_from,
            valid_until=s.valid_until
        )
        for s in user.scopes
    ]

    return UserResponse(
        id=user.id,
        email_normalized=user.email_normalized,
        display_name=user.display_name,
        account_status=user.account_status,
        roles=role_codes,
        scopes=scopes_resp,
        permissions=sorted(list(all_perms))
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    email = req.email.strip().lower()
    result = await db.execute(select(User).where(User.email_normalized == email))
    user = result.scalars().first()

    # Constant time / generic check to avoid user enumeration
    if not user or not verify_password(req.password, user.password_hash):
        await log_audit_event(
            db,
            action="LOGIN_FAILED",
            target_type="AUTH",
            actor_email=email,
            outcome="FAILURE",
            metadata={"reason": "Invalid credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status != "active":
        await log_audit_event(
            db,
            action="LOGIN_BLOCKED",
            target_type="AUTH",
            target_id=user.id,
            actor_user_id=user.id,
            actor_email=user.email_normalized,
            outcome="FAILURE",
            metadata={"account_status": user.account_status}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.account_status}. Please contact an administrator.",
        )

    # Update last login
    user.last_login_at = utc_now()

    # Generate Tokens
    token_data = {"sub": user.id, "email": user.email_normalized}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store hashed refresh session
    rf_hash = hash_refresh_token(refresh_token)
    rf_session = RefreshSession(
        user_id=user.id,
        token_hash=rf_hash,
        expires_at=utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(rf_session)
    await db.flush()

    # Set secure HttpOnly cookie for refresh token
    cookie_settings = get_refresh_cookie_settings(request)
    response.set_cookie(
        key="neev_refresh_token",
        value=refresh_token,
        **cookie_settings
    )

    await log_audit_event(
        db,
        action="LOGIN_SUCCESS",
        target_type="USER",
        target_id=user.id,
        actor_user_id=user.id,
        actor_email=user.email_normalized,
        outcome="SUCCESS"
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=build_user_response(user)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    cookie_settings = get_refresh_cookie_settings(request)
    refresh_token = request.cookies.get("neev_refresh_token")

    if not refresh_token:
        # Check Authorization header fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header[7:]

    if not refresh_token:
        # Check JSON body fallback
        try:
            body = await request.json()
            if isinstance(body, dict):
                refresh_token = body.get("refresh_token")
        except Exception:
            pass

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session found. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if not user_id or token_type != "refresh":
            response.delete_cookie(
                key="neev_refresh_token",
                path="/",
                secure=cookie_settings["secure"],
                samesite=cookie_settings["samesite"]
            )
            raise HTTPException(status_code=401, detail="Session is invalid or malformed. Please sign in again.")
    except HTTPException:
        raise
    except Exception:
        response.delete_cookie(
            key="neev_refresh_token",
            path="/",
            secure=cookie_settings["secure"],
            samesite=cookie_settings["samesite"]
        )
        raise HTTPException(status_code=401, detail="Session has expired. Please sign in again.")

    rf_hash = hash_refresh_token(refresh_token)
    session_res = await db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == rf_hash)
    )
    rf_session = session_res.scalars().first()

    if not rf_session:
        response.delete_cookie(
            key="neev_refresh_token",
            path="/",
            secure=cookie_settings["secure"],
            samesite=cookie_settings["samesite"]
        )
        raise HTTPException(status_code=401, detail="Session not recognized or revoked. Please sign in again.")

    now = utc_now()

    # Reuse detection: If a refresh token that was already replaced/rotated is presented again,
    # it indicates token reuse or replay. Revoke the entire active session family for security.
    if rf_session.replaced_by_token_hash is not None or rf_session.revoked_at is not None:
        active_sessions = (await db.execute(
            select(RefreshSession).where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
        )).scalars().all()
        for s in active_sessions:
            s.revoked_at = now
        await db.flush()

        response.delete_cookie(
            key="neev_refresh_token",
            path="/",
            secure=cookie_settings["secure"],
            samesite=cookie_settings["samesite"]
        )

        await log_audit_event(
            db,
            action="REFRESH_TOKEN_REUSE_DETECTED",
            target_type="AUTH",
            target_id=user_id,
            actor_user_id=user_id,
            outcome="FAILURE",
            metadata={"token_hash_prefix": rf_hash[:10], "reason": "Attempted reuse of rotated token"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security notice: Session expired due to concurrent access. Please sign in again."
        )

    exp = rf_session.expires_at
    if exp.tzinfo is None:
        is_past = exp < datetime.now()
    else:
        is_past = exp < now

    if is_past:
        response.delete_cookie(
            key="neev_refresh_token",
            path="/",
            secure=cookie_settings["secure"],
            samesite=cookie_settings["samesite"]
        )
        raise HTTPException(status_code=401, detail="Session has expired. Please sign in again.")

    user = await db.get(User, user_id)
    if not user or user.account_status != "active":
        response.delete_cookie(
            key="neev_refresh_token",
            path="/",
            secure=cookie_settings["secure"],
            samesite=cookie_settings["samesite"]
        )
        raise HTTPException(status_code=403, detail="User account is inactive or missing.")

    # Rotate Refresh Token
    new_token_data = {"sub": user.id, "email": user.email_normalized}
    new_access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    new_rf_hash = hash_refresh_token(new_refresh_token)

    # Invalidate old session and link to new session
    rf_session.revoked_at = now
    rf_session.replaced_by_token_hash = new_rf_hash

    new_session = RefreshSession(
        user_id=user.id,
        token_hash=new_rf_hash,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_session)
    await db.flush()

    response.set_cookie(
        key="neev_refresh_token",
        value=new_refresh_token,
        **cookie_settings
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=build_user_response(user)
    )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("neev_refresh_token")
    if not refresh_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header[7:]
    if not refresh_token:
        try:
            body = await request.json()
            if isinstance(body, dict):
                refresh_token = body.get("refresh_token")
        except Exception:
            pass

    user_id = None
    if refresh_token:
        rf_hash = hash_refresh_token(refresh_token)
        session_res = await db.execute(select(RefreshSession).where(RefreshSession.token_hash == rf_hash))
        session = session_res.scalars().first()
        if session:
            user_id = session.user_id
            session.revoked_at = utc_now()
            await db.flush()

    cookie_settings = get_refresh_cookie_settings(request)
    response.delete_cookie(
        key="neev_refresh_token",
        path="/",
        secure=cookie_settings["secure"],
        samesite=cookie_settings["samesite"]
    )

    if user_id:
        await log_audit_event(
            db,
            action="LOGOUT",
            target_type="USER",
            target_id=user_id,
            actor_user_id=user_id,
            outcome="SUCCESS"
        )

    return {"message": "Session successfully terminated"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return build_user_response(current_user)

@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    email = req.email.strip().lower()
    result = await db.execute(select(User).where(User.email_normalized == email))
    user = result.scalars().first()

    # Generic return to prevent user enumeration
    generic_msg = "If an authorized account is associated with this email address, password recovery instructions have been initiated."

    if user and user.account_status == "active":
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_reset_token(raw_token)
        expires_at = utc_now() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(reset_record)
        await db.flush()

        await log_audit_event(
            db,
            action="PASSWORD_RESET_REQUESTED",
            target_type="USER",
            target_id=user.id,
            actor_email=user.email_normalized,
            outcome="SUCCESS"
        )

        # In development environment, log the testing link clearly for local testability
        if settings.ENVIRONMENT.lower() == "development":
            logger.info(
                f"[DEVELOPMENT ONLY] Password reset initiated. "
                f"Test Reset URL: http://localhost:3000/reset-password?token={raw_token}"
            )
            return {
                "message": generic_msg,
                "dev_reset_token": raw_token  # Provided strictly for development / automated testing
            }

    return {"message": generic_msg}

@router.post("/reset-password")
async def reset_password(
    req: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    token_hash = hash_reset_token(req.token)
    res = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    record = res.scalars().first()

    now = utc_now()
    if not record or record.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used password reset link."
        )

    exp = record.expires_at
    if exp.tzinfo is None:
        is_past = exp < datetime.now()
    else:
        is_past = exp < now

    if is_past:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link has expired. Please submit a new request."
        )

    user = await db.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User account not found.")

    # Update password
    user.password_hash = hash_password(req.new_password)
    record.used_at = now

    # Invalidate all active refresh sessions for this user (security requirement)
    active_sessions = (await db.execute(
        select(RefreshSession).where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))
    )).scalars().all()
    for s in active_sessions:
        s.revoked_at = now

    await db.flush()

    await log_audit_event(
        db,
        action="PASSWORD_RESET_SUCCESS",
        target_type="USER",
        target_id=user.id,
        actor_user_id=user.id,
        actor_email=user.email_normalized,
        outcome="SUCCESS"
    )

    return {"message": "Password successfully updated. Please sign in with your new password."}

@router.post("/provision-user", response_model=UserResponse)
async def provision_user(
    req: ProvisionUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Enforce administrator permissions
    is_admin = any(r.code in ["PLATFORM_ADMIN", "AICTE_ADMIN"] for r in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: only platform or AICTE administrators can provision accounts."
        )

    email = req.email.strip().lower()
    existing = await db.execute(select(User).where(User.email_normalized == email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    role_res = await db.execute(select(Role).where(Role.code == req.role_code))
    role = role_res.scalars().first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Invalid role code: {req.role_code}")

    if req.role_code == "INSTITUTION_ADMIN":
        if not req.institution_id:
            raise HTTPException(status_code=400, detail="Institution ID is required for institutional administrator accounts.")
        inst = await db.get(Institution, req.institution_id)
        if not inst:
            raise HTTPException(status_code=400, detail="Specified institution does not exist.")

    initial_pass = req.initial_password or "NeevTemp@2026"
    new_user = User(
        email_normalized=email,
        password_hash=hash_password(initial_pass),
        display_name=req.display_name.strip(),
        account_status="active",
        email_verified_at=utc_now()
    )
    new_user.roles.append(role)
    db.add(new_user)
    await db.flush()

    # Assign scope
    scope_type = "INSTITUTION" if req.role_code == "INSTITUTION_ADMIN" else "NATIONAL"
    user_scope = UserScope(
        user_id=new_user.id,
        scope_type=scope_type,
        institution_id=req.institution_id if scope_type == "INSTITUTION" else None,
        valid_from=utc_now()
    )
    db.add(user_scope)
    await db.flush()

    await log_audit_event(
        db,
        action="USER_PROVISIONED",
        target_type="USER",
        target_id=new_user.id,
        actor_user_id=current_user.id,
        actor_email=current_user.email_normalized,
        metadata={"role": req.role_code, "scope_type": scope_type, "institution_id": req.institution_id}
    )

    # Reload relationships
    reloaded = (await db.execute(select(User).where(User.id == new_user.id))).scalars().first()
    return build_user_response(reloaded)

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    is_admin = any(r.code in ["PLATFORM_ADMIN", "AICTE_ADMIN"] for r in current_user.roles)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: user directory access is restricted to national administrators."
        )

    users = (await db.execute(select(User).order_by(User.email_normalized.asc()))).scalars().all()
    return [build_user_response(u) for u in users]
