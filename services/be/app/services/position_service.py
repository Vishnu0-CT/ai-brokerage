"""
Position Service

Manages open positions, order placement, and exit functionality.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Position, Trade


class PositionService:
    """Service for managing positions and orders."""
    
    def __init__(self, session: AsyncSession, price_service: Any = None) -> None:
        self._session = session
        self._price_service = price_service
    
    async def place_order(
        self,
        user_id: uuid.UUID,
        symbol: str,
        order_type: str,  # "BUY" or "SELL"
        quantity: int,
        lots: int,
        price: Decimal,
        expiry: str,
    ) -> dict:
        """
        Place an order and create a position.
        For mock trading, orders are always filled immediately.
        """
        # Create position
        position = Position(
            id=uuid.uuid4(),
            user_id=user_id,
            symbol=symbol,
            position_type=order_type,
            quantity=quantity,
            lots=lots,
            avg_price=price,
            expiry=expiry,
        )
        
        self._session.add(position)
        await self._session.commit()
        await self._session.refresh(position)
        
        return {
            "id": str(position.id),
            "symbol": position.symbol,
            "type": position.position_type,
            "quantity": position.quantity,
            "lots": position.lots,
            "avg_price": float(position.avg_price),
            "expiry": position.expiry,
            "timestamp": position.created_at.isoformat(),
            "status": "filled",
        }
    
    async def get_positions(self, user_id: uuid.UUID) -> list[dict]:
        """Get all open positions for a user with current P&L."""
        result = await self._session.execute(
            select(Position)
            .where(Position.user_id == user_id)
            .order_by(Position.created_at.desc())
        )
        positions = result.scalars().all()
        
        position_list = []
        for pos in positions:
            # Get current price
            ltp = await self._get_current_price(pos.symbol)
            
            # Calculate P&L
            if pos.position_type == "BUY":
                pnl = (ltp - float(pos.avg_price)) * pos.quantity
            else:  # SELL
                pnl = (float(pos.avg_price) - ltp) * pos.quantity
            
            pnl_percent = (pnl / (float(pos.avg_price) * pos.quantity)) * 100 if pos.avg_price > 0 else 0
            
            position_list.append({
                "id": str(pos.id),
                "symbol": pos.symbol,
                "type": pos.position_type,
                "quantity": pos.quantity,
                "lots": pos.lots,
                "avg_price": float(pos.avg_price),
                "ltp": ltp,
                "pnl": round(pnl, 2),
                "pnl_percent": round(pnl_percent, 2),
                "expiry": pos.expiry,
                "created_at": pos.created_at.isoformat(),
            })
        
        return position_list
    
    async def get_position(self, position_id: uuid.UUID) -> dict | None:
        """Get a single position by ID."""
        result = await self._session.execute(
            select(Position).where(Position.id == position_id)
        )
        pos = result.scalar_one_or_none()
        
        if not pos:
            return None
        
        ltp = await self._get_current_price(pos.symbol)
        
        if pos.position_type == "BUY":
            pnl = (ltp - float(pos.avg_price)) * pos.quantity
        else:
            pnl = (float(pos.avg_price) - ltp) * pos.quantity
        
        pnl_percent = (pnl / (float(pos.avg_price) * pos.quantity)) * 100 if pos.avg_price > 0 else 0
        
        return {
            "id": str(pos.id),
            "symbol": pos.symbol,
            "type": pos.position_type,
            "quantity": pos.quantity,
            "lots": pos.lots,
            "avg_price": float(pos.avg_price),
            "ltp": ltp,
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "expiry": pos.expiry,
            "created_at": pos.created_at.isoformat(),
        }
    
    async def exit_position(
        self,
        position_id: uuid.UUID,
        exit_price: Decimal | None = None,
    ) -> dict:
        """
        Exit a position and record the trade.
        
        Returns:
            {"success": True, "trade": trade_record}
        """
        result = await self._session.execute(
            select(Position).where(Position.id == position_id)
        )
        position = result.scalar_one_or_none()
        
        if not position:
            return {"success": False, "error": "Position not found"}
        
        # Get exit price
        if exit_price is None:
            exit_price = Decimal(str(await self._get_current_price(position.symbol)))
        
        # Calculate P&L
        if position.position_type == "BUY":
            pnl = (float(exit_price) - float(position.avg_price)) * position.quantity
        else:
            pnl = (float(position.avg_price) - float(exit_price)) * position.quantity
        
        pnl_percent = (pnl / (float(position.avg_price) * position.quantity)) * 100
        
        # Calculate hold time
        hold_time = datetime.now(timezone.utc) - position.created_at
        hold_time_minutes = int(hold_time.total_seconds() / 60)
        
        # Create trade record
        trade = Trade(
            id=uuid.uuid4(),
            user_id=position.user_id,
            date=datetime.now(timezone.utc),
            time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            instrument=position.symbol,
            trade_type=position.position_type,
            entry_price=position.avg_price,
            exit_price=exit_price,
            quantity=position.quantity,
            pnl=Decimal(str(round(pnl, 2))),
            pnl_percent=Decimal(str(round(pnl_percent, 2))),
            hold_time_minutes=hold_time_minutes,
            strategy="Manual Trade",
            tags=["manual_exit"],
            notes=f"Position exited manually",
            is_revenge_trade=False,
            is_overtrade=False,
            is_tilt_trade=False,
        )
        
        self._session.add(trade)
        
        # Delete position
        await self._session.delete(position)
        await self._session.commit()
        
        return {
            "success": True,
            "trade": {
                "id": str(trade.id),
                "symbol": trade.instrument,
                "type": trade.trade_type,
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price),
                "quantity": trade.quantity,
                "pnl": float(trade.pnl),
                "pnl_percent": float(trade.pnl_percent),
                "hold_time_minutes": trade.hold_time_minutes,
            },
        }
    
    async def exit_all_positions(self, user_id: uuid.UUID) -> dict:
        """Exit all open positions for a user."""
        result = await self._session.execute(
            select(Position).where(Position.user_id == user_id)
        )
        positions = result.scalars().all()
        
        results = []
        total_pnl = 0
        
        for position in positions:
            exit_result = await self.exit_position(position.id)
            results.append(exit_result)
            if exit_result["success"]:
                total_pnl += exit_result["trade"]["pnl"]
        
        return {
            "success": True,
            "positions_closed": len(results),
            "total_pnl": round(total_pnl, 2),
            "results": results,
        }
    
    async def get_position_summary(self, user_id: uuid.UUID) -> dict:
        """Get summary of all positions."""
        positions = await self.get_positions(user_id)
        
        if not positions:
            return {
                "total_positions": 0,
                "total_invested": 0,
                "total_current_value": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "profitable_positions": 0,
                "losing_positions": 0,
            }
        
        total_invested = sum(p["avg_price"] * p["quantity"] for p in positions)
        total_current = sum(p["ltp"] * p["quantity"] for p in positions)
        total_pnl = sum(p["pnl"] for p in positions)
        
        profitable = sum(1 for p in positions if p["pnl"] > 0)
        losing = sum(1 for p in positions if p["pnl"] < 0)
        
        return {
            "total_positions": len(positions),
            "total_invested": round(total_invested, 2),
            "total_current_value": round(total_current, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round((total_pnl / total_invested) * 100, 2) if total_invested > 0 else 0,
            "profitable_positions": profitable,
            "losing_positions": losing,
        }
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        if self._price_service:
            try:
                tick = await self._price_service.get_price(symbol.split()[0])  # Get base symbol
                if tick:
                    return tick.price
            except Exception:
                pass
        
        # Mock price based on symbol
        import random
        
        # Extract base price from symbol if it's an option
        parts = symbol.split()
        if len(parts) >= 2:
            try:
                strike = int(parts[1])
                # Option price is typically a fraction of strike
                base_price = strike * 0.01 * random.uniform(0.5, 2.0)
                return round(base_price, 2)
            except ValueError:
                pass
        
        return round(random.uniform(100, 500), 2)
