from sqlalchemy import Column, String, Integer, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(String, primary_key=True, default=generate_uuid)
    label = Column(String, unique=True, index=True, nullable=False)  # e.g., "2024-2025"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)  # ACTIVE, HISTORICAL, UPCOMING

    approvals = relationship("ProgrammeApproval", back_populates="academic_year")
    enrolment_records = relationship("EnrolmentRecord", back_populates="academic_year")
    submission_batches = relationship("SubmissionBatch", back_populates="academic_year")

class Programme(Base):
    __tablename__ = "programmes"

    id = Column(String, primary_key=True, default=generate_uuid)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    official_programme_code = Column(String, nullable=False, index=True)  # e.g., "BTECH-CSE", "BTECH-ECE"
    programme_name = Column(String, nullable=False)
    qualification_level = Column(String, nullable=False)  # UNDERGRADUATE, POSTGRADUATE, DIPLOMA
    academic_discipline = Column(String, default="Engineering & Technology", nullable=False)
    status = Column(String, default="APPROVED", nullable=False)  # APPROVED, DISCONTINUED
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    institution = relationship("Institution", back_populates="programmes")
    approvals = relationship("ProgrammeApproval", back_populates="programme", cascade="all, delete-orphan")
    enrolment_records = relationship("EnrolmentRecord", back_populates="programme")

class ProgrammeApproval(Base):
    __tablename__ = "programme_approvals"

    id = Column(String, primary_key=True, default=generate_uuid)
    programme_id = Column(String, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(String, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    approval_reference = Column(String, nullable=False)  # e.g., "AICTE/EOA/2024-25/1-DEMO"
    approval_status = Column(String, default="APPROVED", nullable=False)
    source_reference = Column(String, default="AICTE_EOA_LETTER", nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    programme = relationship("Programme", back_populates="approvals")
    academic_year = relationship("AcademicYear", back_populates="approvals")
    intake_versions = relationship("ApprovedIntakeVersion", back_populates="programme_approval", cascade="all, delete-orphan")

class ApprovedIntakeVersion(Base):
    __tablename__ = "approved_intake_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    programme_approval_id = Column(String, ForeignKey("programme_approvals.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_intake = Column(Integer, nullable=False)  # e.g., 120
    source_type = Column(String, default="AICTE_APPROVAL_LETTER", nullable=False)
    source_reference = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=False)
    recorded_by = Column(String, default="SYSTEM_INITIALIZER", nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    programme_approval = relationship("ProgrammeApproval", back_populates="intake_versions")

class SeatCategoryRule(Base):
    __tablename__ = "seat_category_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    rule_code = Column(String, unique=True, index=True, nullable=False)
    rule_name = Column(String, nullable=False)
    programme_scope = Column(String, default="ALL", nullable=False)
    academic_year_scope = Column(String, default="ALL", nullable=False)
    rule_version = Column(Integer, default=1, nullable=False)
    configuration_json = Column(Text, nullable=False)  # JSON defining category limits, e.g. supernumerary, NRI
    status = Column(String, default="ACTIVE", nullable=False)
