from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.seed import DEFAULT_USER_ID

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me")
async def get_current_user(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == DEFAULT_USER_ID))
    user = result.scalar_one()
    return {
        "id": str(user.id),
        "name": user.name,
        "created_at": user.created_at.isoformat(),
    }
