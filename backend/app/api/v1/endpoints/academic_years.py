from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.programme import AcademicYear
from app.schemas.programme import AcademicYearResponse
from app.policies.authorization import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("", response_model=List[AcademicYearResponse])
async def list_academic_years(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AcademicYear).order_by(AcademicYear.start_date.desc()))
    return result.scalars().all()
