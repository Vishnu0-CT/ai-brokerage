from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session_factory, engine, Base
from app.seed import seed_default_user, seed_portfolio_config, seed_demo_data, seed_trade_history, seed_watchlist, seed_portfolio_snapshots, DEFAULT_USER_ID
from app.services.price import PriceService, SimulatedPriceStream
from app.services.price_monitor import PriceMonitor
from app.services.margin import MarginService
from app.services.scheduler import SchedulerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Indian market seed prices (from tradeai niftyHistoricalData)
SEED_PRICES = {
    # Indices
    "NIFTY": 25496.55,
    "BANKNIFTY": 61187.70,
    "FINNIFTY": 28309.85,
    
    # Stocks - Top Weightage
    "RELIANCE": 1423.90,
    "HDFCBANK": 915.60,
    "INFY": 1407.30,
    "TCS": 2738.80,
    "ICICIBANK": 1401.80,
    "SBIN": 1224.90,
    "TATAMOTORS": 735.00,
    
    # Banking & Finance
    "AXISBANK": 1387.10,
    "KOTAKBANK": 428.90,
    "BAJFINANCE": 1017.05,
    
    # IT Sector
    "WIPRO": 216.76,
    "HCLTECH": 1489.30,
    "TECHM": 1529.30,
    
    # Auto Sector
    "M&M": 3474.10,
    "MARUTI": 12800.00,
    "BAJAJ-AUTO": 9759.50,
    
    # Pharma Sector
    "SUNPHARMA": 1820.00,
    "DRREDDY": 1265.90,
    "CIPLA": 1346.20,
    
    # FMCG Sector
    "ITC": 325.50,
    "HINDUNILVR": 2279.30,
    "BRITANNIA": 5200.00,
    
    # Energy Sector
    "ONGC": 274.65,
    "BPCL": 320.00,
    "POWERGRID": 298.50,
    
    # Metals & Mining
    "TATASTEEL": 203.30,
    "HINDALCO": 890.30,
    "JSWSTEEL": 960.00,
    
    # Telecom
    "BHARTIARTL": 2029.60,
    
    # Conglomerates & Infrastructure
    "ADANIENT": 2204.90,
    "LT": 3650.00,
    "ULTRACEMCO": 12943.00,
    
    # Additional Popular Stocks
    "ASIANPAINT": 2439.20,
    "NTPC": 370.00,
    "COALINDIA": 421.60,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    # 1. Create tables (dev shortcut -- use alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Seed default user and portfolio
    user = await seed_default_user()
    await seed_portfolio_config(user.id)
    logger.info(f"Default user: {user.name} ({user.id})")

    # 3. Price service
    stream = SimulatedPriceStream(
        seed_prices=SEED_PRICES,
        tick_interval=settings.price_tick_interval_seconds,
    )
    price_service = PriceService(stream=stream)

    # 4. Scheduler
    scheduler_service = SchedulerService(
        session_factory=async_session_factory,
        price_service=price_service,
    )
    await scheduler_service.start()

    # 5. Price monitor
    price_monitor = PriceMonitor(
        stream=stream,
        session_factory=async_session_factory,
        price_service=price_service,
    )

    # 6. Start price stream
    await price_service.start()

    for symbol in SEED_PRICES:
        stream.add_symbol(symbol)

    # 7. Store on app.state
    app.state.price_service = price_service
    app.state.price_monitor = price_monitor
    app.state.scheduler_service = scheduler_service
    app.state.session_factory = async_session_factory
    app.state.margin_service = MarginService

    # 8. Seed demo data
    await seed_demo_data(user.id)

    # 8a. Seed enhanced trade history with behavioral patterns
    trade_count = await seed_trade_history(user.id)
    if trade_count > 0:
        logger.info(f"Trade history seeded: {trade_count} trades with behavioral patterns")

    # 8b. Seed default watchlist
    watchlist_count = await seed_watchlist(user.id)
    if watchlist_count > 0:
        logger.info(f"Watchlist seeded: {watchlist_count} items")

    # 8c. Seed portfolio snapshots for dashboard chart
    snapshot_count = await seed_portfolio_snapshots(user.id)
    if snapshot_count > 0:
        logger.info(f"Portfolio snapshots seeded: {snapshot_count} snapshots")

    # 9. Load active conditions from DB
    async with async_session_factory() as session:
        from app.services.condition import ConditionService
        from app.services.order import OrderService

        condition_svc = ConditionService(
            session=session,
            price_service=price_service,
            order_service=OrderService(session=session),
        )

        active = await condition_svc.get_active()
        await price_monitor.load_active_conditions(active)
        await scheduler_service.load_time_conditions(active)
        await session.commit()
        logger.info(f"Loaded {len(active)} active conditions")

    # 10. Schedule portfolio snapshots
    async def take_snapshot():
        async with async_session_factory() as session:
            from app.services.portfolio import PortfolioService
            svc = PortfolioService(session, price_service)
            await svc.take_snapshot(DEFAULT_USER_ID)
            logger.info("Portfolio snapshot taken")

    await scheduler_service.schedule_periodic(
        take_snapshot,
        interval_seconds=settings.snapshot_interval_minutes * 60,
        job_id="portfolio_snapshot",
    )

    # 11. Schedule periodic alert detection (every 5 min)
    async def run_alert_detection():
        async with async_session_factory() as session:
            from app.services.analytics import AnalyticsService
            from app.services.alert_detector import AlertDetectorService
            analytics_svc = AnalyticsService(session, price_service)
            alert_svc = AlertDetectorService(session, analytics_svc)
            alerts = await alert_svc.evaluate_all(DEFAULT_USER_ID)
            if alerts:
                logger.info(f"Alert detection: {len(alerts)} new alerts")

    await scheduler_service.schedule_periodic(
        run_alert_detection,
        interval_seconds=300,
        job_id="alert_detection",
    )

    logger.info("Startup complete")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await price_service.stop()
    await scheduler_service.stop()
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(title="AI Brokerage BE", lifespan=lifespan)

# Exception handlers
from app.middleware import register_exception_handlers
register_exception_handlers(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routes.health import router as health_router
from app.routes.user import router as user_router
from app.routes.portfolio import router as portfolio_router
from app.routes.orders import router as orders_router
from app.routes.market import router as market_router
from app.routes.conversations import router as conversations_router
from app.routes.notifications import router as notifications_router
from app.routes.alerts import router as alerts_router
from app.routes.analytics import router as analytics_router
from app.routes.wellbeing import router as wellbeing_router
from app.routes.trades import router as trades_router
from app.routes.strategies import router as strategies_router
from app.routes.positions import router as positions_router
from app.routes.watchlist import router as watchlist_router
from app.routes.watchlist import option_chain_router, expiry_router
from app.routes.yahoo_finance import router as yahoo_finance_router

app.include_router(health_router)
app.include_router(user_router)
app.include_router(portfolio_router)
app.include_router(orders_router)
app.include_router(market_router)
app.include_router(conversations_router)
app.include_router(notifications_router)
app.include_router(alerts_router)
app.include_router(analytics_router)
app.include_router(wellbeing_router)
app.include_router(trades_router)
app.include_router(strategies_router)
app.include_router(positions_router)
app.include_router(watchlist_router)
app.include_router(option_chain_router)
app.include_router(expiry_router)
app.include_router(yahoo_finance_router)
