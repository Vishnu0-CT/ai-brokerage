"""
Strategy Service

Manages trading strategies with CRUD operations, AI parsing, and templates.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy import Strategy, StrategyVersion


# Strategy Templates - 18 total, 6 categories
STRATEGY_TEMPLATES = [
    # Category 1: Momentum Strategies
    {
        "id": "momentum_rsi_bounce",
        "category": "momentum",
        "title": "RSI Oversold Bounce",
        "description": "Buy when RSI crosses above 30, indicating oversold conditions with potential reversal",
        "template": "Buy NIFTY CE when RSI(14) crosses above 30 on 15-min chart and price is above VWAP. Exit when RSI crosses above 70 or price hits 2% profit. Stop loss at 1.5%.",
    },
    {
        "id": "momentum_macd_crossover",
        "category": "momentum",
        "title": "MACD Crossover",
        "description": "Enter on MACD line crossing above signal line with histogram turning positive",
        "template": "Buy NIFTY CE when MACD line crosses above signal line on 15-min chart and histogram is positive. Exit when MACD crosses below signal or 3% profit. Stop loss at 2%.",
    },
    {
        "id": "momentum_volume_breakout",
        "category": "momentum",
        "title": "Volume Breakout",
        "description": "Enter on price breakout with volume surge above 2x average",
        "template": "Buy NIFTY CE when price breaks above previous day high with volume greater than 2x 20-period average. Exit at 2.5% profit or end of day. Stop loss at 1.5%.",
    },
    
    # Category 2: Mean Reversion
    {
        "id": "reversion_bb_squeeze",
        "category": "mean_reversion",
        "title": "Bollinger Band Squeeze",
        "description": "Enter when price touches lower Bollinger Band with RSI oversold",
        "template": "Buy NIFTY CE when price touches lower Bollinger Band(20,2) and RSI(14) is below 35. Exit when price reaches middle band or 2% profit. Stop loss at 1.5%.",
    },
    {
        "id": "reversion_rsi_overbought",
        "category": "mean_reversion",
        "title": "RSI Overbought Fade",
        "description": "Sell when RSI reaches extreme overbought levels above 75",
        "template": "Buy NIFTY PE when RSI(14) crosses below 75 from above on 15-min chart. Exit when RSI reaches 50 or 2% profit. Stop loss at 1.5%.",
    },
    {
        "id": "reversion_vwap",
        "category": "mean_reversion",
        "title": "VWAP Reversion",
        "description": "Trade price returning to VWAP after significant deviation",
        "template": "Buy NIFTY CE when price is 1% below VWAP and RSI is below 40. Exit when price reaches VWAP or 1.5% profit. Stop loss at 1%.",
    },
    
    # Category 3: Trend Following
    {
        "id": "trend_supertrend",
        "category": "trend_following",
        "title": "SuperTrend Strategy",
        "description": "Follow SuperTrend indicator for trend direction",
        "template": "Buy NIFTY CE when SuperTrend(10,3) turns green on 15-min chart and price is above 20 EMA. Exit when SuperTrend turns red or 3% profit. Trailing stop at 1.5%.",
    },
    {
        "id": "trend_ma_crossover",
        "category": "trend_following",
        "title": "Moving Average Crossover",
        "description": "Enter on 9 EMA crossing above 21 EMA",
        "template": "Buy NIFTY CE when 9 EMA crosses above 21 EMA on 15-min chart. Exit when 9 EMA crosses below 21 EMA or 2.5% profit. Stop loss at 2%.",
    },
    {
        "id": "trend_adx_strength",
        "category": "trend_following",
        "title": "ADX Trend Strength",
        "description": "Enter strong trends when ADX is above 25",
        "template": "Buy NIFTY CE when ADX(14) is above 25 and +DI is above -DI on 15-min chart. Exit when ADX falls below 20 or 3% profit. Stop loss at 2%.",
    },
    
    # Category 4: Intraday Scalping
    {
        "id": "scalp_orb",
        "category": "scalping",
        "title": "Opening Range Breakout",
        "description": "Trade breakout of first 15-minute range",
        "template": "Buy NIFTY CE when price breaks above first 15-min candle high after 9:30 AM. Exit at 1% profit or 10:30 AM. Stop loss at first candle low.",
    },
    {
        "id": "scalp_vwap",
        "category": "scalping",
        "title": "VWAP Scalp",
        "description": "Quick scalps around VWAP with tight stops",
        "template": "Buy NIFTY CE when price bounces off VWAP with bullish candle on 5-min chart. Exit at 0.5% profit or 10 minutes. Stop loss at 0.3%.",
    },
    {
        "id": "scalp_gap_fill",
        "category": "scalping",
        "title": "Gap Fill Strategy",
        "description": "Trade gap fills in the first hour",
        "template": "Buy NIFTY PE when market gaps up more than 0.5% at open. Exit when gap is 50% filled or 30 minutes. Stop loss at 0.5%.",
    },
    
    # Category 5: Options Selling
    {
        "id": "selling_iron_condor",
        "category": "options_selling",
        "title": "Iron Condor Weekly",
        "description": "Sell OTM call and put spreads for weekly expiry",
        "template": "Sell NIFTY Iron Condor with strikes 500 points away from spot on Monday. Exit at 50% profit or Thursday 2 PM. Max loss at 100% of premium.",
    },
    {
        "id": "selling_strangle",
        "category": "options_selling",
        "title": "Strangle Selling",
        "description": "Sell OTM strangle when IV is high",
        "template": "Sell NIFTY strangle with delta 0.15 when India VIX is above 15. Exit at 50% profit or 2 days before expiry. Stop loss at 100% of premium.",
    },
    {
        "id": "selling_covered_call",
        "category": "options_selling",
        "title": "Covered Call",
        "description": "Sell calls against long futures position",
        "template": "Sell NIFTY CE at 200 points OTM against long futures. Exit at 80% profit or expiry. Roll if price approaches strike.",
    },
    
    # Category 6: Event Based
    {
        "id": "event_earnings",
        "category": "event_based",
        "title": "Earnings Momentum",
        "description": "Trade stock options around earnings announcements",
        "template": "Buy RELIANCE CE/PE based on earnings surprise direction. Enter after results, exit at 5% profit or next day. Stop loss at 3%.",
    },
    {
        "id": "event_expiry",
        "category": "event_based",
        "title": "Expiry Day Strategy",
        "description": "Trade weekly expiry volatility on Thursday",
        "template": "Buy NIFTY ATM straddle at 2 PM on expiry day. Exit at 2% profit or 3:15 PM. Stop loss at 1.5%.",
    },
    {
        "id": "event_news_fade",
        "category": "event_based",
        "title": "News Fade",
        "description": "Fade overreaction to news events",
        "template": "Buy NIFTY CE/PE opposite to initial news reaction after 30 minutes. Exit at 1.5% profit or 2 hours. Stop loss at 1%.",
    },
]

STRATEGY_CATEGORIES = [
    {
        "id": "momentum",
        "name": "Momentum",
        "icon": "🚀",
        "color": "blue",
    },
    {
        "id": "mean_reversion",
        "name": "Mean Reversion",
        "icon": "🔄",
        "color": "purple",
    },
    {
        "id": "trend_following",
        "name": "Trend Following",
        "icon": "📈",
        "color": "green",
    },
    {
        "id": "scalping",
        "name": "Intraday Scalping",
        "icon": "⚡",
        "color": "yellow",
    },
    {
        "id": "options_selling",
        "name": "Options Selling",
        "icon": "💰",
        "color": "orange",
    },
    {
        "id": "event_based",
        "name": "Event Based",
        "icon": "📅",
        "color": "red",
    },
]


class StrategyService:
    """Service for managing trading strategies."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def create_strategy(
        self,
        user_id: uuid.UUID,
        name: str,
        description: str | None = None,
        entry_conditions: list[dict] | None = None,
        exit_conditions: list[dict] | None = None,
        stop_loss: dict | None = None,
        target: dict | None = None,
        position_size: dict | None = None,
        max_positions: int = 1,
        natural_language_input: str | None = None,
    ) -> Strategy:
        """Create a new trading strategy."""
        strategy = Strategy(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            description=description,
            status="paper_trading",
            entry_conditions=entry_conditions or [],
            exit_conditions=exit_conditions or [],
            stop_loss=stop_loss,
            target=target,
            position_size=position_size or {"type": "fixed", "value": 1},
            max_positions=max_positions,
            paper_trading_stats={
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "max_drawdown": 0.0,
                "last_trade_date": None,
            },
            natural_language_input=natural_language_input,
        )
        
        self._session.add(strategy)
        await self._session.commit()
        await self._session.refresh(strategy)
        
        # Create initial version
        await self._create_version(strategy)
        
        return strategy
    
    async def get_strategy(self, strategy_id: uuid.UUID) -> Strategy | None:
        """Get a strategy by ID."""
        result = await self._session.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        return result.scalar_one_or_none()
    
    async def get_strategies(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
    ) -> list[Strategy]:
        """Get all strategies for a user."""
        stmt = select(Strategy).where(Strategy.user_id == user_id)
        
        if status:
            stmt = stmt.where(Strategy.status == status)
        
        stmt = stmt.order_by(Strategy.updated_at.desc())
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_strategy(
        self,
        strategy_id: uuid.UUID,
        **updates: Any,
    ) -> Strategy | None:
        """Update a strategy."""
        strategy = await self.get_strategy(strategy_id)
        if not strategy:
            return None
        
        for key, value in updates.items():
            if hasattr(strategy, key) and value is not None:
                setattr(strategy, key, value)
        
        strategy.updated_at = datetime.now(timezone.utc)
        
        await self._session.commit()
        await self._session.refresh(strategy)
        
        # Create new version
        await self._create_version(strategy)
        
        return strategy
    
    async def delete_strategy(self, strategy_id: uuid.UUID) -> bool:
        """Delete a strategy."""
        strategy = await self.get_strategy(strategy_id)
        if not strategy:
            return False
        
        await self._session.delete(strategy)
        await self._session.commit()
        return True
    
    async def parse_natural_language(self, description: str) -> dict:
        """
        Parse natural language strategy description into structured format.
        
        This is a rule-based parser. In production, this would call an LLM API.
        """
        result = {
            "name": "",
            "description": description,
            "entry_conditions": [],
            "exit_conditions": [],
            "stop_loss": None,
            "target": None,
            "position_size": {"type": "fixed", "value": 1},
            "confidence": 0.0,
        }
        
        description_lower = description.lower()
        
        # Extract name from first part or generate
        if "when" in description_lower:
            name_part = description.split("when")[0].strip()
            if len(name_part) < 50:
                result["name"] = name_part.replace("Buy", "").replace("Sell", "").strip()
        
        if not result["name"]:
            result["name"] = self._generate_strategy_name(description)
        
        # Parse entry conditions
        entry_conditions = []
        
        # RSI patterns
        rsi_match = re.search(r'rsi\s*\(?(\d+)?\)?\s*(crosses?\s*(above|below)|is\s*(above|below)|[<>])\s*(\d+)', description_lower)
        if rsi_match:
            period = rsi_match.group(1) or "14"
            direction = rsi_match.group(3) or rsi_match.group(4)
            value = int(rsi_match.group(5))
            
            operator = "crosses_above" if direction == "above" else "crosses_below"
            entry_conditions.append({
                "type": "indicator",
                "indicator": f"RSI({period})",
                "operator": operator,
                "value": value,
                "timeframe": self._extract_timeframe(description),
            })
        
        # MACD patterns
        if "macd" in description_lower:
            if "crosses above signal" in description_lower or "crosses above" in description_lower:
                entry_conditions.append({
                    "type": "indicator",
                    "indicator": "MACD",
                    "operator": "crosses_above",
                    "value": "signal",
                    "timeframe": self._extract_timeframe(description),
                })
            elif "crosses below signal" in description_lower or "crosses below" in description_lower:
                entry_conditions.append({
                    "type": "indicator",
                    "indicator": "MACD",
                    "operator": "crosses_below",
                    "value": "signal",
                    "timeframe": self._extract_timeframe(description),
                })
        
        # SuperTrend patterns
        supertrend_match = re.search(r'supertrend\s*\(?(\d+)?,?\s*(\d+)?\)?\s*(turns?\s*(green|red)|is\s*(green|red|bullish|bearish))', description_lower)
        if supertrend_match:
            period = supertrend_match.group(1) or "10"
            multiplier = supertrend_match.group(2) or "3"
            direction = supertrend_match.group(4) or supertrend_match.group(5)
            
            value = "bullish" if direction in ["green", "bullish"] else "bearish"
            entry_conditions.append({
                "type": "indicator",
                "indicator": f"SuperTrend({period},{multiplier})",
                "operator": "equals",
                "value": value,
                "timeframe": self._extract_timeframe(description),
            })
        
        # EMA crossover patterns
        ema_match = re.search(r'(\d+)\s*ema\s*crosses?\s*(above|below)\s*(\d+)\s*ema', description_lower)
        if ema_match:
            fast = ema_match.group(1)
            direction = ema_match.group(2)
            slow = ema_match.group(3)
            
            entry_conditions.append({
                "type": "indicator",
                "indicator": f"EMA({fast})",
                "operator": f"crosses_{direction}",
                "value": f"EMA({slow})",
                "timeframe": self._extract_timeframe(description),
            })
        
        # Bollinger Band patterns
        if "bollinger" in description_lower or "bb" in description_lower:
            if "lower" in description_lower:
                entry_conditions.append({
                    "type": "indicator",
                    "indicator": "BollingerBand(20,2)",
                    "operator": "touches",
                    "value": "lower",
                    "timeframe": self._extract_timeframe(description),
                })
            elif "upper" in description_lower:
                entry_conditions.append({
                    "type": "indicator",
                    "indicator": "BollingerBand(20,2)",
                    "operator": "touches",
                    "value": "upper",
                    "timeframe": self._extract_timeframe(description),
                })
        
        # VWAP patterns
        if "vwap" in description_lower:
            if "above vwap" in description_lower:
                entry_conditions.append({
                    "type": "indicator",
                    "indicator": "VWAP",
                    "operator": "price_above",
                    "value": 0,
                    "timeframe": self._extract_timeframe(description),
                })
            elif "below vwap" in description_lower:
                entry_conditions.append({
                    "type": "indicator",
                    "indicator": "VWAP",
                    "operator": "price_below",
                    "value": 0,
                    "timeframe": self._extract_timeframe(description),
                })
        
        # ADX patterns
        adx_match = re.search(r'adx\s*\(?(\d+)?\)?\s*(is\s*)?(above|below|>|<)\s*(\d+)', description_lower)
        if adx_match:
            period = adx_match.group(1) or "14"
            direction = adx_match.group(3)
            value = int(adx_match.group(4))
            
            operator = "greater_than" if direction in ["above", ">"] else "less_than"
            entry_conditions.append({
                "type": "indicator",
                "indicator": f"ADX({period})",
                "operator": operator,
                "value": value,
                "timeframe": self._extract_timeframe(description),
            })
        
        result["entry_conditions"] = entry_conditions
        
        # Parse exit conditions
        exit_conditions = []
        
        # RSI exit
        rsi_exit_match = re.search(r'exit\s+when\s+rsi\s*(crosses?\s*(above|below)|reaches?)\s*(\d+)', description_lower)
        if rsi_exit_match:
            direction = rsi_exit_match.group(2) or "above"
            value = int(rsi_exit_match.group(3))
            
            exit_conditions.append({
                "type": "indicator",
                "indicator": "RSI(14)",
                "operator": f"crosses_{direction}",
                "value": value,
                "timeframe": self._extract_timeframe(description),
            })
        
        # MACD exit
        if "exit" in description_lower and "macd" in description_lower:
            if "crosses below" in description_lower:
                exit_conditions.append({
                    "type": "indicator",
                    "indicator": "MACD",
                    "operator": "crosses_below",
                    "value": "signal",
                    "timeframe": self._extract_timeframe(description),
                })
        
        # SuperTrend exit
        if "exit" in description_lower and "supertrend" in description_lower:
            if "turns red" in description_lower:
                exit_conditions.append({
                    "type": "indicator",
                    "indicator": "SuperTrend",
                    "operator": "equals",
                    "value": "bearish",
                    "timeframe": self._extract_timeframe(description),
                })
        
        result["exit_conditions"] = exit_conditions
        
        # Parse stop loss
        sl_match = re.search(r'stop\s*loss\s*(at|of|:)?\s*(\d+\.?\d*)\s*(%|percent|points?)?', description_lower)
        if sl_match:
            value = float(sl_match.group(2))
            unit = sl_match.group(3) or "%"
            
            result["stop_loss"] = {
                "type": "fixed",
                "value": value,
                "unit": "percent" if "%" in unit or "percent" in unit else "points",
            }
        
        # Parse target
        target_match = re.search(r'(\d+\.?\d*)\s*(%|percent)?\s*(profit|target)', description_lower)
        if target_match:
            value = float(target_match.group(1))
            
            result["target"] = {
                "type": "fixed",
                "value": value,
                "unit": "percent",
            }
        
        # Trailing stop
        if "trailing" in description_lower:
            trailing_match = re.search(r'trailing\s*(stop)?\s*(at|of)?\s*(\d+\.?\d*)\s*(%|percent)?', description_lower)
            if trailing_match:
                value = float(trailing_match.group(3))
                result["stop_loss"] = {
                    "type": "trailing",
                    "value": value,
                    "unit": "percent",
                }
        
        # Calculate confidence based on how much we parsed
        parsed_items = len(entry_conditions) + len(exit_conditions)
        if result["stop_loss"]:
            parsed_items += 1
        if result["target"]:
            parsed_items += 1
        
        result["confidence"] = min(0.95, parsed_items * 0.15 + 0.3)
        
        return result
    
    def get_templates(self) -> list[dict]:
        """Get all strategy templates."""
        return STRATEGY_TEMPLATES
    
    def get_template_categories(self) -> list[dict]:
        """Get strategy template categories with their strategies."""
        categories = []
        
        for cat in STRATEGY_CATEGORIES:
            cat_templates = [t for t in STRATEGY_TEMPLATES if t["category"] == cat["id"]]
            categories.append({
                **cat,
                "strategies": cat_templates,
            })
        
        return categories
    
    def get_template_by_id(self, template_id: str) -> dict | None:
        """Get a specific template by ID."""
        for template in STRATEGY_TEMPLATES:
            if template["id"] == template_id:
                return template
        return None
    
    async def get_strategy_versions(self, strategy_id: uuid.UUID) -> list[dict]:
        """Get version history for a strategy."""
        result = await self._session.execute(
            select(StrategyVersion)
            .where(StrategyVersion.strategy_id == strategy_id)
            .order_by(StrategyVersion.version.desc())
        )
        versions = result.scalars().all()
        
        return [
            {
                "id": str(v.id),
                "version": v.version,
                "snapshot": v.snapshot,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ]
    
    async def _create_version(self, strategy: Strategy) -> StrategyVersion:
        """Create a new version snapshot of a strategy."""
        # Get current max version
        result = await self._session.execute(
            select(StrategyVersion)
            .where(StrategyVersion.strategy_id == strategy.id)
            .order_by(StrategyVersion.version.desc())
            .limit(1)
        )
        last_version = result.scalar_one_or_none()
        new_version_num = (last_version.version + 1) if last_version else 1
        
        version = StrategyVersion(
            id=uuid.uuid4(),
            strategy_id=strategy.id,
            version=new_version_num,
            snapshot={
                "name": strategy.name,
                "description": strategy.description,
                "status": strategy.status,
                "entry_conditions": strategy.entry_conditions,
                "exit_conditions": strategy.exit_conditions,
                "stop_loss": strategy.stop_loss,
                "target": strategy.target,
                "position_size": strategy.position_size,
                "max_positions": strategy.max_positions,
                "natural_language_input": strategy.natural_language_input,
            },
        )
        
        self._session.add(version)
        await self._session.commit()
        
        return version
    
    def _extract_timeframe(self, description: str) -> str:
        """Extract timeframe from description."""
        description_lower = description.lower()
        
        if "5-min" in description_lower or "5 min" in description_lower or "5min" in description_lower:
            return "5min"
        elif "15-min" in description_lower or "15 min" in description_lower or "15min" in description_lower:
            return "15min"
        elif "1-hour" in description_lower or "1 hour" in description_lower or "hourly" in description_lower:
            return "1hour"
        elif "daily" in description_lower or "day" in description_lower:
            return "daily"
        
        return "15min"  # Default
    
    def _generate_strategy_name(self, description: str) -> str:
        """Generate a strategy name from description."""
        description_lower = description.lower()
        
        indicators = []
        if "rsi" in description_lower:
            indicators.append("RSI")
        if "macd" in description_lower:
            indicators.append("MACD")
        if "supertrend" in description_lower:
            indicators.append("SuperTrend")
        if "ema" in description_lower:
            indicators.append("EMA")
        if "bollinger" in description_lower or "bb" in description_lower:
            indicators.append("BB")
        if "vwap" in description_lower:
            indicators.append("VWAP")
        if "adx" in description_lower:
            indicators.append("ADX")
        
        if indicators:
            return f"{' + '.join(indicators)} Strategy"
        
        return "Custom Strategy"
