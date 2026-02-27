"""
Market Data Service

Manages watchlist, option chain generation, and expiry dates.
"""
from __future__ import annotations

import hashlib
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import WatchlistItem


# Default watchlist items with Indian market instruments
DEFAULT_WATCHLIST = [
    # Indices
    {
        "symbol": "NIFTY",
        "name": "NIFTY 50",
        "instrument_type": "INDEX",
        "lot_size": 25,  # Revised lot size
        "tick_size": 0.05,
        "base_price": 25496.55,
    },
    {
        "symbol": "BANKNIFTY",
        "name": "BANK NIFTY",
        "instrument_type": "INDEX",
        "lot_size": 15,  # Revised lot size
        "tick_size": 0.05,
        "base_price": 61187.70,
    },
    {
        "symbol": "FINNIFTY",
        "name": "FIN NIFTY",
        "instrument_type": "INDEX",
        "lot_size": 25,  # Revised lot size
        "tick_size": 0.05,
        "base_price": 28309.85,
    },
    # Stocks
    {
        "symbol": "RELIANCE",
        "name": "RELIANCE",
        "instrument_type": "STOCK",
        "lot_size": 250,
        "tick_size": 0.05,
        "base_price": 1423.90,
    },
    {
        "symbol": "HDFCBANK",
        "name": "HDFCBANK",
        "instrument_type": "STOCK",
        "lot_size": 550,
        "tick_size": 0.05,
        "base_price": 915.60,
    },
    {
        "symbol": "INFY",
        "name": "INFY",
        "instrument_type": "STOCK",
        "lot_size": 300,
        "tick_size": 0.05,
        "base_price": 1407.30,
    },
    {
        "symbol": "TCS",
        "name": "TCS",
        "instrument_type": "STOCK",
        "lot_size": 175,
        "tick_size": 0.05,
        "base_price": 2738.80,
    },
    {
        "symbol": "ICICIBANK",
        "name": "ICICIBANK",
        "instrument_type": "STOCK",
        "lot_size": 700,
        "tick_size": 0.05,
        "base_price": 1401.80,
    },
    {
        "symbol": "SBIN",
        "name": "SBIN",
        "instrument_type": "STOCK",
        "lot_size": 1500,
        "tick_size": 0.05,
        "base_price": 1224.90,
    },
    {
        "symbol": "TATAMOTORS",
        "name": "TATAMOTORS",
        "instrument_type": "STOCK",
        "lot_size": 575,
        "tick_size": 0.05,
        "base_price": 735.00,
    },
    # Banking & Finance
    {
        "symbol": "AXISBANK",
        "name": "AXISBANK",
        "instrument_type": "STOCK",
        "lot_size": 750,
        "tick_size": 0.05,
        "base_price": 1387.10,
    },
    {
        "symbol": "KOTAKBANK",
        "name": "KOTAKBANK",
        "instrument_type": "STOCK",
        "lot_size": 400,
        "tick_size": 0.05,
        "base_price": 428.90,
    },
    {
        "symbol": "BAJFINANCE",
        "name": "BAJFINANCE",
        "instrument_type": "STOCK",
        "lot_size": 125,
        "tick_size": 0.05,
        "base_price": 1017.05,
    },
    # IT Sector
    {
        "symbol": "WIPRO",
        "name": "WIPRO",
        "instrument_type": "STOCK",
        "lot_size": 1200,
        "tick_size": 0.05,
        "base_price": 216.76,
    },
    {
        "symbol": "HCLTECH",
        "name": "HCLTECH",
        "instrument_type": "STOCK",
        "lot_size": 400,
        "tick_size": 0.05,
        "base_price": 1489.30,
    },
    {
        "symbol": "TECHM",
        "name": "TECHM",
        "instrument_type": "STOCK",
        "lot_size": 450,
        "tick_size": 0.05,
        "base_price": 1529.30,
    },
    # Auto Sector
    {
        "symbol": "M&M",
        "name": "M&M",
        "instrument_type": "STOCK",
        "lot_size": 300,
        "tick_size": 0.05,
        "base_price": 3474.10,
    },
    {
        "symbol": "MARUTI",
        "name": "MARUTI",
        "instrument_type": "STOCK",
        "lot_size": 50,
        "tick_size": 0.05,
        "base_price": 12800.00,
    },
    {
        "symbol": "BAJAJ-AUTO",
        "name": "BAJAJ-AUTO",
        "instrument_type": "STOCK",
        "lot_size": 125,
        "tick_size": 0.05,
        "base_price": 9759.50,
    },
    # Pharma Sector
    {
        "symbol": "SUNPHARMA",
        "name": "SUNPHARMA",
        "instrument_type": "STOCK",
        "lot_size": 400,
        "tick_size": 0.05,
        "base_price": 1820.00,
    },
    {
        "symbol": "DRREDDY",
        "name": "DRREDDY",
        "instrument_type": "STOCK",
        "lot_size": 125,
        "tick_size": 0.05,
        "base_price": 1265.90,
    },
    {
        "symbol": "CIPLA",
        "name": "CIPLA",
        "instrument_type": "STOCK",
        "lot_size": 500,
        "tick_size": 0.05,
        "base_price": 1346.20,
    },
    # FMCG Sector
    {
        "symbol": "ITC",
        "name": "ITC",
        "instrument_type": "STOCK",
        "lot_size": 1600,
        "tick_size": 0.05,
        "base_price": 325.50,
    },
    {
        "symbol": "HINDUNILVR",
        "name": "HINDUNILVR",
        "instrument_type": "STOCK",
        "lot_size": 300,
        "tick_size": 0.05,
        "base_price": 2279.30,
    },
    {
        "symbol": "BRITANNIA",
        "name": "BRITANNIA",
        "instrument_type": "STOCK",
        "lot_size": 200,
        "tick_size": 0.05,
        "base_price": 5200.00,
    },
    # Energy Sector
    {
        "symbol": "ONGC",
        "name": "ONGC",
        "instrument_type": "STOCK",
        "lot_size": 2850,
        "tick_size": 0.05,
        "base_price": 274.65,
    },
    {
        "symbol": "BPCL",
        "name": "BPCL",
        "instrument_type": "STOCK",
        "lot_size": 1750,
        "tick_size": 0.05,
        "base_price": 320.00,
    },
    {
        "symbol": "POWERGRID",
        "name": "POWERGRID",
        "instrument_type": "STOCK",
        "lot_size": 2100,
        "tick_size": 0.05,
        "base_price": 298.50,
    },
    # Metals & Mining
    {
        "symbol": "TATASTEEL",
        "name": "TATASTEEL",
        "instrument_type": "STOCK",
        "lot_size": 650,
        "tick_size": 0.05,
        "base_price": 203.30,
    },
    {
        "symbol": "HINDALCO",
        "name": "HINDALCO",
        "instrument_type": "STOCK",
        "lot_size": 1200,
        "tick_size": 0.05,
        "base_price": 890.30,
    },
    {
        "symbol": "JSWSTEEL",
        "name": "JSWSTEEL",
        "instrument_type": "STOCK",
        "lot_size": 850,
        "tick_size": 0.05,
        "base_price": 960.00,
    },
    # Telecom
    {
        "symbol": "BHARTIARTL",
        "name": "BHARTIARTL",
        "instrument_type": "STOCK",
        "lot_size": 550,
        "tick_size": 0.05,
        "base_price": 2029.60,
    },
    # Conglomerates & Infrastructure
    {
        "symbol": "ADANIENT",
        "name": "ADANIENT",
        "instrument_type": "STOCK",
        "lot_size": 250,
        "tick_size": 0.05,
        "base_price": 2204.90,
    },
    {
        "symbol": "LT",
        "name": "LT",
        "instrument_type": "STOCK",
        "lot_size": 300,
        "tick_size": 0.05,
        "base_price": 3650.00,
    },
    {
        "symbol": "ULTRACEMCO",
        "name": "ULTRACEMCO",
        "instrument_type": "STOCK",
        "lot_size": 100,
        "tick_size": 0.05,
        "base_price": 12943.00,
    },
    # Additional Popular Stocks
    {
        "symbol": "ASIANPAINT",
        "name": "ASIANPAINT",
        "instrument_type": "STOCK",
        "lot_size": 300,
        "tick_size": 0.05,
        "base_price": 2439.20,
    },
    {
        "symbol": "NTPC",
        "name": "NTPC",
        "instrument_type": "STOCK",
        "lot_size": 2175,
        "tick_size": 0.05,
        "base_price": 370.00,
    },
    {
        "symbol": "COALINDIA",
        "name": "COALINDIA",
        "instrument_type": "STOCK",
        "lot_size": 1800,
        "tick_size": 0.05,
        "base_price": 421.60,
    },
]

# Strike intervals for different instruments
STRIKE_INTERVALS = {
    # Indices
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    # Original Stocks
    "RELIANCE": 10,
    "HDFCBANK": 20,
    "INFY": 20,
    "TCS": 50,
    "ICICIBANK": 10,
    "SBIN": 10,
    "TATAMOTORS": 10,
    # Banking & Finance
    "AXISBANK": 10,
    "KOTAKBANK": 20,
    "BAJFINANCE": 100,
    # IT Sector
    "WIPRO": 5,
    "HCLTECH": 20,
    "TECHM": 20,
    # Auto Sector
    "M&M": 50,
    "MARUTI": 100,
    "BAJAJ-AUTO": 100,
    # Pharma Sector
    "SUNPHARMA": 20,
    "DRREDDY": 50,
    "CIPLA": 20,
    # FMCG Sector
    "ITC": 5,
    "HINDUNILVR": 20,
    "BRITANNIA": 50,
    # Energy Sector
    "ONGC": 5,
    "BPCL": 5,
    "POWERGRID": 5,
    # Metals & Mining
    "TATASTEEL": 5,
    "HINDALCO": 10,
    "JSWSTEEL": 10,
    # Telecom
    "BHARTIARTL": 20,
    # Conglomerates & Infrastructure
    "ADANIENT": 20,
    "LT": 50,
    "ULTRACEMCO": 100,
    # Additional Popular Stocks
    "ASIANPAINT": 20,
    "NTPC": 5,
    "COALINDIA": 5,
}


def _get_deterministic_noise(symbol: str, strike: int, is_call: bool) -> float:
    """
    Get deterministic noise factor based on symbol, strike, and option type.
    Returns a value between 0.95 and 1.05 for consistent pricing.
    """
    key = f"{symbol}_{strike}_{'CE' if is_call else 'PE'}"
    hash_val = int(hashlib.md5(key.encode()).hexdigest(), 16)
    # Map to range 0.95 to 1.05
    return 0.95 + (hash_val % 100) / 1000


def _calculate_option_price(
    spot: float,
    strike: int,
    is_call: bool,
    days_to_expiry: int,
    iv: float = 0.15,
    symbol: str = "",
) -> float:
    """
    Calculate option price using simplified Black-Scholes approximation.
    This is a mock implementation for realistic-looking prices.
    Uses deterministic noise for consistent pricing across calls.
    """
    # Intrinsic value
    if is_call:
        intrinsic = max(0, spot - strike)
    else:
        intrinsic = max(0, strike - spot)
    
    # Time value (simplified)
    time_factor = math.sqrt(days_to_expiry / 365)
    moneyness = abs(spot - strike) / spot
    
    # ATM options have highest time value
    atm_factor = math.exp(-moneyness * 10)
    time_value = spot * iv * time_factor * atm_factor * 0.4
    
    # Use deterministic noise for consistent pricing
    noise = _get_deterministic_noise(symbol, strike, is_call)
    
    price = (intrinsic + time_value) * noise
    return max(0.05, round(price, 2))


def _calculate_iv(spot: float, strike: int, is_call: bool, symbol: str = "") -> float:
    """Calculate implied volatility (mock) with deterministic variation."""
    moneyness = abs(spot - strike) / spot
    
    # IV smile - higher IV for OTM options
    base_iv = 0.15
    smile_factor = 1 + moneyness * 2
    
    # Use deterministic variation instead of random
    noise = _get_deterministic_noise(symbol, strike, is_call)
    # Map noise from 0.95-1.05 to 0.9-1.1
    iv_noise = 0.9 + (noise - 0.95) * 2
    
    iv = base_iv * smile_factor * iv_noise
    return round(iv * 100, 2)  # Return as percentage


def generate_option_chain(
    symbol: str,
    spot_price: float,
    lot_size: int,
    days_to_expiry: int = 3,
    num_strikes: int = 21,
) -> list[dict]:
    """
    Generate realistic option chain with:
    - 21 strikes (10 ITM, ATM, 10 OTM)
    - Call and Put data for each strike
    """
    strike_interval = STRIKE_INTERVALS.get(symbol, 50)
    
    # Find ATM strike
    atm_strike = round(spot_price / strike_interval) * strike_interval
    
    # Generate strikes with randomness
    half_strikes = num_strikes // 2
    strikes = []

    # Use deterministic randomness based on symbol and expiry
    seed_hash = int(hashlib.md5(f"{symbol}_{days_to_expiry}".encode()).hexdigest()[:8], 16)

    for i in range(-half_strikes, half_strikes + 1):
        # Add random variation to strike interval (±20% of interval)
        # Uses deterministic variation based on position
        variation_seed = (seed_hash + i) % 100
        # Map to range -0.2 to +0.2 (±20%)
        variation_factor = (variation_seed / 100 - 0.5) * 0.4

        # Apply variation to the interval
        adjusted_interval = strike_interval * (1 + variation_factor)
        strike = atm_strike + (i * adjusted_interval)

        # Round to nearest tick (typically 0.05 or whole number for indices)
        if strike_interval >= 10:
            strike = round(strike)  # Round to whole number for larger intervals
        else:
            strike = round(strike / 0.05) * 0.05  # Round to nearest 0.05

        strikes.append(strike)
    
    option_chain = []
    
    for strike in strikes:
        # Calculate call data with deterministic pricing
        call_price = _calculate_option_price(spot_price, strike, True, days_to_expiry, symbol=symbol)
        call_iv = _calculate_iv(spot_price, strike, True, symbol=symbol)
        # Use deterministic OI/volume based on strike and symbol
        call_hash = int(hashlib.md5(f"{symbol}_{strike}_CE".encode()).hexdigest(), 16)
        call_oi = 10000 + (call_hash % 490000)
        call_volume = 1000 + (call_hash % 49000)
        call_change = -10 + (call_hash % 2000) / 100  # Range: -10 to 10
        
        # Calculate put data with deterministic pricing
        put_price = _calculate_option_price(spot_price, strike, False, days_to_expiry, symbol=symbol)
        put_iv = _calculate_iv(spot_price, strike, False, symbol=symbol)
        # Use deterministic OI/volume based on strike and symbol
        put_hash = int(hashlib.md5(f"{symbol}_{strike}_PE".encode()).hexdigest(), 16)
        put_oi = 10000 + (put_hash % 490000)
        put_volume = 1000 + (put_hash % 49000)
        put_change = -10 + (put_hash % 2000) / 100  # Range: -10 to 10
        
        # Bid-ask spread (tighter for ATM)
        moneyness = abs(spot_price - strike) / spot_price
        spread_factor = 1 + moneyness * 5
        
        call_spread = max(0.05, call_price * 0.01 * spread_factor)
        put_spread = max(0.05, put_price * 0.01 * spread_factor)
        
        option_chain.append({
            "strike": strike,
            "call": {
                "ltp": call_price,
                "bid": round(call_price - call_spread / 2, 2),
                "ask": round(call_price + call_spread / 2, 2),
                "oi": call_oi,
                "iv": call_iv,
                "volume": call_volume,
                "change": round(call_change, 2),
                "change_percent": round(call_change / call_price * 100 if call_price > 0 else 0, 2),
            },
            "put": {
                "ltp": put_price,
                "bid": round(put_price - put_spread / 2, 2),
                "ask": round(put_price + put_spread / 2, 2),
                "oi": put_oi,
                "iv": put_iv,
                "volume": put_volume,
                "change": round(put_change, 2),
                "change_percent": round(put_change / put_price * 100 if put_price > 0 else 0, 2),
            },
        })
    
    return option_chain


def get_expiry_dates(weeks: int = 4) -> list[dict]:
    """Return next N Thursday expiry dates."""
    expiries = []
    today = datetime.now(timezone.utc).date()
    
    # Find next Thursday
    days_until_thursday = (3 - today.weekday()) % 7
    if days_until_thursday == 0 and datetime.now(timezone.utc).hour >= 15:
        # If it's Thursday after market close, go to next week
        days_until_thursday = 7
    
    next_thursday = today + timedelta(days=days_until_thursday)
    
    for i in range(weeks):
        expiry_date = next_thursday + timedelta(weeks=i)
        expiries.append({
            "date": expiry_date.strftime("%Y-%m-%d"),
            "label": expiry_date.strftime("%d %b"),
            "is_weekly": True,
            "is_monthly": expiry_date.month != (expiry_date + timedelta(days=7)).month,
        })
    
    return expiries


class MarketDataService:
    """Service for market data, watchlist, and option chains."""
    
    def __init__(self, session: AsyncSession, price_service: Any = None) -> None:
        self._session = session
        self._price_service = price_service
        self._price_cache: dict[str, dict] = {}
    
    async def seed_default_watchlist(self, user_id: uuid.UUID) -> int:
        """Seed default watchlist items for a user."""
        # Check if user already has watchlist items
        result = await self._session.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user_id).limit(1)
        )
        if result.scalar_one_or_none():
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
            self._session.add(watchlist_item)
            
            # Cache base price
            self._price_cache[item["symbol"]] = {
                "price": item["base_price"],
                "open": item["base_price"] * random.uniform(0.995, 1.005),
                "high": item["base_price"] * random.uniform(1.005, 1.015),
                "low": item["base_price"] * random.uniform(0.985, 0.995),
                "change": random.uniform(-1.5, 1.5),
            }
        
        await self._session.commit()
        return len(DEFAULT_WATCHLIST)
    
    async def search_tickers(self, user_id: uuid.UUID, query: str, limit: int = 10) -> list[dict]:
        """Search watchlist items by symbol or name using substring match."""
        pattern = f"%{query.upper()}%"
        result = await self._session.execute(
            select(WatchlistItem)
            .where(
                WatchlistItem.user_id == user_id,
                WatchlistItem.symbol.ilike(pattern) | WatchlistItem.name.ilike(pattern),
            )
            .order_by(WatchlistItem.display_order)
            .limit(limit)
        )
        items = result.scalars().all()
        return [
            {
                "symbol": item.symbol,
                "name": item.name,
                "type": item.instrument_type,
                "lot_size": item.lot_size,
            }
            for item in items
        ]

    async def get_watchlist(self, user_id: uuid.UUID) -> list[dict]:
        """Get user's watchlist with current prices."""
        result = await self._session.execute(
            select(WatchlistItem)
            .where(WatchlistItem.user_id == user_id)
            .order_by(WatchlistItem.display_order)
        )
        items = result.scalars().all()
        
        watchlist = []
        for item in items:
            price_data = await self._get_price_data(item.symbol)
            
            watchlist.append({
                "id": str(item.id),
                "symbol": item.symbol,
                "name": item.name,
                "type": item.instrument_type,
                "lot_size": item.lot_size,
                "tick_size": float(item.tick_size),
                "price": price_data["price"],
                "change": price_data["change"],
                "change_percent": price_data["change_percent"],
                "high": price_data["high"],
                "low": price_data["low"],
                "open": price_data["open"],
            })
        
        return watchlist
    
    async def add_to_watchlist(
        self,
        user_id: uuid.UUID,
        symbol: str,
        name: str,
        instrument_type: str,
        lot_size: int,
        tick_size: float = 0.05,
    ) -> dict:
        """Add an item to the watchlist."""
        # Get max display order
        result = await self._session.execute(
            select(WatchlistItem)
            .where(WatchlistItem.user_id == user_id)
            .order_by(WatchlistItem.display_order.desc())
            .limit(1)
        )
        last_item = result.scalar_one_or_none()
        display_order = (last_item.display_order + 1) if last_item else 0
        
        item = WatchlistItem(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol=symbol,
            name=name,
            instrument_type=instrument_type,
            lot_size=lot_size,
            tick_size=tick_size,
            display_order=display_order,
        )
        
        self._session.add(item)
        await self._session.commit()
        await self._session.refresh(item)
        
        return {
            "id": str(item.id),
            "symbol": item.symbol,
            "name": item.name,
            "type": item.instrument_type,
            "lot_size": item.lot_size,
            "tick_size": float(item.tick_size),
        }
    
    async def remove_from_watchlist(self, item_id: uuid.UUID) -> bool:
        """Remove an item from the watchlist."""
        result = await self._session.execute(
            select(WatchlistItem).where(WatchlistItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        await self._session.delete(item)
        await self._session.commit()
        return True
    
    async def get_option_chain(
        self,
        symbol: str,
        expiry: str | None = None,
    ) -> dict:
        """Get option chain for a symbol."""
        # Get spot price
        price_data = await self._get_price_data(symbol)
        spot_price = price_data["price"]
        
        # Get lot size
        lot_size = next(
            (item["lot_size"] for item in DEFAULT_WATCHLIST if item["symbol"] == symbol),
            50
        )
        
        # Calculate days to expiry
        if expiry:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            days_to_expiry = (expiry_date - datetime.now(timezone.utc).date()).days
        else:
            # Use next expiry
            expiries = get_expiry_dates(1)
            expiry = expiries[0]["date"]
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            days_to_expiry = (expiry_date - datetime.now(timezone.utc).date()).days
        
        days_to_expiry = max(1, days_to_expiry)
        
        # Generate option chain
        strikes = generate_option_chain(symbol, spot_price, lot_size, days_to_expiry)
        
        return {
            "symbol": symbol,
            "spot_price": spot_price,
            "expiry": expiry,
            "lot_size": lot_size,
            "strikes": strikes,
        }
    
    def get_expiry_dates(self, weeks: int = 4) -> list[dict]:
        """Get upcoming expiry dates."""
        return get_expiry_dates(weeks)
    
    async def _get_price_data(self, symbol: str) -> dict:
        """Get price data for a symbol."""
        # Try to get from price service first
        if self._price_service:
            try:
                tick = await self._price_service.get_price(symbol)
                if tick:
                    return {
                        "price": tick.price,
                        "open": tick.price * 0.998,
                        "high": tick.high,
                        "low": tick.low,
                        "change": tick.price * random.uniform(-0.02, 0.02),
                        "change_percent": random.uniform(-2, 2),
                    }
            except Exception:
                pass
        
        # Fall back to cache or default
        if symbol in self._price_cache:
            cached = self._price_cache[symbol]
            # Add some price movement
            movement = random.uniform(-0.002, 0.002)
            new_price = cached["price"] * (1 + movement)
            
            return {
                "price": round(new_price, 2),
                "open": cached["open"],
                "high": max(cached["high"], new_price),
                "low": min(cached["low"], new_price),
                "change": round(new_price - cached["open"], 2),
                "change_percent": round((new_price - cached["open"]) / cached["open"] * 100, 2),
            }
        
        # Find in default watchlist
        for item in DEFAULT_WATCHLIST:
            if item["symbol"] == symbol:
                base_price = item["base_price"]
                movement = random.uniform(-0.01, 0.01)
                price = base_price * (1 + movement)
                
                return {
                    "price": round(price, 2),
                    "open": round(base_price * 0.998, 2),
                    "high": round(price * 1.01, 2),
                    "low": round(price * 0.99, 2),
                    "change": round(price - base_price, 2),
                    "change_percent": round(movement * 100, 2),
                }
        
        # Default fallback
        return {
            "price": 100.0,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "change": 0.0,
            "change_percent": 0.0,
        }
