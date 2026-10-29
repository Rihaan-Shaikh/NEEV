from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.policies.authorization import get_current_user
from app.schemas.verification import (
    IntegrationStatusItem,
    IntegrationTestResponse
)
from app.services.integration_service import IntegrationService

router = APIRouter()

@router.get("/integrations/status", response_model=List[IntegrationStatusItem])
async def list_integration_statuses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns transparency status metadata for all external adapters (APAAR, AISHE, NAD, State Boards, AICTE).
    Clearly distinguishes simulated prototypes from live APIs.
    """
    adapters = await IntegrationService.list_adapters(session=db)
    return [IntegrationStatusItem(**a) for a in adapters]

@router.get("/integrations/{adapter_code}/status", response_model=IntegrationStatusItem)
async def get_integration_status(
    adapter_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns status and contract metadata for a specific integration adapter.
    """
    adapter = await IntegrationService.get_adapter(session=db, adapter_code=adapter_code)
    return IntegrationStatusItem(**adapter)

@router.post("/integrations/{adapter_code}/test-contract", response_model=IntegrationTestResponse)
async def test_integration_contract(
    adapter_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a simulated contract test probe against the external adapter.
    """
    res = await IntegrationService.test_contract(session=db, adapter_code=adapter_code)
    return IntegrationTestResponse(**res)
