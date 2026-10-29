from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class VerificationReference(Base):
    __tablename__ = "verification_references"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    public_reference_code = Column(String(32), unique=True, index=True, nullable=False)
    reference_token_hash = Column(String(64), unique=True, index=True, nullable=False)
    
    enrolment_record_id = Column(String(36), ForeignKey("enrolment_records.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    issuing_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    purpose = Column(String(100), nullable=False, default="GENERAL_VERIFICATION")
    disclosure_profile = Column(Text, nullable=False)  # JSON string of permitted claim keys
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, REVOKED, EXPIRED, EXHAUSTED
    max_uses = Column(Integer, nullable=True)  # None = unlimited within validity window
    use_count = Column(Integer, default=0, nullable=False)
    
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    enrolment_record = relationship("EnrolmentRecord", lazy="selectin")
    institution = relationship("Institution", lazy="selectin")
    issuing_user = relationship("User", foreign_keys=[issuing_user_id], lazy="selectin")
    revoking_user = relationship("User", foreign_keys=[revoked_by_user_id], lazy="selectin")
    access_logs = relationship("VerificationAccessLog", back_populates="verification_reference", cascade="all, delete-orphan", order_by="desc(VerificationAccessLog.created_at)")

    __table_args__ = (
        Index("ix_vrf_inst_status", "institution_id", "status"),
        Index("ix_vrf_expiry", "expires_at", "status"),
    )

class VerificationAccessLog(Base):
    __tablename__ = "verification_access_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    verification_reference_id = Column(String(36), ForeignKey("verification_references.id", ondelete="CASCADE"), nullable=False, index=True)
    outcome = Column(String(30), nullable=False)  # SUCCESS, EXPIRED, REVOKED, USE_LIMIT_EXCEEDED, RECORD_INELIGIBLE
    disclosed_claims_json = Column(Text, nullable=True)
    request_ip_hash = Column(String(64), nullable=True)
    user_agent_safe = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    verification_reference = relationship("VerificationReference", back_populates="access_logs")

class IntegrationStatusLog(Base):
    __tablename__ = "integration_status_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    adapter_code = Column(String(50), unique=True, index=True, nullable=False)
    adapter_name = Column(String(100), nullable=False)
    status = Column(String(30), default="SIMULATED", nullable=False)  # SIMULATED, NOT_CONFIGURED, UNAVAILABLE, CONFIGURED, HEALTHY, DEGRADED
    is_simulated = Column(Boolean, default=True, nullable=False)
    last_checked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    latency_ms = Column(Float, nullable=True)
    supported_claims = Column(Text, nullable=False)  # JSON array
    known_limitations = Column(Text, nullable=False)
    contract_test_status = Column(String(20), default="PASSED", nullable=False)
    error_code = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
