from __future__ import annotations

import asyncio
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models.order import Transaction
from app.models.portfolio import Holding, PortfolioConfig
from app.models.user import User

DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
INITIAL_CASH = Decimal("1400000")  # 14 lakh starting capital


async def seed_default_user() -> User:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == DEFAULT_USER_ID))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(id=DEFAULT_USER_ID, name=settings.default_user_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def seed_portfolio_config(user_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        if result.scalar_one_or_none() is None:
            config = PortfolioConfig(
                user_id=user_id,
                initial_cash=INITIAL_CASH,
                current_cash=INITIAL_CASH,
                daily_loss_limit=Decimal("25000"),
            )
            session.add(config)
            await session.commit()


# Indian F&O demo holdings (from tradeai mockPortfolio)
DEMO_HOLDINGS = [
    {"symbol": "NIFTY", "side": "long", "quantity": Decimal("300"), "avg_price": Decimal("26200.00")},
    {"symbol": "BANKNIFTY", "side": "short", "quantity": Decimal("75"), "avg_price": Decimal("58200.00")},
    {"symbol": "RELIANCE", "side": "long", "quantity": Decimal("100"), "avg_price": Decimal("1280.00")},
    {"symbol": "INFY", "side": "long", "quantity": Decimal("200"), "avg_price": Decimal("1550.00")},
    {"symbol": "TCS", "side": "long", "quantity": Decimal("50"), "avg_price": Decimal("3800.00")},
]

# Time-of-day trading patterns (from tradeai mockTradeHistory)
TIME_PATTERNS = {
    "morning": {"win_rate": 0.58, "avg_hold_mins": 25},    # 9:15-10:30
    "midday": {"win_rate": 0.48, "avg_hold_mins": 45},     # 10:30-13:00
    "afternoon": {"win_rate": 0.38, "avg_hold_mins": 35},  # 13:00-15:30
}

DAY_PATTERNS = {
    0: {"win_rate": 0.52, "trade_factor": 1.0},  # Monday
    1: {"win_rate": 0.55, "trade_factor": 1.2},  # Tuesday
    2: {"win_rate": 0.58, "trade_factor": 1.1},  # Wednesday
    3: {"win_rate": 0.45, "trade_factor": 1.4},  # Thursday (expiry)
    4: {"win_rate": 0.50, "trade_factor": 0.9},  # Friday
}

TRADE_SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "INFY", "TCS"]
TRADE_PRICES = {
    "NIFTY": 26400.0,
    "BANKNIFTY": 57550.0,
    "RELIANCE": 1280.0,
    "INFY": 1550.0,
    "TCS": 3800.0,
}
LOT_SIZES = {
    "NIFTY": 50,
    "BANKNIFTY": 25,
    "RELIANCE": 1,
    "INFY": 1,
    "TCS": 1,
}


def _get_time_period(hour: int, minute: int) -> str:
    total_mins = hour * 60 + minute
    if total_mins < 630:  # before 10:30
        return "morning"
    elif total_mins < 780:  # before 13:00
        return "midday"
    return "afternoon"


async def seed_demo_data(user_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(Holding).where(Holding.user_id == user_id))
        if result.scalars().first() is not None:
            return  # already seeded

        # Seed holdings
        for h in DEMO_HOLDINGS:
            holding = Holding(user_id=user_id, **h)
            session.add(holding)

            txn = Transaction(
                user_id=user_id,
                symbol=h["symbol"],
                side="sell" if h["side"] == "short" else "buy",
                quantity=h["quantity"],
                price=h["avg_price"],
            )
            session.add(txn)

        total_invested = sum(h["quantity"] * h["avg_price"] for h in DEMO_HOLDINGS)
        config_result = await session.execute(
            select(PortfolioConfig).where(PortfolioConfig.user_id == user_id)
        )
        config = config_result.scalar_one()
        config.current_cash -= total_invested

        # Seed trade history (250+ trades over 30 days)
        now = datetime.now(timezone.utc)
        for day_offset in range(30, 0, -1):
            day = now - timedelta(days=day_offset)
            weekday = day.weekday()
            if weekday >= 5:  # skip weekends
                continue

            day_pattern = DAY_PATTERNS.get(weekday, DAY_PATTERNS[2])
            num_trades = int(8 + random.random() * 10 * day_pattern["trade_factor"])

            for _ in range(num_trades):
                symbol = random.choice(TRADE_SYMBOLS)
                base_price = TRADE_PRICES[symbol]
                lot_size = LOT_SIZES[symbol]

                hour = 9 + int(random.random() * 6)
                minute = int(random.random() * 60)
                time_period = _get_time_period(hour, minute)
                time_pattern = TIME_PATTERNS[time_period]

                combined_wr = (time_pattern["win_rate"] + day_pattern["win_rate"]) / 2
                is_win = random.random() < combined_wr

                noise = random.gauss(0, base_price * 0.02)
                entry_price = base_price + noise

                if is_win:
                    exit_price = entry_price * (1 + random.uniform(0.005, 0.025))
                else:
                    exit_price = entry_price * (1 - random.uniform(0.005, 0.018))

                qty = Decimal(str(lot_size * random.choice([1, 1, 1, 2])))
                trade_time = day.replace(hour=hour, minute=minute, second=0, microsecond=0)

                # Buy
                buy_txn = Transaction(
                    user_id=user_id,
                    symbol=symbol,
                    side="buy",
                    quantity=qty,
                    price=Decimal(str(round(entry_price, 2))),
                    created_at=trade_time,
                )
                session.add(buy_txn)

                # Sell
                hold_mins = int(time_pattern["avg_hold_mins"] * (0.5 + random.random()))
                sell_time = trade_time + timedelta(minutes=hold_mins)

                sell_txn = Transaction(
                    user_id=user_id,
                    symbol=symbol,
                    side="sell",
                    quantity=qty,
                    price=Decimal(str(round(exit_price, 2))),
                    created_at=sell_time,
                )
                session.add(sell_txn)

        await session.commit()


async def seed_trade_history(user_id: uuid.UUID) -> int:
    """Seed enhanced trade history with behavioral patterns."""
    from app.models.trade import Trade
    from app.services.trade_history import generate_trade_history
    
    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(select(Trade).where(Trade.user_id == user_id).limit(1))
        if result.scalar_one_or_none() is not None:
            return 0  # Already seeded
        
        # Generate trade history with behavioral patterns
        trades_data = generate_trade_history(user_id, days=65)
        
        for trade_data in trades_data:
            trade = Trade(
                id=uuid.uuid4(),
                user_id=trade_data["user_id"],
                date=trade_data["date"],
                time=trade_data["time"],
                instrument=trade_data["instrument"],
                trade_type=trade_data["trade_type"],
                entry_price=Decimal(str(trade_data["entry_price"])),
                exit_price=Decimal(str(trade_data["exit_price"])),
                quantity=trade_data["quantity"],
                pnl=Decimal(str(trade_data["pnl"])),
                pnl_percent=Decimal(str(trade_data["pnl_percent"])),
                hold_time_minutes=trade_data["hold_time_minutes"],
                strategy=trade_data["strategy"],
                tags=trade_data["tags"],
                notes=trade_data["notes"],
                is_revenge_trade=trade_data["is_revenge_trade"],
                is_overtrade=trade_data["is_overtrade"],
                is_tilt_trade=trade_data["is_tilt_trade"],
            )
            session.add(trade)
        
        await session.commit()
        return len(trades_data)


async def seed_watchlist(user_id: uuid.UUID) -> int:
    """Seed default watchlist items."""
    from app.models.watchlist import WatchlistItem
    from app.services.market_data import DEFAULT_WATCHLIST
    
    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user_id).limit(1)
        )
        if result.scalar_one_or_none() is not None:
            return 0  # Already seeded
        
        for i, item in enumerate(DEFAULT_WATCHLIST):
            watchlist_item = WatchlistItem(
                id=uuid.uuid4(),
                user_id=user_id,
                symbol=item["symbol"],
                name=item["name"],
                instrument_type=item["instrument_type"],
                lot_size=item["lot_size"],
                tick_size=item["tick_size"],
                display_order=i,
            )
            session.add(watchlist_item)
        
        await session.commit()
        return len(DEFAULT_WATCHLIST)


async def main() -> None:
    user = await seed_default_user()
    print(f"Default user: {user.name} ({user.id})")
    await seed_portfolio_config(user.id)
    print(f"Portfolio config seeded: {INITIAL_CASH} starting cash")
    
    # Seed enhanced trade history
    trade_count = await seed_trade_history(user.id)
    if trade_count > 0:
        print(f"Trade history seeded: {trade_count} trades with behavioral patterns")
    
    # Seed watchlist
    watchlist_count = await seed_watchlist(user.id)
    if watchlist_count > 0:
        print(f"Watchlist seeded: {watchlist_count} items")


if __name__ == "__main__":
    asyncio.run(main())
