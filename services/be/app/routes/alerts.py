from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.alert import Alert
from app.seed import DEFAULT_USER_ID
from app.services.alert_detector import AlertDetectorService
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def get_active_alerts(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Alert)
        .where(Alert.user_id == DEFAULT_USER_ID)
        .where(Alert.dismissed == False)  # noqa: E712
        .order_by(Alert.created_at.desc())
    )
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "type": a.type,
            "severity": a.severity,
            "title": a.title,
            "description": a.description,
            "context": a.context,
            "suggestion": a.suggestion,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


@router.get("/risk-metrics")
async def get_risk_metrics(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    analytics_svc = AnalyticsService(session, request.app.state.price_service)
    alert_svc = AlertDetectorService(session, analytics_svc)
    return await alert_svc.calculate_risk_metrics(DEFAULT_USER_ID)


@router.patch("/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.dismissed = True
    await session.commit()
    return {"status": "dismissed"}
