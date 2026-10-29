from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String, primary_key=True, default=generate_uuid)
    official_institution_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    institution_type = Column(String, nullable=False)  # CENTRAL_UNIVERSITY, STATE_GOVERNMENT, PRIVATE_AIDED, PRIVATE_UNAIDED
    state_code = Column(String, nullable=False, index=True)
    district_code = Column(String, nullable=False)
    address = Column(String, nullable=True)
    status = Column(String, default="ACTIVE", nullable=False)  # ACTIVE, SUSPENDED, PENDING
    source_reference = Column(String, default="AICTE_REGULATORY_PORTAL", nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    programmes = relationship("Programme", back_populates="institution", cascade="all, delete-orphan")
    submission_batches = relationship("SubmissionBatch", back_populates="institution")
    enrolment_records = relationship("EnrolmentRecord", back_populates="institution")
