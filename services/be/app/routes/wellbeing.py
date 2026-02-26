from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.analytics import AnalyticsService
from app.services.wellbeing import WellbeingService

router = APIRouter(prefix="/api/wellbeing", tags=["wellbeing"])


@router.get("/assess")
async def assess_wellbeing(
    conversation_id: uuid.UUID = Query(...),
    request: Request = None,
    session: AsyncSession = Depends(get_session),
):
    analytics_svc = AnalyticsService(session, request.app.state.price_service)
    wellbeing_svc = WellbeingService(session)
    return await wellbeing_svc.assess(
        user_id=DEFAULT_USER_ID,
        conversation_id=conversation_id,
        analytics_service=analytics_svc,
    )
