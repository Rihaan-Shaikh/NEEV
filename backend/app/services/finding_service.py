import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.integrity import Finding, FindingResponse, Notification
from app.models.institution import Institution
from app.models.user import User
from app.models.audit import AuditEvent

PERMITTED_TRANSITIONS = {
    "OPEN": ["AWAITING_INSTITUTION_RESPONSE", "UNDER_REVIEW"],
    "AWAITING_INSTITUTION_RESPONSE": ["RESPONSE_RECEIVED", "UNDER_REVIEW"],
    "RESPONSE_RECEIVED": ["UNDER_REVIEW"],
    "UNDER_REVIEW": ["RESOLVED", "DISMISSED", "ESCALATED"],
    "ESCALATED": ["UNDER_REVIEW", "RESOLVED", "DISMISSED"],
    "RESOLVED": [],
    "DISMISSED": [],
}

class FindingService:
    @staticmethod
    def get_permitted_transitions_for_user(finding_status: str, is_national_admin: bool) -> List[str]:
        base_transitions = PERMITTED_TRANSITIONS.get(finding_status, [])
        if not is_national_admin:
            # Institution admins can only transition to RESPONSE_RECEIVED (handled via response submission)
            return [t for t in base_transitions if t == "RESPONSE_RECEIVED"]
        return base_transitions

    @staticmethod
    async def transition_finding_status(
        session: AsyncSession,
        finding_id: str,
        target_status: str,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        rationale: Optional[str] = None
    ) -> Finding:
        now = datetime.now(timezone.utc)
        is_national_admin = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in user_roles)

        query = (
            select(Finding)
            .where(Finding.id == finding_id)
            .options(
                selectinload(Finding.primary_institution),
                selectinload(Finding.secondary_institution)
            )
        )
        res = await session.execute(query)
        finding = res.scalar_one_or_none()
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Finding with ID '{finding_id}' not found."
            )

        # Check tenant isolation if user is institution-scoped
        if not is_national_admin:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if user_inst_id not in (finding.primary_institution_id, finding.secondary_institution_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not authorized to view or manage findings for other institutions."
                )

        current_status = finding.status
        allowed = PERMITTED_TRANSITIONS.get(current_status, [])

        # WF-001: Invalid finding-state transition
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"WF-001: Invalid state transition from '{current_status}' to '{target_status}'. Allowed transitions: {allowed}."
            )

        # Terminal and oversight status transitions require NATIONAL_ADMIN
        if target_status in ("UNDER_REVIEW", "RESOLVED", "DISMISSED", "ESCALATED") and not is_national_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Only national administrators and authorized reviewers can transition findings to '{target_status}'."
            )

        # WF-002: Required response or resolution rationale missing
        if target_status in ("RESOLVED", "DISMISSED", "ESCALATED"):
            if not rationale or len(rationale.strip()) < 10:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="WF-002: A documented resolution rationale of at least 10 characters is required for this decision."
                )

        # Apply state transition
        finding.status = target_status
        finding.last_detected_at = now

        if target_status in ("RESOLVED", "DISMISSED"):
            finding.resolution_rationale = rationale
            finding.resolved_by_user_id = current_user.id
            finding.resolved_at = now
        elif target_status == "UNDER_REVIEW":
            finding.assigned_reviewer_id = current_user.id

        # Record audit event
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="FINDING_STATUS_TRANSITION",
            target_type="FINDING",
            target_id=finding.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "from_status": current_status,
                "to_status": target_status,
                "rationale": rationale,
                "rule_code": finding.rule_code
            })
        )
        session.add(audit)

        # Notify relevant institutions
        notif = Notification(
            target_institution_id=finding.primary_institution_id,
            role_target="INSTITUTION_ADMIN",
            title=f"Finding Status Updated: {target_status}",
            message=f"Finding {finding.rule_code} status transitioned to {target_status}. Rationale: {rationale or 'N/A'}",
            event_type="TRANSITION_OCCURRED",
            related_resource_type="FINDING",
            related_resource_id=finding.id,
            is_read=False,
            created_at=now
        )
        session.add(notif)

        await session.commit()
        return finding

    @staticmethod
    async def submit_response(
        session: AsyncSession,
        finding_id: str,
        response_type: str,
        explanation: str,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        related_correction_id: Optional[str] = None
    ) -> FindingResponse:
        now = datetime.now(timezone.utc)
        is_national_admin = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in user_roles)

        query = (
            select(Finding)
            .where(Finding.id == finding_id)
            .options(
                selectinload(Finding.primary_institution),
                selectinload(Finding.secondary_institution)
            )
        )
        res = await session.execute(query)
        finding = res.scalar_one_or_none()
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Finding with ID '{finding_id}' not found."
            )

        # Derive institutional scope
        if is_national_admin:
            submitting_inst_id = finding.primary_institution_id
        else:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if user_inst_id not in (finding.primary_institution_id, finding.secondary_institution_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You cannot submit a response on behalf of an unrelated institution."
                )
            submitting_inst_id = user_inst_id

        # Create response
        response = FindingResponse(
            finding_id=finding.id,
            submitting_user_id=current_user.id,
            institution_id=submitting_inst_id,
            response_type=response_type,
            explanation=explanation,
            related_correction_id=related_correction_id,
            review_status="PENDING",
            submitted_at=now
        )
        session.add(response)

        # Automatically transition status if currently OPEN or AWAITING_INSTITUTION_RESPONSE
        if finding.status in ("OPEN", "AWAITING_INSTITUTION_RESPONSE"):
            finding.status = "RESPONSE_RECEIVED"
            finding.last_detected_at = now

        # Record audit event
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="FINDING_RESPONSE_SUBMITTED",
            target_type="FINDING",
            target_id=finding.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "response_type": response_type,
                "institution_id": submitting_inst_id,
                "explanation_preview": explanation[:100]
            })
        )
        session.add(audit)

        # Notify reviewers
        notif = Notification(
            recipient_user_id=finding.assigned_reviewer_id,
            role_target="NATIONAL_ADMIN",
            title="Institutional Response Received",
            message=f"An institutional response was submitted for finding {finding.rule_code}.",
            event_type="RESPONSE_SUBMITTED",
            related_resource_type="FINDING",
            related_resource_id=finding.id,
            is_read=False,
            created_at=now
        )
        session.add(notif)

        await session.commit()
        return response
