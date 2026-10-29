from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import json
from app.models.audit import AuditEvent

async def log_audit_event(
    db: AsyncSession,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    actor_type: str = "USER",
    request_id: Optional[str] = None,
    outcome: str = "SUCCESS",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """
    Persist an append-only audit event. Sensitive data (passwords, tokens, full student payloads)
    is never placed in metadata.
    """
    event = AuditEvent(
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        actor_type=actor_type,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        outcome=outcome,
        metadata_json=json.dumps(metadata) if metadata else None
    )
    db.add(event)
    await db.flush()
    return event
