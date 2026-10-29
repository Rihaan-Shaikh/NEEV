from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class StudentIdentity(Base):
    __tablename__ = "student_identities"

    id = Column(String, primary_key=True, default=generate_uuid)
    apaar_id_ciphertext = Column(String, nullable=True)  # Protected/encrypted storage
    apaar_id_fingerprint = Column(String, nullable=True, index=True)  # Keyed HMAC comparison value
    apaar_validation_status = Column(String, default="UNAVAILABLE", nullable=False)  # UNAVAILABLE, SIMULATED, FORMAT_VALID
    apaar_validation_source = Column(String, default="NONE", nullable=False)
    apaar_validation_checked_at = Column(DateTime(timezone=True), nullable=True)
    masked_apaar_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    enrolments = relationship("EnrolmentRecord", back_populates="student_identity")

class EnrolmentRecord(Base):
    __tablename__ = "enrolment_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    student_identity_id = Column(String, ForeignKey("student_identities.id", ondelete="RESTRICT"), nullable=False, index=True)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    programme_id = Column(String, ForeignKey("programmes.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id = Column(String, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    institution_student_id = Column(String, nullable=False, index=True)  # e.g., "IITD-2024-CSE-001"
    student_full_name = Column(String, nullable=False)
    admission_date = Column(Date, nullable=False)
    enrolment_status = Column(String, default="ACTIVE", nullable=False, index=True)  # ACTIVE, TRANSFERRED, WITHDRAWN, COMPLETED, SUSPENDED
    admission_category = Column(String, default="OPEN", nullable=False)  # OPEN, OBC, SC, ST, EWS, NRI, MANAGEMENT
    supernumerary_category = Column(String, nullable=True)  # J&K, PMSSS, TWF, SPORTS, FOREIGN_NATIONAL
    source_submission_batch_id = Column(String, ForeignKey("submission_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    current_record_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    student_identity = relationship("StudentIdentity", back_populates="enrolments")
    institution = relationship("Institution", back_populates="enrolment_records")
    programme = relationship("Programme", back_populates="enrolment_records")
    academic_year = relationship("AcademicYear", back_populates="enrolment_records")
    batch = relationship("SubmissionBatch", back_populates="enrolments")
    versions = relationship("EnrolmentRecordVersion", back_populates="enrolment_record", cascade="all, delete-orphan", order_by="EnrolmentRecordVersion.version_number.asc()")

class EnrolmentRecordVersion(Base):
    __tablename__ = "enrolment_record_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    enrolment_record_id = Column(String, ForeignKey("enrolment_records.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    change_reason = Column(String, default="INITIAL_IMPORT", nullable=False)
    changed_by = Column(String, nullable=False)
    changed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    enrolment_record = relationship("EnrolmentRecord", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("enrolment_record_id", "version_number", name="uq_enrolment_record_version"),
    )

