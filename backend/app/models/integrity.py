from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=generate_uuid)
    rule_code = Column(String, nullable=False, index=True)  # DUP-001, DUP-002, DUP-003, DUP-004, etc.
    rule_version = Column(String, default="1.0.0", nullable=False)
    category = Column(String, nullable=False, index=True)  # DUPLICATE, HISTORY, PROVENANCE, WORKFLOW
    severity = Column(String, default="WARNING", nullable=False, index=True)  # CRITICAL, ERROR, WARNING, INFO
    status = Column(String, default="OPEN", nullable=False, index=True)  
    # Lifecycle: OPEN, AWAITING_INSTITUTION_RESPONSE, RESPONSE_RECEIVED, UNDER_REVIEW, RESOLVED, DISMISSED, ESCALATED
    explanation = Column(Text, nullable=False)
    structured_evidence_json = Column(Text, nullable=True)  # Candidate matches, dates, overlapping periods
    
    primary_institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    secondary_institution_id = Column(String, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    programme_id = Column(String, ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year_id = Column(String, ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True)
    
    primary_enrolment_id = Column(String, ForeignKey("enrolment_records.id", ondelete="CASCADE"), nullable=True, index=True)
    secondary_enrolment_id = Column(String, ForeignKey("enrolment_records.id", ondelete="SET NULL"), nullable=True, index=True)
    
    assigned_reviewer_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resolution_rationale = Column(Text, nullable=True)
    resolved_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    first_detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_detected_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    primary_institution = relationship("Institution", foreign_keys=[primary_institution_id])
    secondary_institution = relationship("Institution", foreign_keys=[secondary_institution_id])
    programme = relationship("Programme", foreign_keys=[programme_id])
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])
    primary_enrolment = relationship("EnrolmentRecord", foreign_keys=[primary_enrolment_id])
    secondary_enrolment = relationship("EnrolmentRecord", foreign_keys=[secondary_enrolment_id])
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    resolved_by_user = relationship("User", foreign_keys=[resolved_by_user_id])
    
    responses = relationship("FindingResponse", back_populates="finding", cascade="all, delete-orphan", order_by="FindingResponse.submitted_at.desc()")
    evidence_attachments = relationship("EvidenceMetadata", back_populates="finding", cascade="all, delete-orphan", order_by="EvidenceMetadata.uploaded_at.desc()")

    __table_args__ = (
        UniqueConstraint(
            "rule_code", 
            "primary_enrolment_id", 
            "secondary_enrolment_id", 
            name="uq_rule_primary_secondary_enrolment"
        ),
    )


class FindingResponse(Base):
    __tablename__ = "finding_responses"

    id = Column(String, primary_key=True, default=generate_uuid)
    finding_id = Column(String, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    submitting_user_id = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    response_type = Column(String, nullable=False)  # EXPLANATION, CORRECTION_REQUEST, TRANSFER_DOCUMENTATION, DISPUTE
    explanation = Column(Text, nullable=False)
    related_correction_id = Column(String, nullable=True)
    review_status = Column(String, default="PENDING", nullable=False)  # PENDING, ACCEPTED, REJECTED
    reviewer_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    finding = relationship("Finding", back_populates="responses")
    submitting_user = relationship("User", foreign_keys=[submitting_user_id])
    institution = relationship("Institution", foreign_keys=[institution_id])


class EvidenceMetadata(Base):
    __tablename__ = "evidence_metadata"

    id = Column(String, primary_key=True, default=generate_uuid)
    finding_id = Column(String, ForeignKey("findings.id", ondelete="SET NULL"), nullable=True, index=True)
    enrolment_record_id = Column(String, ForeignKey("enrolment_records.id", ondelete="SET NULL"), nullable=True, index=True)
    original_filename = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # application/pdf, image/png, image/jpeg
    file_size_bytes = Column(Integer, nullable=False)
    sha256_checksum = Column(String, nullable=False, index=True)
    storage_path = Column(String, nullable=False)  # Private storage path
    uploader_user_id = Column(String, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    institution_id = Column(String, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    evidence_category = Column(String, default="OTHER", nullable=False)  # TRANSFER_CERTIFICATE, ADMISSION_LETTER, IDENTITY_DOCUMENT, ERP_EXTRACT, OTHER
    source_provenance = Column(String, default="INSTITUTION_SUBMISSION", nullable=False)  
    # Provenance labels: INSTITUTION_SUBMISSION, INSTITUTION_ERP, AUTHORIZED_IDENTITY_VALIDATION, AUTHORIZED_ACADEMIC_RECORD,
    # STUDENT_CONFIRMATION, MANUAL_DOCUMENT_REVIEW, AICTE_REVIEW, EXTERNAL_SOURCE_UNAVAILABLE, SIMULATED_INTEGRATION
    scanning_status = Column(String, default="CLEARED_LOCAL", nullable=False)  # PENDING_SCAN, CLEARED_LOCAL, QUARANTINED, SIMULATED_CLEARED
    uploaded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    finding = relationship("Finding", back_populates="evidence_attachments")
    enrolment_record = relationship("EnrolmentRecord")
    uploader = relationship("User", foreign_keys=[uploader_user_id])
    institution = relationship("Institution", foreign_keys=[institution_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    recipient_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    target_institution_id = Column(String, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    role_target = Column(String, nullable=True, index=True)  # e.g. NATIONAL_ADMIN, INSTITUTION_ADMIN
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    event_type = Column(String, nullable=False, index=True)  # FINDING_CREATED, RESPONSE_SUBMITTED, TRANSITION_OCCURRED, CORRECTION_APPLIED, EVIDENCE_ATTACHED
    related_resource_type = Column(String, nullable=False)  # FINDING, ENROLMENT, SUBMISSION
    related_resource_id = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    recipient = relationship("User", foreign_keys=[recipient_user_id])
    target_institution = relationship("Institution", foreign_keys=[target_institution_id])
