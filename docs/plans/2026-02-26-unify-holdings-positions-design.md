# Unify Holdings & Positions

**Date:** 2026-02-26
**Status:** Approved

## Problem

Two independent tables (`holdings`, `positions`) track open trades with zero synchronization. Holdings is the integrated system (cash, transactions, analytics). Positions was added for F&O but never wired into the financial lifecycle. Orders placed from the Trade page don't affect cash or appear in analytics. The dashboard shows holdings data in a component labeled "positions."

## Decision

Extend the `holdings` table with optional F&O columns. Rewire all position flows through `OrderService`. Eliminate the `positions` table and `PositionService`.

## Schema Change

Add to `holdings`:

| Column | Type | Nullable | Default | Purpose |
|-|-|-|-|-|
| lots | INTEGER | YES | NULL | F&O lot count |
| expiry | VARCHAR | YES | NULL | F&O expiry date |
| created_at | TIMESTAMPTZ | YES | now() | When first opened |

Equity holdings: `lots=NULL, expiry=NULL`. F&O holdings: both populated.
Existing unique constraint `(user_id, symbol)` unchanged -- F&O symbols are full descriptors (e.g. `NIFTY 26500 CE`).

## OrderService Extensions

### place_fno_order(user_id, symbol, side, quantity, lots, price, expiry)

- Maps `"BUY"` -> `_buy()`, `"SELL"` -> `_sell()`
- After upsert, patches `lots` and `expiry` on the holding
- Cash deducted, Transaction created (same as equity path)

### exit_holding(user_id, symbol, exit_price=None)

- Looks up holding by `(user_id, symbol)`
- Fetches LTP from price service if no exit_price
- Calls `_sell` (longs) or `_buy` (shorts) with full quantity
- Creates a `Trade` record for analytics pipeline
- Returns trade summary

## Route Rewiring

| Route | Before | After |
|-|-|-|
| POST /api/positions | PositionService.place_order -> Position row | OrderService.place_fno_order -> Holding row |
| GET /api/positions | PositionService.get_positions -> positions table | PortfolioService.get_holdings |
| GET /api/positions/{id} | PositionService.get_position | PortfolioService: query holding by ID |
| POST /api/positions/{id}/exit | PositionService.exit_position | OrderService.exit_holding |
| POST /api/positions/exit-all | Loop exit_position | Loop exit_holding |
| GET /api/positions/summary | PositionService.get_position_summary | PortfolioService.get_portfolio_summary |

Both `/api/positions` and `/api/portfolio/holdings` hit the same data.

## Frontend Changes

- **PositionsTable.jsx**: Already uses `getHoldings()`. Fix exit button to work with holding ID (include `id` in holdings API response).
- **Trade.jsx**: No change needed -- same request shape, backend delegates differently.
- **api/positions.js**: Keep as-is for URL compatibility.

## Elimination

- Delete `PositionService` (`position_service.py`)
- Delete `Position` model from `trade.py`
- Migration: `DROP TABLE positions`
- Clean up imports

## Unchanged

- `PortfolioService.get_holdings`, `get_balance`, `get_portfolio_summary`
- `AnalyticsService` (reads Transaction table, which OrderService writes to)
- `AlertDetector`, `ConditionService`, seed data
- `Trade` model (exit_holding creates Trade records)
