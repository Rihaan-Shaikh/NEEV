from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.policies.authorization import get_current_user
from app.services.evidence_service import EvidenceService

router = APIRouter()

@router.get("/{evidence_id}")
async def download_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles = [r.code for r in current_user.roles]
    return await EvidenceService.get_evidence_file_response(
        session=db,
        evidence_id=evidence_id,
        current_user=current_user,
        user_scopes=current_user.scopes,
        user_roles=roles
    )
