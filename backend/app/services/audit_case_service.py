import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.institution import Institution
from app.models.programme import Programme, AcademicYear
from app.models.user import User
from app.models.integrity import Finding, Notification, EvidenceMetadata
from app.models.oversight import (
    AuditCase,
    AuditCaseFinding,
    AuditCaseEvent,
    ClarificationRequest,
    AuditCaseDecision
)
from app.models.audit import AuditEvent
from app.services.notification_service import NotificationService

class AuditCaseService:
    VALID_TRANSITIONS = {
        "OPEN": ["ASSIGNED", "UNDER_REVIEW", "CLOSED_NO_ACTION"],
        "ASSIGNED": ["UNDER_REVIEW", "CLARIFICATION_REQUESTED", "CLOSED_NO_ACTION"],
        "UNDER_REVIEW": ["CLARIFICATION_REQUESTED", "RESOLVED", "ESCALATED", "CLOSED_NO_ACTION"],
        "CLARIFICATION_REQUESTED": ["RESPONSE_RECEIVED", "UNDER_REVIEW"],
        "RESPONSE_RECEIVED": ["UNDER_REVIEW"],
        "ESCALATED": ["UNDER_REVIEW"],
        "RESOLVED": [],
        "CLOSED_NO_ACTION": []
    }

    TERMINAL_STATUSES = ["RESOLVED", "ESCALATED", "CLOSED_NO_ACTION"]

    @staticmethod
    def _is_national_admin(user_roles: List[str]) -> bool:
        return any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "NATIONAL_ADMIN") for r in user_roles)

    @classmethod
    async def create_case(
        cls,
        session: AsyncSession,
        current_user: User,
        user_roles: List[str],
        institution_id: str,
        case_category: str,
        priority: str,
        creation_rationale: str,
        programme_id: Optional[str] = None,
        academic_year_id: Optional[str] = None,
        finding_ids: Optional[List[str]] = None,
        response_deadline: Optional[datetime] = None,
        assigned_reviewer_id: Optional[str] = None
    ) -> AuditCase:
        now = datetime.now(timezone.utc)

        # 1. Permission check: Only regulatory officers or national admins can initiate cases
        is_regulatory = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER", "AUDITOR") for r in user_roles)
        if not is_regulatory:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only authorized AICTE regulatory officers can create audit cases."
            )

        # 2. Validation
        if not creation_rationale or len(creation_rationale.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rule WF-002: Case creation rationale is mandatory and must contain at least 10 characters."
            )

        inst_res = await session.execute(select(Institution).where(Institution.id == institution_id))
        institution = inst_res.scalar_one_or_none()
        if not institution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Institution with ID '{institution_id}' not found."
            )

        # Generate unique case reference: CASE-YYYY-NNNN
        year = now.year
        count_q = select(func.count(AuditCase.id)).where(AuditCase.created_at >= datetime(year, 1, 1, tzinfo=timezone.utc))
        case_seq = ((await session.execute(count_q)).scalar() or 0) + 1
        case_reference = f"CASE-{year}-{case_seq:04d}"

        initial_status = "ASSIGNED" if assigned_reviewer_id else "OPEN"

        # Verify assigned reviewer if provided
        if assigned_reviewer_id:
            rev_res = await session.execute(select(User).where(User.id == assigned_reviewer_id))
            reviewer = rev_res.unique().scalar_one_or_none()
            if not reviewer or reviewer.account_status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned reviewer not found or account is not active."
                )

        audit_case = AuditCase(
            case_reference=case_reference,
            institution_id=institution_id,
            programme_id=programme_id,
            academic_year_id=academic_year_id,
            case_category=case_category,
            priority=priority,
            status=initial_status,
            creation_rationale=creation_rationale.strip(),
            assigned_reviewer_id=assigned_reviewer_id,
            response_deadline=response_deadline,
            created_by_user_id=current_user.id,
            created_at=now,
            updated_at=now
        )
        session.add(audit_case)
        await session.flush()

        # Link findings
        if finding_ids:
            for f_id in finding_ids:
                f_res = await session.execute(select(Finding).where(Finding.id == f_id))
                f_obj = f_res.scalar_one_or_none()
                if f_obj:
                    case_finding = AuditCaseFinding(
                        audit_case_id=audit_case.id,
                        finding_id=f_id,
                        linked_at=now
                    )
                    session.add(case_finding)

        # Record timeline event
        event = AuditCaseEvent(
            audit_case_id=audit_case.id,
            event_type="CASE_CREATED",
            actor_user_id=current_user.id,
            actor_name=current_user.display_name,
            to_status=initial_status,
            description=f"Audit case initiated by {current_user.display_name}. Priority: {priority}. Category: {case_category}.",
            is_internal=False,
            created_at=now
        )
        session.add(event)

        # Audit log
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="AUDIT_CASE_CREATE",
            target_type="AUDIT_CASE",
            target_id=audit_case.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "case_reference": case_reference,
                "institution_id": institution_id,
                "priority": priority,
                "findings_count": len(finding_ids or [])
            })
        )
        session.add(audit)

        # Notify assigned reviewer or national admins
        if assigned_reviewer_id:
            notif = Notification(
                recipient_user_id=assigned_reviewer_id,
                title=f"Audit Case Assigned: {case_reference}",
                message=f"You have been assigned to review {case_reference} ({institution.name}).",
                event_type="CASE_ASSIGNED",
                related_resource_type="AUDIT_CASE",
                related_resource_id=audit_case.id
            )
            session.add(notif)

        await session.commit()
        await session.refresh(audit_case)
        return audit_case

    @classmethod
    async def assign_case(
        cls,
        session: AsyncSession,
        current_user: User,
        user_roles: List[str],
        case_id: str,
        reviewer_id: str,
        rationale: Optional[str] = None
    ) -> AuditCase:
        now = datetime.now(timezone.utc)

        # Permission check
        is_regulatory = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER") for r in user_roles)
        if not is_regulatory:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only regulatory officers can assign or reassign audit cases."
            )

        case_res = await session.execute(select(AuditCase).where(AuditCase.id == case_id))
        audit_case = case_res.scalar_one_or_none()
        if not audit_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit case with ID '{case_id}' not found."
            )

        rev_res = await session.execute(select(User).where(User.id == reviewer_id))
        reviewer = rev_res.unique().scalar_one_or_none()
        if not reviewer or reviewer.account_status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target reviewer does not exist or account is inactive."
            )

        prev_reviewer_id = audit_case.assigned_reviewer_id
        is_reassignment = prev_reviewer_id is not None and prev_reviewer_id != reviewer_id

        audit_case.assigned_reviewer_id = reviewer_id
        from_status = audit_case.status
        if audit_case.status == "OPEN":
            audit_case.status = "ASSIGNED"
        audit_case.updated_at = now

        event_desc = f"Case assigned to {reviewer.display_name} by {current_user.display_name}."
        if is_reassignment:
            event_desc = f"Case reassigned from previous reviewer to {reviewer.display_name} by {current_user.display_name}."
        if rationale:
            event_desc += f" Rationale: {rationale.strip()}"

        event = AuditCaseEvent(
            audit_case_id=audit_case.id,
            event_type="REASSIGNED" if is_reassignment else "ASSIGNED",
            actor_user_id=current_user.id,
            actor_name=current_user.display_name,
            from_status=from_status,
            to_status=audit_case.status,
            description=event_desc,
            is_internal=False,
            created_at=now
        )
        session.add(event)

        # Notify new assignee
        notif = Notification(
            recipient_user_id=reviewer_id,
            title=f"Audit Case Assignment: {audit_case.case_reference}",
            message=f"You have been assigned to case {audit_case.case_reference}.",
            event_type="CASE_ASSIGNED",
            related_resource_type="AUDIT_CASE",
            related_resource_id=audit_case.id
        )
        session.add(notif)

        # Audit Event
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="AUDIT_CASE_ASSIGNMENT",
            target_type="AUDIT_CASE",
            target_id=audit_case.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "case_reference": audit_case.case_reference,
                "assigned_to": reviewer_id,
                "is_reassignment": is_reassignment
            })
        )
        session.add(audit)
        await session.commit()
        await session.refresh(audit_case)
        return audit_case

    @classmethod
    async def transition_case_status(
        cls,
        session: AsyncSession,
        current_user: User,
        user_roles: List[str],
        case_id: str,
        target_status: str,
        rationale: str
    ) -> AuditCase:
        now = datetime.now(timezone.utc)

        case_res = await session.execute(select(AuditCase).where(AuditCase.id == case_id))
        audit_case = case_res.scalar_one_or_none()
        if not audit_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit case with ID '{case_id}' not found."
            )

        current_status = audit_case.status
        allowed_targets = cls.VALID_TRANSITIONS.get(current_status, [])

        if target_status not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Rule WF-001: Invalid case lifecycle transition from '{current_status}' to '{target_status}'. Permitted: {allowed_targets}"
            )

        # Terminal state authorization check
        if target_status in cls.TERMINAL_STATUSES:
            if not cls._is_national_admin(user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Only national administrators can transition case to terminal state '{target_status}'."
                )
            if not rationale or len(rationale.strip()) < 10:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Rule WF-002: Decision rationale is mandatory and must contain at least 10 characters."
                )

        audit_case.status = target_status
        audit_case.updated_at = now
        if target_status in cls.TERMINAL_STATUSES:
            audit_case.closed_at = now
            audit_case.closure_reason = rationale.strip()

        event = AuditCaseEvent(
            audit_case_id=audit_case.id,
            event_type="STATUS_CHANGED",
            actor_user_id=current_user.id,
            actor_name=current_user.display_name,
            from_status=current_status,
            to_status=target_status,
            description=f"Status changed from {current_status} to {target_status}. Rationale: {rationale.strip()}",
            is_internal=False,
            created_at=now
        )
        session.add(event)

        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="AUDIT_CASE_TRANSITION",
            target_type="AUDIT_CASE",
            target_id=audit_case.id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "case_reference": audit_case.case_reference,
                "from_status": current_status,
                "to_status": target_status
            })
        )
        session.add(audit)
        await session.commit()
        await session.refresh(audit_case)
        return audit_case

    @classmethod
    async def add_reviewer_note(
        cls,
        session: AsyncSession,
        current_user: User,
        user_roles: List[str],
        case_id: str,
        note_text: str,
        is_internal: bool = True
    ) -> AuditCaseEvent:
        now = datetime.now(timezone.utc)
        is_regulatory = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER", "AUDITOR") for r in user_roles)
        if not is_regulatory:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only regulatory officers can record reviewer notes."
            )

        case_res = await session.execute(select(AuditCase).where(AuditCase.id == case_id))
        audit_case = case_res.scalar_one_or_none()
        if not audit_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit case with ID '{case_id}' not found."
            )

        if not note_text or not note_text.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Note text cannot be empty.")

        event = AuditCaseEvent(
            audit_case_id=case_id,
            event_type="REVIEWER_NOTE",
            actor_user_id=current_user.id,
            actor_name=current_user.display_name,
            description=note_text.strip(),
            is_internal=is_internal,
            created_at=now
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    @classmethod
    async def create_clarification_request(
        cls,
        session: AsyncSession,
        current_user: User,
        user_roles: List[str],
        case_id: str,
        subject: str,
        information_requested: str,
        response_deadline: Optional[datetime] = None
    ) -> ClarificationRequest:
        now = datetime.now(timezone.utc)
        is_regulatory = any(r in ("PLATFORM_ADMIN", "AICTE_ADMIN", "AICTE_OFFICER") for r in user_roles)
        if not is_regulatory:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only regulatory officers can request clarification."
            )

        case_res = await session.execute(select(AuditCase).where(AuditCase.id == case_id))
        audit_case = case_res.scalar_one_or_none()
        if not audit_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID '{case_id}' not found.")

        # Reference CLR-YYYY-NNNN
        year = now.year
        clr_count_q = select(func.count(ClarificationRequest.id)).where(ClarificationRequest.created_at >= datetime(year, 1, 1, tzinfo=timezone.utc))
        clr_seq = ((await session.execute(clr_count_q)).scalar() or 0) + 1
        clr_ref = f"CLR-{year}-{clr_seq:04d}"

        req = ClarificationRequest(
            audit_case_id=case_id,
            institution_id=audit_case.institution_id,
            request_reference=clr_ref,
            subject=subject.strip(),
            information_requested=information_requested.strip(),
            response_deadline=response_deadline,
            status="PENDING_RESPONSE",
            issuing_officer_id=current_user.id,
            created_at=now
        )
        session.add(req)

        # Update case status
        if audit_case.status in ["ASSIGNED", "UNDER_REVIEW"]:
            audit_case.status = "CLARIFICATION_REQUESTED"
            audit_case.updated_at = now

        # Add event
        event = AuditCaseEvent(
            audit_case_id=case_id,
            event_type="CLARIFICATION_ISSUED",
            actor_user_id=current_user.id,
            actor_name=current_user.display_name,
            to_status="CLARIFICATION_REQUESTED",
            description=f"Clarification request {clr_ref} issued: '{subject}'.",
            is_internal=False,
            created_at=now
        )
        session.add(event)

        # Notify institution admin
        notif = Notification(
            target_institution_id=audit_case.institution_id,
            role_target="INSTITUTION_ADMIN",
            title=f"Clarification Requested: {clr_ref}",
            message=f"Regulatory clarification requested regarding {audit_case.case_reference}: {subject}.",
            event_type="CLARIFICATION_REQUESTED",
            related_resource_type="AUDIT_CASE",
            related_resource_id=case_id
        )
        session.add(notif)

        await session.commit()
        await session.refresh(req)
        return req

    @classmethod
    async def submit_clarification_response(
        cls,
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        request_id: str,
        explanation: str
    ) -> ClarificationRequest:
        now = datetime.now(timezone.utc)
        req_res = await session.execute(
            select(ClarificationRequest)
            .options(selectinload(ClarificationRequest.audit_case))
            .where(ClarificationRequest.id == request_id)
        )
        req = req_res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Clarification request '{request_id}' not found.")

        # Institutional scope check
        is_national = cls._is_national_admin(user_roles)
        if not is_national:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if user_inst_id != req.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You cannot respond to clarification requests issued to another institution."
                )

        if not explanation or not explanation.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Response explanation cannot be empty.")

        req.response_explanation = explanation.strip()
        req.responded_by_user_id = current_user.id
        req.responded_at = now
        req.status = "RESPONSE_RECEIVED"

        # Update case status
        if req.audit_case and req.audit_case.status == "CLARIFICATION_REQUESTED":
            req.audit_case.status = "RESPONSE_RECEIVED"
            req.audit_case.updated_at = now

        # Add event
        event = AuditCaseEvent(
            audit_case_id=req.audit_case_id,
            event_type="RESPONSE_SUBMITTED",
            actor_user_id=current_user.id,
            actor_name=current_user.display_name,
            from_status="CLARIFICATION_REQUESTED",
            to_status="RESPONSE_RECEIVED",
            description=f"Institutional response submitted for {req.request_reference} by {current_user.display_name}.",
            is_internal=False,
            created_at=now
        )
        session.add(event)

        # Notify assigned reviewer
        if req.audit_case and req.audit_case.assigned_reviewer_id:
            notif = Notification(
                recipient_user_id=req.audit_case.assigned_reviewer_id,
                title=f"Response Received: {req.request_reference}",
                message=f"Institution submitted clarification response for case {req.audit_case.case_reference}.",
                event_type="RESPONSE_SUBMITTED",
                related_resource_type="AUDIT_CASE",
                related_resource_id=req.audit_case_id
            )
            session.add(notif)

        await session.commit()
        await session.refresh(req)
        return req

    @classmethod
    async def record_case_decision(
        cls,
        session: AsyncSession,
        current_user: User,
        user_roles: List[str],
        case_id: str,
        decision_type: str,
        decision_rationale: str,
        follow_up_action: Optional[str] = None
    ) -> AuditCaseDecision:
        now = datetime.now(timezone.utc)
        if not cls._is_national_admin(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Only authorized national regulatory administrators can record case decisions."
            )

        if decision_type not in ["RESOLVED", "ESCALATED", "CLOSED_NO_ACTION"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid decision type '{decision_type}'. Must be RESOLVED, ESCALATED, or CLOSED_NO_ACTION."
            )

        if not decision_rationale or len(decision_rationale.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Rule WF-002: Regulatory decision rationale is mandatory and must contain at least 10 characters."
            )

        case_res = await session.execute(select(AuditCase).where(AuditCase.id == case_id))
        audit_case = case_res.scalar_one_or_none()
        if not audit_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case with ID '{case_id}' not found.")

        # Create decision
        decision = AuditCaseDecision(
            audit_case_id=case_id,
            decision_type=decision_type,
            decision_rationale=decision_rationale.strip(),
            follow_up_action=follow_up_action.strip() if follow_up_action else None,
            reviewer_id=current_user.id,
            decided_at=now
        )
        session.add(decision)

        # Transition case
        from_status = audit_case.status
        audit_case.status = decision_type
        audit_case.updated_at = now
        audit_case.closed_at = now
        audit_case.closure_reason = decision_rationale.strip()

        # Add event
        event = AuditCaseEvent(
            audit_case_id=case_id,
            event_type="DECISION_RECORDED",
            actor_user_id=current_user.id,
            actor_name=current_user.display_name,
            from_status=from_status,
            to_status=decision_type,
            description=f"Regulatory decision '{decision_type}' recorded by {current_user.display_name}. Rationale: {decision_rationale.strip()}",
            is_internal=False,
            created_at=now
        )
        session.add(event)

        # Audit event
        audit = AuditEvent(
            actor_user_id=current_user.id,
            actor_email=current_user.email_normalized,
            actor_type="USER",
            action="AUDIT_CASE_DECISION",
            target_type="AUDIT_CASE",
            target_id=case_id,
            occurred_at=now,
            outcome="SUCCESS",
            metadata_json=json.dumps({
                "case_reference": audit_case.case_reference,
                "decision_type": decision_type,
                "follow_up_action": follow_up_action
            })
        )
        session.add(audit)

        await session.commit()
        await session.refresh(decision)
        return decision

    @classmethod
    async def get_case_detail(
        cls,
        session: AsyncSession,
        current_user: User,
        user_scopes: List[Any],
        user_roles: List[str],
        case_id: str
    ) -> Dict[str, Any]:
        """Retrieves full case workspace data respecting visibility rules."""
        is_national = cls._is_national_admin(user_roles) or any(r in ("AICTE_OFFICER", "AUDITOR") for r in user_roles)

        q = (
            select(AuditCase)
            .options(
                selectinload(AuditCase.institution),
                selectinload(AuditCase.programme),
                selectinload(AuditCase.academic_year),
                selectinload(AuditCase.assigned_reviewer),
                selectinload(AuditCase.created_by_user),
                selectinload(AuditCase.findings).selectinload(AuditCaseFinding.finding),
                selectinload(AuditCase.events),
                selectinload(AuditCase.clarification_requests).selectinload(ClarificationRequest.issuing_officer),
                selectinload(AuditCase.clarification_requests).selectinload(ClarificationRequest.responded_by_user),
                selectinload(AuditCase.decisions).selectinload(AuditCaseDecision.reviewer),
            )
            .where(AuditCase.id == case_id)
        )
        res = await session.execute(q)
        case = res.unique().scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Audit case with ID '{case_id}' not found.")

        # Institutional scope validation
        if not is_national:
            user_inst_id = user_scopes[0].institution_id if user_scopes else None
            if user_inst_id != case.institution_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have permission to inspect this audit case."
                )

        # Filter events for institution users (hide is_internal == True)
        visible_events = []
        for ev in case.events:
            if not is_national and ev.is_internal:
                continue
            visible_events.append({
                "id": ev.id,
                "event_type": ev.event_type,
                "actor_name": ev.actor_name,
                "from_status": ev.from_status,
                "to_status": ev.to_status,
                "description": ev.description,
                "is_internal": ev.is_internal,
                "created_at": ev.created_at
            })

        findings_data = [
            {
                "id": cf.id,
                "finding_id": cf.finding_id,
                "rule_code": cf.finding.rule_code if cf.finding else "UNKNOWN",
                "severity": cf.finding.severity if cf.finding else "WARNING",
                "status": cf.finding.status if cf.finding else "OPEN",
                "explanation": cf.finding.explanation if cf.finding else "",
                "linked_at": cf.linked_at
            }
            for cf in case.findings
        ]

        clarifications_data = [
            {
                "id": clr.id,
                "audit_case_id": clr.audit_case_id,
                "case_reference": case.case_reference,
                "institution_id": clr.institution_id,
                "institution_name": case.institution.name if case.institution else "",
                "request_reference": clr.request_reference,
                "subject": clr.subject,
                "information_requested": clr.information_requested,
                "response_deadline": clr.response_deadline,
                "status": clr.status,
                "issuing_officer_name": clr.issuing_officer.display_name if clr.issuing_officer else None,
                "response_explanation": clr.response_explanation,
                "response_evidence_id": clr.response_evidence_id,
                "responded_by_user_name": clr.responded_by_user.display_name if clr.responded_by_user else None,
                "responded_at": clr.responded_at,
                "created_at": clr.created_at
            }
            for clr in case.clarification_requests
        ]

        decisions_data = [
            {
                "id": dec.id,
                "decision_type": dec.decision_type,
                "decision_rationale": dec.decision_rationale,
                "follow_up_action": dec.follow_up_action,
                "reviewer_name": dec.reviewer.display_name if dec.reviewer else None,
                "decided_at": dec.decided_at
            }
            for dec in case.decisions
        ]

        permitted_transitions = cls.VALID_TRANSITIONS.get(case.status, [])

        return {
            "id": case.id,
            "case_reference": case.case_reference,
            "institution_id": case.institution_id,
            "institution_name": case.institution.name if case.institution else "Unknown",
            "programme_id": case.programme_id,
            "programme_name": case.programme.programme_name if case.programme else None,
            "academic_year_id": case.academic_year_id,
            "academic_year_label": case.academic_year.label if case.academic_year else None,
            "case_category": case.case_category,
            "priority": case.priority,
            "status": case.status,
            "creation_rationale": case.creation_rationale,
            "assigned_reviewer_id": case.assigned_reviewer_id,
            "assigned_reviewer_name": case.assigned_reviewer.display_name if case.assigned_reviewer else None,
            "response_deadline": case.response_deadline,
            "created_by_user_name": case.created_by_user.display_name if case.created_by_user else None,
            "created_at": case.created_at,
            "updated_at": case.updated_at,
            "closed_at": case.closed_at,
            "closure_reason": case.closure_reason,
            "findings": findings_data,
            "events": visible_events,
            "clarification_requests": clarifications_data,
            "decisions": decisions_data,
            "permitted_transitions": permitted_transitions
        }
