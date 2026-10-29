from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.db.session import get_db
from app.models.user import User
from app.models.institution import Institution
from app.models.oversight import (
    AuditCase,
    ClarificationRequest,
    AuditCaseFinding,
    AuditCaseEvent,
    AuditCaseDecision
)
from app.policies.authorization import (
    get_current_user,
    get_user_permitted_institution_ids,
    enforce_institution_scope
)
from app.schemas.oversight import (
    AuditCaseCreateRequest,
    AuditCaseAssignRequest,
    AuditCaseTransitionRequest,
    AuditCaseNoteRequest,
    AuditCaseDecisionRequest,
    ClarificationRequestCreateRequest,
    ClarificationResponseSubmitRequest,
    AuditCaseDetailResponse,
    AuditCaseListResponse,
    AuditCaseListItem,
    ClarificationRequestItem,
    AuditCaseDecisionItem,
    AuditCaseEventItem
)
from app.services.audit_case_service import AuditCaseService

router = APIRouter()

@router.post("/audit-cases", response_model=AuditCaseDetailResponse)
async def create_audit_case(
    payload: AuditCaseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates an audit case from findings, review recommendation, or institution review.
    Requires regulatory authority (PLATFORM_ADMIN, AICTE_ADMIN, AICTE_OFFICER, AUDITOR).
    """
    roles = [r.code for r in current_user.roles]
    case = await AuditCaseService.create_case(
        session=db,
        current_user=current_user,
        user_roles=roles,
        institution_id=payload.institution_id,
        case_category=payload.case_category,
        priority=payload.priority,
        creation_rationale=payload.creation_rationale,
        programme_id=payload.programme_id,
        academic_year_id=payload.academic_year_id,
        finding_ids=payload.finding_ids,
        response_deadline=payload.response_deadline,
        assigned_reviewer_id=payload.assigned_reviewer_id
    )
    detail = await AuditCaseService.get_case_detail(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        case_id=case.id
    )
    return AuditCaseDetailResponse(**detail)

from pydantic import BaseModel
from app.models.user import User, Role

class ReviewerItem(BaseModel):
    id: str
    display_name: str
    email: str
    role: str

@router.get("/audit-cases/reviewers", response_model=List[ReviewerItem])
async def list_regulatory_reviewers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns regulatory reviewers eligible for audit case assignment.
    """
    q = (
        select(User)
        .join(User.roles)
        .options(selectinload(User.roles))
        .where(User.account_status == "active", Role.code.in_(["REGULATOR_OFFICER", "SYSTEM_ADMIN"]))
        .distinct()
    )
    res_users = (await db.execute(q)).unique().scalars().all()
    out = []
    for u in res_users:
        codes = [r.code for r in u.roles]
        primary = "REGULATOR_OFFICER" if "REGULATOR_OFFICER" in codes else codes[0]
        out.append(ReviewerItem(
            id=u.id,
            display_name=u.display_name or u.email_normalized,
            email=u.email_normalized,
            role=primary
        ))
    return out

@router.get("/audit-cases", response_model=AuditCaseListResponse)
async def list_audit_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    assigned_reviewer_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Searches and paginates audit cases within the user's permitted institutional scope.
    """
    allowed_ids = get_user_permitted_institution_ids(current_user)
    q = select(AuditCase).options(
        selectinload(AuditCase.institution),
        selectinload(AuditCase.assigned_reviewer),
        selectinload(AuditCase.findings)
    )

    if allowed_ids is not None:
        q = q.where(AuditCase.institution_id.in_(allowed_ids))
    elif institution_id:
        q = q.where(AuditCase.institution_id == institution_id)

    if status_filter:
        q = q.where(AuditCase.status == status_filter)
    if priority:
        q = q.where(AuditCase.priority == priority)
    if assigned_reviewer_id:
        q = q.where(AuditCase.assigned_reviewer_id == assigned_reviewer_id)
    if search:
        q = q.join(Institution).where(
            or_(
                AuditCase.case_reference.ilike(f"%{search}%"),
                Institution.name.ilike(f"%{search}%")
            )
        )

    # Count
    count_q = select(func.count(AuditCase.id))
    if allowed_ids is not None:
        count_q = count_q.where(AuditCase.institution_id.in_(allowed_ids))
    elif institution_id:
        count_q = count_q.where(AuditCase.institution_id == institution_id)
    if status_filter:
        count_q = count_q.where(AuditCase.status == status_filter)
    if priority:
        count_q = count_q.where(AuditCase.priority == priority)
    if assigned_reviewer_id:
        count_q = count_q.where(AuditCase.assigned_reviewer_id == assigned_reviewer_id)

    total = (await db.execute(count_q)).scalar() or 0

    cases = (
        await db.execute(
            q.order_by(AuditCase.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    items = [
        AuditCaseListItem(
            id=c.id,
            case_reference=c.case_reference,
            institution_id=c.institution_id,
            institution_name=c.institution.name if c.institution else "Unknown",
            case_category=c.case_category,
            priority=c.priority,
            status=c.status,
            assigned_reviewer_name=c.assigned_reviewer.display_name if c.assigned_reviewer else None,
            response_deadline=c.response_deadline,
            findings_count=len(c.findings or []),
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in cases
    ]

    return AuditCaseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/audit-cases/{case_id}", response_model=AuditCaseDetailResponse)
async def get_audit_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full audit case workspace data.
    Internal notes and actions are filtered based on user role.
    """
    roles = [r.code for r in current_user.roles]
    detail = await AuditCaseService.get_case_detail(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        case_id=case_id
    )
    return AuditCaseDetailResponse(**detail)

@router.patch("/audit-cases/{case_id}/assignment", response_model=AuditCaseDetailResponse)
async def assign_audit_case(
    case_id: str,
    payload: AuditCaseAssignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Assigns or reassigns an audit case to a regulatory reviewer.
    """
    roles = [r.code for r in current_user.roles]
    await AuditCaseService.assign_case(
        session=db,
        current_user=current_user,
        user_roles=roles,
        case_id=case_id,
        reviewer_id=payload.reviewer_id,
        rationale=payload.rationale
    )
    detail = await AuditCaseService.get_case_detail(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        case_id=case_id
    )
    return AuditCaseDetailResponse(**detail)

@router.post("/audit-cases/{case_id}/events", response_model=AuditCaseDetailResponse)
async def transition_audit_case(
    case_id: str,
    payload: AuditCaseTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Transitions the case through its permitted state machine.
    """
    roles = [r.code for r in current_user.roles]
    await AuditCaseService.transition_case_status(
        session=db,
        current_user=current_user,
        user_roles=roles,
        case_id=case_id,
        target_status=payload.target_status,
        rationale=payload.rationale
    )
    detail = await AuditCaseService.get_case_detail(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        case_id=case_id
    )
    return AuditCaseDetailResponse(**detail)

@router.post("/audit-cases/{case_id}/notes", response_model=AuditCaseEventItem)
async def add_reviewer_note(
    case_id: str,
    payload: AuditCaseNoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Records a reviewer note on the case workspace.
    """
    roles = [r.code for r in current_user.roles]
    event = await AuditCaseService.add_reviewer_note(
        session=db,
        current_user=current_user,
        user_roles=roles,
        case_id=case_id,
        note_text=payload.note,
        is_internal=payload.is_internal
    )
    return AuditCaseEventItem(
        id=event.id,
        event_type=event.event_type,
        actor_name=event.actor_name,
        from_status=event.from_status,
        to_status=event.to_status,
        description=event.description,
        is_internal=event.is_internal,
        created_at=event.created_at
    )

@router.post("/audit-cases/{case_id}/clarification-requests", response_model=ClarificationRequestItem)
async def create_clarification_request(
    case_id: str,
    payload: ClarificationRequestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Issues a formal clarification request to the institution.
    """
    roles = [r.code for r in current_user.roles]
    req = await AuditCaseService.create_clarification_request(
        session=db,
        current_user=current_user,
        user_roles=roles,
        case_id=case_id,
        subject=payload.subject,
        information_requested=payload.information_requested,
        response_deadline=payload.response_deadline
    )
    return ClarificationRequestItem(
        id=req.id,
        audit_case_id=req.audit_case_id,
        institution_id=req.institution_id,
        request_reference=req.request_reference,
        subject=req.subject,
        information_requested=req.information_requested,
        response_deadline=req.response_deadline,
        status=req.status,
        issuing_officer_name=current_user.display_name,
        created_at=req.created_at
    )

@router.post("/audit-cases/{case_id}/decisions", response_model=AuditCaseDecisionItem)
async def record_case_decision(
    case_id: str,
    payload: AuditCaseDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Records an authorized regulatory review decision with mandatory rationale.
    """
    roles = [r.code for r in current_user.roles]
    dec = await AuditCaseService.record_case_decision(
        session=db,
        current_user=current_user,
        user_roles=roles,
        case_id=case_id,
        decision_type=payload.decision_type,
        decision_rationale=payload.decision_rationale,
        follow_up_action=payload.follow_up_action
    )
    return AuditCaseDecisionItem(
        id=dec.id,
        decision_type=dec.decision_type,
        decision_rationale=dec.decision_rationale,
        follow_up_action=dec.follow_up_action,
        reviewer_name=current_user.display_name,
        decided_at=dec.decided_at
    )

# ================= Clarification Endpoints =================

@router.get("/clarification-requests", response_model=List[ClarificationRequestItem])
async def list_clarification_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists clarification requests within the user's permitted institutional scope.
    """
    allowed_ids = get_user_permitted_institution_ids(current_user)
    q = select(ClarificationRequest).options(
        selectinload(ClarificationRequest.audit_case),
        selectinload(ClarificationRequest.institution),
        selectinload(ClarificationRequest.issuing_officer),
        selectinload(ClarificationRequest.responded_by_user)
    )

    if allowed_ids is not None:
        q = q.where(ClarificationRequest.institution_id.in_(allowed_ids))
    if status_filter:
        q = q.where(ClarificationRequest.status == status_filter)

    requests = (await db.execute(q.order_by(ClarificationRequest.created_at.desc()))).scalars().all()

    return [
        ClarificationRequestItem(
            id=r.id,
            audit_case_id=r.audit_case_id,
            case_reference=r.audit_case.case_reference if r.audit_case else None,
            institution_id=r.institution_id,
            institution_name=r.institution.name if r.institution else None,
            request_reference=r.request_reference,
            subject=r.subject,
            information_requested=r.information_requested,
            response_deadline=r.response_deadline,
            status=r.status,
            issuing_officer_name=r.issuing_officer.display_name if r.issuing_officer else None,
            response_explanation=r.response_explanation,
            response_evidence_id=r.response_evidence_id,
            responded_by_user_name=r.responded_by_user.display_name if r.responded_by_user else None,
            responded_at=r.responded_at,
            created_at=r.created_at
        )
        for r in requests
    ]

@router.get("/clarification-requests/{request_id}", response_model=ClarificationRequestItem)
async def get_clarification_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detail of a clarification request.
    """
    q = (
        select(ClarificationRequest)
        .options(
            selectinload(ClarificationRequest.audit_case),
            selectinload(ClarificationRequest.institution),
            selectinload(ClarificationRequest.issuing_officer),
            selectinload(ClarificationRequest.responded_by_user)
        )
        .where(ClarificationRequest.id == request_id)
    )
    req = (await db.execute(q)).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request '{request_id}' not found.")

    enforce_institution_scope(current_user, req.institution_id)

    return ClarificationRequestItem(
        id=req.id,
        audit_case_id=req.audit_case_id,
        case_reference=req.audit_case.case_reference if req.audit_case else None,
        institution_id=req.institution_id,
        institution_name=req.institution.name if req.institution else None,
        request_reference=req.request_reference,
        subject=req.subject,
        information_requested=req.information_requested,
        response_deadline=req.response_deadline,
        status=req.status,
        issuing_officer_name=req.issuing_officer.display_name if req.issuing_officer else None,
        response_explanation=req.response_explanation,
        response_evidence_id=req.response_evidence_id,
        responded_by_user_name=req.responded_by_user.display_name if req.responded_by_user else None,
        responded_at=req.responded_at,
        created_at=req.created_at
    )

@router.post("/clarification-requests/{request_id}/response", response_model=ClarificationRequestItem)
@router.post("/clarification-requests/{request_id}/respond", response_model=ClarificationRequestItem)
async def submit_clarification_response(
    request_id: str,
    payload: ClarificationResponseSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an institutional response to a clarification request.
    Restricted to authorized institution administrators.
    """
    roles = [r.code for r in current_user.roles]
    req = await AuditCaseService.submit_clarification_response(
        session=db,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles,
        request_id=request_id,
        explanation=payload.explanation
    )
    return ClarificationRequestItem(
        id=req.id,
        audit_case_id=req.audit_case_id,
        institution_id=req.institution_id,
        request_reference=req.request_reference,
        subject=req.subject,
        information_requested=req.information_requested,
        response_deadline=req.response_deadline,
        status=req.status,
        response_explanation=req.response_explanation,
        responded_by_user_name=current_user.display_name,
        responded_at=req.responded_at,
        created_at=req.created_at
    )
