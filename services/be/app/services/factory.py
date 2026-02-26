from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.alert_detector import AlertDetectorService
from app.services.analytics import AnalyticsService
from app.services.condition import ConditionService
from app.services.margin import MarginService
from app.services.order import OrderService
from app.services.portfolio import PortfolioService
from app.services.wellbeing import WellbeingService


@dataclass
class RequestServices:
    portfolio: PortfolioService
    order: OrderService
    condition: ConditionService
    analytics: AnalyticsService
    margin: MarginService
    alert_detector: AlertDetectorService
    wellbeing: WellbeingService


def create_request_services(
    session: AsyncSession,
    app_state: Any,
    user_id: uuid.UUID,
) -> RequestServices:
    """Wire up all per-request services and return them as a bundle."""
    portfolio_svc = PortfolioService(session, app_state.price_service)
    margin_svc = MarginService(session)
    order_svc = OrderService(session, margin_service=margin_svc)
    condition_svc = ConditionService(
        session, app_state.price_service, order_svc, portfolio_svc,
        price_monitor=app_state.price_monitor,
        scheduler_service=app_state.scheduler_service,
    )
    analytics_svc = AnalyticsService(session, app_state.price_service)
    alert_detector_svc = AlertDetectorService(session, analytics_svc)
    wellbeing_svc = WellbeingService(session)

    return RequestServices(
        portfolio=portfolio_svc,
        order=order_svc,
        condition=condition_svc,
        analytics=analytics_svc,
        margin=margin_svc,
        alert_detector=alert_detector_svc,
        wellbeing=wellbeing_svc,
    )
