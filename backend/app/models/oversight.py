from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    Float, 
    DateTime, 
    ForeignKey, 
    Text, 
    Boolean, 
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RiskCalculation(Base):
    __tablename__ = "risk_calculations"

    id = Column(String, primary_key=True, default=generate_uuid)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(String, ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year_id = Column(String, ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True)
    
    total_score = Column(Float, nullable=False)  # 0.0 to 100.0
    risk_band = Column(String, nullable=False, index=True)  # ROUTINE, WATCH, REVIEW_RECOMMENDED, PRIORITY_REVIEW
    calculation_version = Column(String, default="1.0.0", nullable=False)
    
    # Illustrative Factor contributions
    factor_capacity_discrepancy = Column(Float, default=0.0, nullable=False)      # max 25
    factor_unresolved_conflicts = Column(Float, default=0.0, nullable=False)      # max 25
    factor_data_quality = Column(Float, default=0.0, nullable=False)              # max 15
    factor_unusual_roster_changes = Column(Float, default=0.0, nullable=False)    # max 15
    factor_source_reconciliation_gap = Column(Float, default=0.0, nullable=False) # max 10
    factor_repeated_prior_findings = Column(Float, default=0.0, nullable=False)   # max 10
    
    input_snapshot_json = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    completeness_state = Column(String, default="COMPLETE", nullable=False)  # COMPLETE, PARTIAL_MISSING_EXTERNAL, PARTIAL_NO_INTAKE
    
    calculated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    triggered_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id])
    programme = relationship("Programme", foreign_keys=[programme_id])
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])
    triggered_by_user = relationship("User", foreign_keys=[triggered_by_user_id])


class AuditCase(Base):
    __tablename__ = "audit_cases"

    id = Column(String, primary_key=True, default=generate_uuid)
    case_reference = Column(String, unique=True, nullable=False, index=True)  # e.g. CASE-2026-0001
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    programme_id = Column(String, ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year_id = Column(String, ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True)
    
    case_category = Column(String, default="GENERAL", nullable=False, index=True)
    # Categories: CAPACITY_VIOLATION, CROSS_INSTITUTION_DUPLICATE, DATA_QUALITY_ANOMALY, REGULATORY_REVIEW, GENERAL
    priority = Column(String, default="MEDIUM", nullable=False, index=True)
    # Priorities: LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String, default="OPEN", nullable=False, index=True)
    # Statuses: OPEN, ASSIGNED, UNDER_REVIEW, CLARIFICATION_REQUESTED, RESPONSE_RECEIVED, RESOLVED, ESCALATED, CLOSED_NO_ACTION
    
    creation_rationale = Column(Text, nullable=False)
    assigned_reviewer_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    response_deadline = Column(DateTime(timezone=True), nullable=True)
    
    created_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closure_reason = Column(Text, nullable=True)

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id])
    programme = relationship("Programme", foreign_keys=[programme_id])
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])

    findings = relationship("AuditCaseFinding", back_populates="audit_case", cascade="all, delete-orphan")
    events = relationship("AuditCaseEvent", back_populates="audit_case", cascade="all, delete-orphan", order_by="AuditCaseEvent.created_at.asc()")
    clarification_requests = relationship("ClarificationRequest", back_populates="audit_case", cascade="all, delete-orphan", order_by="ClarificationRequest.created_at.asc()")
    decisions = relationship("AuditCaseDecision", back_populates="audit_case", cascade="all, delete-orphan", order_by="AuditCaseDecision.decided_at.desc()")


class AuditCaseFinding(Base):
    __tablename__ = "audit_case_findings"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_case_id = Column(String, ForeignKey("audit_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    linked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    audit_case = relationship("AuditCase", back_populates="findings")
    finding = relationship("Finding")

    __table_args__ = (
        UniqueConstraint("audit_case_id", "finding_id", name="uq_audit_case_finding"),
    )


class AuditCaseEvent(Base):
    __tablename__ = "audit_case_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_case_id = Column(String, ForeignKey("audit_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    # Event types: CASE_CREATED, ASSIGNED, REASSIGNED, STATUS_CHANGED, CLARIFICATION_ISSUED, RESPONSE_SUBMITTED, REVIEWER_NOTE, DECISION_RECORDED, CLOSED
    
    actor_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_name = Column(String, nullable=True)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False, index=True)  # True for private reviewer notes
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    audit_case = relationship("AuditCase", back_populates="events")
    actor = relationship("User", foreign_keys=[actor_user_id])


class ClarificationRequest(Base):
    __tablename__ = "clarification_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_case_id = Column(String, ForeignKey("audit_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    request_reference = Column(String, unique=True, nullable=False, index=True)  # e.g. CLR-2026-0001
    subject = Column(String, nullable=False)
    information_requested = Column(Text, nullable=False)
    response_deadline = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="PENDING_RESPONSE", nullable=False, index=True)  # PENDING_RESPONSE, RESPONSE_RECEIVED, CLOSED
    
    issuing_officer_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    response_explanation = Column(Text, nullable=True)
    response_evidence_id = Column(String, ForeignKey("evidence_metadata.id", ondelete="SET NULL"), nullable=True)
    responded_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    audit_case = relationship("AuditCase", back_populates="clarification_requests")
    institution = relationship("Institution", foreign_keys=[institution_id])
    issuing_officer = relationship("User", foreign_keys=[issuing_officer_id])
    responded_by_user = relationship("User", foreign_keys=[responded_by_user_id])
    response_evidence = relationship("EvidenceMetadata", foreign_keys=[response_evidence_id])


class AuditCaseDecision(Base):
    __tablename__ = "audit_case_decisions"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_case_id = Column(String, ForeignKey("audit_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_type = Column(String, nullable=False, index=True)  # RESOLVED, ESCALATED, CLOSED_NO_ACTION
    decision_rationale = Column(Text, nullable=False)
    follow_up_action = Column(Text, nullable=True)
    reviewer_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    audit_case = relationship("AuditCase", back_populates="decisions")
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class ReportJob(Base):
    __tablename__ = "report_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    report_type = Column(String, nullable=False, index=True)
    # Types: ENROLMENT_RECONCILIATION, PROGRAMME_INTAKE_VARIANCE, DATA_QUALITY_SUMMARY,
    # IDENTIFIER_COVERAGE, DUPLICATE_CONFLICT_FINDINGS, FINDING_RESOLUTION_PERFORMANCE,
    # SUBMISSION_TIMELINESS, AUDIT_CASE_STATUS_OUTCOMES, HISTORICAL_RECORD_CHANGES, STATE_PROGRAMME_AGGREGATES
    report_title = Column(String, nullable=False)
    status = Column(String, default="QUEUED", nullable=False, index=True)  # QUEUED, RUNNING, COMPLETED, FAILED
    
    requester_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year_id = Column(String, ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True)
    
    filter_criteria_json = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_user_id])
    institution = relationship("Institution", foreign_keys=[institution_id])
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])
