from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    actor_user_id = Column(String, nullable=True, index=True)
    actor_email = Column(String, nullable=True)
    actor_type = Column(String, default="USER", nullable=False)  # USER, SYSTEM
    action = Column(String, nullable=False, index=True)  # LOGIN, LOGOUT, BATCH_SUBMIT, BATCH_FINALIZE, etc.
    target_type = Column(String, nullable=False, index=True)  # USER, INSTITUTION, PROGRAMME, BATCH, ENROLMENT
    target_id = Column(String, nullable=True, index=True)
    occurred_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    request_id = Column(String, nullable=True, index=True)
    outcome = Column(String, default="SUCCESS", nullable=False)  # SUCCESS, FAILURE
    metadata_json = Column(Text, nullable=True)  # Restrained sanitized event payload
