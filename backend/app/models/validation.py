from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ValidationRule(Base):
    __tablename__ = "validation_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    rule_code = Column(String, unique=True, index=True, nullable=False)  # SCH-001, APA-001, etc.
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)  # SCHEMA, IDENTIFIER, ENROLMENT, INTAKE
    severity = Column(String, default="ERROR", nullable=False)  # ERROR, WARNING, INFO
    version = Column(String, default="1.0.0", nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("submission_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(String, nullable=False, index=True)
    programme_id = Column(String, nullable=True)
    academic_year_id = Column(String, nullable=False)
    ruleset_version = Column(String, default="1.0.0", nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED
    summary_json = Column(Text, nullable=True)

    batch = relationship("SubmissionBatch", back_populates="validation_runs")
    findings = relationship("ValidationFinding", back_populates="validation_run", cascade="all, delete-orphan")

class ValidationFinding(Base):
    __tablename__ = "validation_findings"

    id = Column(String, primary_key=True, default=generate_uuid)
    rule_code = Column(String, nullable=False, index=True)
    validation_run_id = Column(String, ForeignKey("validation_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    batch_id = Column(String, nullable=True, index=True)
    row_number = Column(Integer, nullable=True)
    field_name = Column(String, nullable=True)
    severity = Column(String, default="ERROR", nullable=False)  # ERROR, WARNING, INFO
    explanation = Column(String, nullable=False)
    raw_value = Column(String, nullable=True)
    status = Column(String, default="OPEN", nullable=False)  # OPEN, RESOLVED, DISMISSED
    first_detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    validation_run = relationship("ValidationRun", back_populates="findings")
