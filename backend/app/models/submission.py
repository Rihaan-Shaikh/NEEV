from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SubmissionBatch(Base):
    __tablename__ = "submission_batches"

    id = Column(String, primary_key=True, default=generate_uuid)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id = Column(String, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    programme_id = Column(String, ForeignKey("programmes.id", ondelete="RESTRICT"), nullable=True, index=True)
    submission_type = Column(String, default="REGULAR_ENROLMENT", nullable=False)
    source_type = Column(String, default="CSV_UPLOAD", nullable=False)
    submitted_by_user_id = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    processing_status = Column(String, default="CREATED", nullable=False, index=True)  # CREATED, UPLOADED, VALIDATED, FINALIZED, REJECTED
    source_filename = Column(String, nullable=True)
    source_checksum = Column(String, nullable=True)
    row_count = Column(Integer, default=0, nullable=False)
    valid_count = Column(Integer, default=0, nullable=False)
    accepted_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    flagged_count = Column(Integer, default=0, nullable=False)
    ruleset_version = Column(String, default="v1.0.0", nullable=False)
    receipt_reference = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    institution = relationship("Institution", back_populates="submission_batches")
    academic_year = relationship("AcademicYear", back_populates="submission_batches")
    programme = relationship("Programme")
    submitter = relationship("User")
    rows = relationship("SubmissionRow", back_populates="batch", cascade="all, delete-orphan")
    receipt = relationship("SubmissionReceipt", back_populates="batch", uselist=False, cascade="all, delete-orphan")
    enrolments = relationship("EnrolmentRecord", back_populates="batch")
    validation_runs = relationship("ValidationRun", back_populates="batch", cascade="all, delete-orphan")

class SubmissionRow(Base):
    __tablename__ = "submission_rows"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("submission_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    processing_status = Column(String, default="PENDING", nullable=False)  # PENDING, VALID, ERROR, WARNING, ACCEPTED, REJECTED
    raw_data_json = Column(Text, nullable=False)
    normalized_data_json = Column(Text, nullable=True)
    errors_json = Column(Text, nullable=True)  # JSON array of error dicts
    warnings_json = Column(Text, nullable=True)  # JSON array of warning dicts
    linked_enrolment_record_id = Column(String, nullable=True)
    processed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    batch = relationship("SubmissionBatch", back_populates="rows")

class SubmissionReceipt(Base):
    __tablename__ = "submission_receipts"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("submission_batches.id", ondelete="CASCADE"), unique=True, nullable=False)
    receipt_reference = Column(String, unique=True, index=True, nullable=False)  # e.g., "NEEV-RCPT-2024-XXXX"
    issued_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    receipt_status = Column(String, default="ISSUED", nullable=False)
    summary_snapshot_json = Column(Text, nullable=False)

    batch = relationship("SubmissionBatch", back_populates="receipt")
