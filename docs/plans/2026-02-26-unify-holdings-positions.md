# Unify Holdings & Positions — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate the `positions` table by extending `holdings` with optional F&O columns, rewiring all position flows through `OrderService`, and removing `PositionService`.

**Architecture:** The `holdings` table becomes the single source of truth for all open trades (equity and F&O). `OrderService` gains two new methods: `place_fno_order` (delegates to existing `_buy`/`_sell` then patches F&O fields) and `exit_holding` (closes a holding and creates a `Trade` record). The `/api/positions` routes become thin wrappers around `OrderService` + `PortfolioService`. `PositionService` and the `Position` model are deleted.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, React (Vite)

**Note:** This project has zero existing tests. Verification steps use `psql` and `curl` against the running dev server.

---

### Task 1: Migration — Add F&O columns to holdings

**Files:**
- Create: `services/be/alembic/versions/004_add_holdings_fno_columns.py`

**Step 1: Write migration**

```python
"""add F&O columns to holdings

Revision ID: 004_holdings_fno
Revises: 003_holding_side
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_holdings_fno"
down_revision: Union[str, Sequence[str], None] = "003_holding_side"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("holdings", sa.Column("lots", sa.Integer(), nullable=True))
    op.add_column("holdings", sa.Column("expiry", sa.String(), nullable=True))
    op.add_column("holdings", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True))


def downgrade() -> None:
    op.drop_column("holdings", "created_at")
    op.drop_column("holdings", "expiry")
    op.drop_column("holdings", "lots")
```

**Step 2: Run migration**

```bash
cd services/be && alembic upgrade head
```

**Step 3: Verify columns exist**

```bash
psql postgresql://localhost:5432/ai_brokerage -c "\d holdings"
```

Expected: `lots`, `expiry`, `created_at` columns visible, all nullable.

**Step 4: Commit**

```bash
git add services/be/alembic/versions/004_add_holdings_fno_columns.py
git commit -m "feat: add lots, expiry, created_at columns to holdings table"
```

---

### Task 2: Extend Holding model

**Files:**
- Modify: `services/be/app/models/portfolio.py:14-36` (Holding class)

**Step 1: Add F&O fields to Holding model**

Add after the `updated_at` field (line 32), before `__table_args__`:

```python
    lots: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expiry: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
```

Also add `Integer` to the sqlalchemy imports on line 7:

```python
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, text
```

**Step 2: Verify app starts**

```bash
cd services/be && python -m app.main
```

Expected: Server starts without import errors.

**Step 3: Commit**

```bash
git add services/be/app/models/portfolio.py
git commit -m "feat: add lots, expiry, created_at fields to Holding model"
```

---

### Task 3: Extend HoldingResponse schema and PortfolioService

**Files:**
- Modify: `services/be/app/schemas/portfolio.py:6-15` (HoldingResponse)
- Modify: `services/be/app/services/portfolio.py:38-70` (get_holdings)

**Step 1: Add F&O fields to HoldingResponse**

In `services/be/app/schemas/portfolio.py`, add to `HoldingResponse`:

```python
class HoldingResponse(BaseModel):
    id: str
    symbol: str
    side: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float | None = None
    pnl: float
    pnl_pct: float
    lots: int | None = None
    expiry: str | None = None
    created_at: str | None = None
```

**Step 2: Include new fields in get_holdings response**

In `services/be/app/services/portfolio.py`, in the `get_holdings` method, update the dict built at lines 58-68 to include `id`, `lots`, `expiry`, `created_at`:

```python
            enriched.append({
                "id": str(h.id),
                "symbol": h.symbol,
                "side": h.side,
                "quantity": h.quantity,
                "avg_price": h.avg_price,
                "current_price": current_price,
                "unrealized_pnl": round(unrealized, 2),
                "realized_pnl": None,
                "pnl": round(unrealized, 2),
                "pnl_pct": round(pnl_pct, 2),
                "lots": h.lots,
                "expiry": h.expiry,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            })
```

**Step 3: Verify**

```bash
curl -s http://localhost:8000/api/portfolio/holdings | python3 -m json.tool
```

Expected: Each holding now includes `"id"`, `"lots": null`, `"expiry": null`, `"created_at"`.

**Step 4: Commit**

```bash
git add services/be/app/schemas/portfolio.py services/be/app/services/portfolio.py
git commit -m "feat: include id, lots, expiry, created_at in holdings API response"
```

---

### Task 4: Add OrderService.place_fno_order

**Files:**
- Modify: `services/be/app/services/order.py:15-18` (constructor) and append new method

**Step 1: Add price_service to OrderService constructor**

The constructor currently takes `(session, margin_service)`. Add `price_service` so `exit_holding` (Task 5) can fetch LTP:

```python
class OrderService:
    def __init__(self, session: AsyncSession, margin_service: Any = None, price_service: Any = None) -> None:
        self._session = session
        self._margin = margin_service
        self._price_service = price_service
```

**Step 2: Add place_fno_order method**

Append after `get_transactions` (after line 176):

```python
    async def place_fno_order(
        self,
        user_id: uuid.UUID,
        symbol: str,
        order_type: str,
        quantity: int,
        lots: int,
        price: Decimal,
        expiry: str,
    ) -> dict:
        """Place an F&O order. Delegates to _buy/_sell, then patches F&O fields on the holding."""
        side = "buy" if order_type == "BUY" else "sell"
        result = await self.place_order(
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=Decimal(quantity),
            price=price,
        )

        # Patch F&O-specific fields on the holding
        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one()
        holding.lots = lots
        holding.expiry = expiry
        await self._session.commit()

        return {
            "id": str(holding.id),
            "symbol": holding.symbol,
            "type": order_type,
            "quantity": int(holding.quantity),
            "lots": holding.lots,
            "avg_price": float(holding.avg_price),
            "expiry": holding.expiry,
            "timestamp": holding.created_at.isoformat() if holding.created_at else None,
            "status": "filled",
        }
```

**Step 3: Verify import**

Ensure `Holding` is imported at the top of `order.py` (it already is at line 11).

**Step 4: Verify app starts**

```bash
cd services/be && python -m app.main
```

**Step 5: Commit**

```bash
git add services/be/app/services/order.py
git commit -m "feat: add place_fno_order to OrderService"
```

---

### Task 5: Add OrderService.exit_holding

**Files:**
- Modify: `services/be/app/services/order.py` (append new method)

**Step 1: Add exit_holding method**

Append after `place_fno_order`. This also needs `Trade` imported:

Add to imports at top of file:
```python
from app.models.trade import Trade
```

Then the method:

```python
    async def exit_holding(
        self,
        user_id: uuid.UUID,
        symbol: str,
        exit_price: Decimal | None = None,
    ) -> dict:
        """Exit a holding entirely. Creates a Trade record for analytics."""
        h_result = await self._session.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.symbol == symbol)
        )
        holding = h_result.scalar_one_or_none()
        if not holding:
            raise ValueError(f"No holding found for symbol: {symbol}")

        # Get exit price from price service if not provided
        if exit_price is None:
            if self._price_service:
                tick = await self._price_service.get_price(symbol)
                exit_price = Decimal(str(tick.price)) if tick else holding.avg_price
            else:
                exit_price = holding.avg_price

        qty = holding.quantity
        avg = holding.avg_price
        is_long = holding.side == "long"

        # Calculate P&L
        if is_long:
            pnl = (float(exit_price) - float(avg)) * float(qty)
        else:
            pnl = (float(avg) - float(exit_price)) * float(qty)

        pnl_percent = (pnl / (float(avg) * float(qty))) * 100 if avg * qty else 0

        # Calculate hold time
        hold_time_minutes = 0
        if holding.created_at:
            hold_time = datetime.now(timezone.utc) - holding.created_at
            hold_time_minutes = int(hold_time.total_seconds() / 60)

        # Close the holding via existing _sell/_buy
        if is_long:
            await self._sell(user_id, symbol, qty, exit_price, triggered_by=None)
        else:
            await self._buy(user_id, symbol, qty, exit_price, triggered_by=None)

        # Create Trade record for analytics pipeline
        trade = Trade(
            id=uuid.uuid4(),
            user_id=user_id,
            date=datetime.now(timezone.utc),
            time=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            instrument=symbol,
            trade_type="BUY" if is_long else "SELL",
            entry_price=avg,
            exit_price=exit_price,
            quantity=int(qty),
            pnl=Decimal(str(round(pnl, 2))),
            pnl_percent=Decimal(str(round(pnl_percent, 2))),
            hold_time_minutes=hold_time_minutes,
            strategy="Manual Trade",
            tags=["manual_exit"],
            notes="Holding exited manually",
            is_revenge_trade=False,
            is_overtrade=False,
            is_tilt_trade=False,
        )
        self._session.add(trade)
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

    async def exit_holding_by_id(
        self,
        holding_id: uuid.UUID,
        exit_price: Decimal | None = None,
    ) -> dict:
        """Exit a holding by its ID. Resolves symbol then delegates to exit_holding."""
        h_result = await self._session.execute(
            select(Holding).where(Holding.id == holding_id)
        )
        holding = h_result.scalar_one_or_none()
        if not holding:
            raise ValueError(f"No holding found with id: {holding_id}")
        return await self.exit_holding(holding.user_id, holding.symbol, exit_price)
```

Also add `datetime` import if not already present:
```python
from datetime import datetime, timezone
```

**Step 2: Verify app starts**

```bash
cd services/be && python -m app.main
```

**Step 3: Commit**

```bash
git add services/be/app/services/order.py
git commit -m "feat: add exit_holding and exit_holding_by_id to OrderService"
```

---

### Task 6: Rewire positions routes

**Files:**
- Rewrite: `services/be/app/routes/positions.py`

**Step 1: Rewrite the positions routes file**

Replace the entire file. The routes keep the same URL paths and request/response shapes but delegate to `OrderService` and `PortfolioService`:

```python
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.order import OrderService
from app.services.portfolio import PortfolioService

router = APIRouter(prefix="/api/positions", tags=["positions"])


def get_order_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> OrderService:
    price_service = getattr(request.app.state, "price_service", None)
    margin_service = getattr(request.app.state, "margin_service", None)
    return OrderService(session, margin_service, price_service)


def get_portfolio_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> PortfolioService:
    return PortfolioService(session=session, price_service=request.app.state.price_service)


class OrderRequest(BaseModel):
    symbol: str
    order_type: str
    quantity: int
    lots: int
    price: Decimal
    expiry: str


class ExitPositionRequest(BaseModel):
    exit_price: Decimal | None = None


@router.get("")
async def get_positions(
    svc: PortfolioService = Depends(get_portfolio_service),
):
    """Get all open holdings (unified positions)."""
    return await svc.get_holdings(DEFAULT_USER_ID)


@router.get("/summary")
async def get_position_summary(
    svc: PortfolioService = Depends(get_portfolio_service),
):
    """Get summary of all holdings."""
    return await svc.get_portfolio_summary(DEFAULT_USER_ID)


@router.post("")
async def place_order(
    body: OrderRequest,
    svc: OrderService = Depends(get_order_service),
):
    """Place an F&O order — creates/upserts a holding with cash impact."""
    return await svc.place_fno_order(
        user_id=DEFAULT_USER_ID,
        symbol=body.symbol,
        order_type=body.order_type,
        quantity=body.quantity,
        lots=body.lots,
        price=body.price,
        expiry=body.expiry,
    )


@router.post("/{holding_id}/exit")
async def exit_position(
    holding_id: str,
    body: ExitPositionRequest | None = None,
    svc: OrderService = Depends(get_order_service),
):
    """Exit a holding by its ID."""
    try:
        import uuid
        hid = uuid.UUID(holding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid holding ID")

    try:
        return await svc.exit_holding_by_id(
            holding_id=hid,
            exit_price=body.exit_price if body else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/exit-all")
async def exit_all_positions(
    svc: OrderService = Depends(get_order_service),
    psvc: PortfolioService = Depends(get_portfolio_service),
):
    """Exit all open holdings."""
    holdings = await psvc.get_holdings(DEFAULT_USER_ID)
    results = []
    total_pnl = 0

    for h in holdings:
        result = await svc.exit_holding(
            user_id=DEFAULT_USER_ID,
            symbol=h["symbol"],
        )
        results.append(result)
        if result["success"]:
            total_pnl += result["trade"]["pnl"]

    return {
        "success": True,
        "positions_closed": len(results),
        "total_pnl": round(total_pnl, 2),
        "results": results,
    }
```

**Step 2: Verify routes load**

```bash
cd services/be && python -m app.main
```

Then:
```bash
curl -s http://localhost:8000/api/positions | python3 -m json.tool
```

Expected: Same data as `/api/portfolio/holdings` (now includes `id`, `lots`, `expiry`).

**Step 3: Test placing an F&O order**

```bash
curl -s -X POST http://localhost:8000/api/positions \
  -H "Content-Type: application/json" \
  -d '{"symbol":"NIFTY 26500 CE","order_type":"BUY","quantity":150,"lots":2,"price":250.00,"expiry":"2026-03-27"}' \
  | python3 -m json.tool
```

Expected: Response with `"status": "filled"`, `"lots": 2`, `"expiry": "2026-03-27"`.

Verify it created a holding and a transaction:
```bash
psql postgresql://localhost:5432/ai_brokerage -c "SELECT symbol, side, quantity, lots, expiry FROM holdings WHERE symbol LIKE '%CE%';"
psql postgresql://localhost:5432/ai_brokerage -c "SELECT symbol, side, quantity, price FROM transactions ORDER BY created_at DESC LIMIT 1;"
```

**Step 4: Test exiting a holding**

```bash
# Get the holding ID from the previous response, or:
HOLDING_ID=$(psql -t postgresql://localhost:5432/ai_brokerage -c "SELECT id FROM holdings WHERE symbol LIKE '%CE%' LIMIT 1;" | tr -d ' ')
curl -s -X POST "http://localhost:8000/api/positions/${HOLDING_ID}/exit" \
  -H "Content-Type: application/json" \
  | python3 -m json.tool
```

Expected: `"success": true` with a trade summary. The holding row should be deleted. A trade record should exist.

```bash
psql postgresql://localhost:5432/ai_brokerage -c "SELECT id FROM holdings WHERE symbol LIKE '%CE%';"
psql postgresql://localhost:5432/ai_brokerage -c "SELECT instrument, pnl FROM trades ORDER BY created_at DESC LIMIT 1;"
```

**Step 5: Commit**

```bash
git add services/be/app/routes/positions.py
git commit -m "feat: rewire /api/positions routes to OrderService + holdings table"
```

---

### Task 7: Fix frontend PositionsTable exit flow

**Files:**
- Modify: `services/fe/src/components/dashboard/PositionsTable.jsx:3-4` (imports), `29` (exit call)

**Step 1: Switch exit import to use positions API with holding ID**

The holdings API now returns `id`. The `/api/positions/{id}/exit` route now accepts holding IDs. So the existing `exitPosition(id)` import works — we just need to make sure we're passing the holding's `id`.

In `PositionsTable.jsx`, the exit handler at line 29 already does:
```javascript
await exitPosition(exitingPosition.id)
```

And the holdings response now includes `id` (from Task 3). Verify the `key` prop also uses `position.id` (currently `position.id || position.symbol` from the earlier fix — `position.id` will now always be present).

Update line 107 to use just `position.id`:
```javascript
<tr key={position.id} className="...">
```

**Step 2: Verify in browser**

Navigate to `http://localhost:5173`, open Dashboard. The "Open Positions" table should show 5 holdings. Click "Exit" on one — it should succeed and remove the row.

**Step 3: Commit**

```bash
git add services/fe/src/components/dashboard/PositionsTable.jsx
git commit -m "fix: PositionsTable exit button works with unified holdings API"
```

---

### Task 8: Remove PositionService, Position model, drop positions table

**Files:**
- Delete: `services/be/app/services/position_service.py`
- Modify: `services/be/app/services/__init__.py:5` (remove PositionService import)
- Modify: `services/be/app/models/trade.py:52-76` (remove Position class)
- Modify: `services/be/app/models/__init__.py:8` (remove Position import)
- Create: `services/be/alembic/versions/005_drop_positions_table.py`

**Step 1: Delete position_service.py**

```bash
rm services/be/app/services/position_service.py
```

**Step 2: Remove PositionService from services/__init__.py**

In `services/be/app/services/__init__.py`, remove the line:
```python
from app.services.position_service import PositionService
```

**Step 3: Remove Position class from trade.py**

In `services/be/app/models/trade.py`, delete lines 52-76 (the entire `Position` class). Also remove `Index` and `Integer` from imports on line 7 if they're no longer used by the remaining `Trade` class. `Trade` uses `Integer` (line 30, 33) so keep that. `Trade` uses `Index` (line 47) so keep that too. No import changes needed.

**Step 4: Remove Position from models/__init__.py**

In `services/be/app/models/__init__.py`, remove `Position` from the import:

```python
# Before:
from app.models.trade import Position, Trade
# After:
from app.models.trade import Trade
```

**Step 5: Write migration to drop positions table**

```python
"""drop positions table

Revision ID: 005_drop_positions
Revises: 004_holdings_fno
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_drop_positions"
down_revision: Union[str, Sequence[str], None] = "004_holdings_fno"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_positions_user", table_name="positions")
    op.drop_table("positions")


def downgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("position_type", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("lots", sa.Integer(), nullable=False),
        sa.Column("avg_price", sa.Numeric(), nullable=False),
        sa.Column("expiry", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_positions_user", "positions", ["user_id"])
```

**Step 6: Run migration**

```bash
cd services/be && alembic upgrade head
```

**Step 7: Verify**

```bash
psql postgresql://localhost:5432/ai_brokerage -c "\dt"
```

Expected: `positions` table no longer listed.

```bash
cd services/be && python -m app.main
```

Expected: Server starts clean, no import errors.

**Step 8: Commit**

```bash
git add -A services/be/app/services/position_service.py services/be/app/services/__init__.py services/be/app/models/trade.py services/be/app/models/__init__.py services/be/alembic/versions/005_drop_positions_table.py
git commit -m "chore: remove PositionService, Position model, drop positions table"
```

---

### Task 9: Final verification — full flow smoke test

**Step 1: Restart backend**

```bash
cd services/be && python -m app.main
```

**Step 2: Verify existing holdings**

```bash
curl -s http://localhost:8000/api/portfolio/holdings | python3 -m json.tool
curl -s http://localhost:8000/api/positions | python3 -m json.tool
```

Expected: Both return the same 5 holdings (NIFTY, BANKNIFTY, RELIANCE, INFY, TCS).

**Step 3: Place an F&O order**

```bash
curl -s -X POST http://localhost:8000/api/positions \
  -H "Content-Type: application/json" \
  -d '{"symbol":"NIFTY 27000 PE","order_type":"BUY","quantity":150,"lots":2,"price":180.00,"expiry":"2026-03-27"}' \
  | python3 -m json.tool
```

Expected: New holding created with `lots=2`, `expiry="2026-03-27"`. Cash reduced. Transaction created.

**Step 4: Verify in DB**

```bash
psql postgresql://localhost:5432/ai_brokerage -c "SELECT symbol, side, quantity, lots, expiry FROM holdings ORDER BY created_at DESC;"
psql postgresql://localhost:5432/ai_brokerage -c "SELECT symbol, side, quantity, price FROM transactions ORDER BY created_at DESC LIMIT 3;"
```

**Step 5: Exit the new holding**

```bash
HOLDING_ID=$(psql -t postgresql://localhost:5432/ai_brokerage -c "SELECT id FROM holdings WHERE symbol = 'NIFTY 27000 PE';" | tr -d ' ')
curl -s -X POST "http://localhost:8000/api/positions/${HOLDING_ID}/exit" \
  -H "Content-Type: application/json" \
  | python3 -m json.tool
```

Expected: Holding deleted. Trade record created. Cash returned.

**Step 6: Verify frontend**

Open `http://localhost:5173` — Dashboard should show holdings in the positions table. Trade page order placement should create a holding visible on dashboard.

**Step 7: Commit any remaining fixes**

If any adjustments were needed, commit them.
