import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import hashlib
import hmac
import uuid
from app.core.config import settings

def hash_password(password: str) -> str:
    """Securely hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a short-lived signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"iat": now, "exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

def hash_refresh_token(token: str) -> str:
    """Hash raw refresh token with SHA-256 for secure database session tracking."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def generate_apaar_fingerprint(apaar_id: str) -> str:
    """
    Generate a keyed, non-reversible comparison fingerprint using HMAC-SHA256
    with a protected server-side key. This prevents exact lookup from rainbow tables.
    """
    normalized = apaar_id.strip().replace("-", "").replace(" ", "")
    return hmac.new(
        settings.APAAR_FINGERPRINT_KEY.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def mask_apaar_id(apaar_id: Optional[str]) -> Optional[str]:
    """
    Mask an APAAR identifier for safe display by default.
    Example: 123456789012 -> '•••• •••• 9012'
    """
    if not apaar_id:
        return None
    cleaned = apaar_id.strip().replace("-", "").replace(" ", "")
    if len(cleaned) >= 4:
        last4 = cleaned[-4:]
        return f"••••-••••-{last4}"
    return "••••-••••-••••"

def sanitize_csv_cell(val: Any) -> Any:
    """
    Neutralize CSV / spreadsheet formula injection for values beginning with =, +, -, @, tab, or carriage return.
    Prepends a single quote to prevent code execution when opened in Excel/Sheets.
    """
    if isinstance(val, str) and len(val) > 0:
        if val[0] in ('=', '+', '-', '@', '\t', '\r'):
            return "'" + val
    return val
