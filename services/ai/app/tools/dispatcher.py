from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.be_client import BEClient

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """Routes Claude tool calls to the BE service via HTTP."""

    def __init__(self, be_client: BEClient) -> None:
        self.be = be_client

    async def dispatch(self, tool_name: str, tool_input: dict) -> dict:
        handler = getattr(self, f"_handle_{tool_name}", None)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return await handler(tool_input)
        except Exception as e:
            logger.exception(f"Tool dispatch error: {tool_name}")
            return {"error": str(e)}

    # --- Market Data ---

    async def _handle_search_tickers(self, params: dict) -> dict:
        results = await self.be.search_tickers(params["query"])
        return {"results": results, "count": len(results)}

    async def _handle_get_price(self, params: dict) -> dict:
        return await self.be.get_price(params["symbol"])

    async def _handle_get_quote(self, params: dict) -> dict:
        return await self.be.get_quote(params["symbol"])

    async def _handle_get_price_history(self, params: dict) -> dict:
        return await self.be.get_price_history(
            params["symbol"], params.get("period", "1m"),
        )

    # --- Portfolio ---

    async def _handle_get_positions(self, params: dict) -> dict:
        query = {}
        if params.get("instrument"):
            query["instrument"] = params["instrument"]
        if params.get("filter"):
            query["filter"] = params["filter"]
        return await self.be.get_holdings(**query)

    async def _handle_get_balance(self, params: dict) -> dict:
        return await self.be.get_balance()

    async def _handle_filter_trades(self, params: dict) -> dict:
        return await self.be.filter_trades(**params)

    async def _handle_aggregate_metrics(self, params: dict) -> dict:
        return await self.be.aggregate_metrics(**params)

    async def _handle_calculate_exposure(self, params: dict) -> dict:
        return await self.be.calculate_exposure(params["by"])

    async def _handle_simulate_scenario(self, params: dict) -> dict:
        return await self.be.simulate_scenario(**params)

    async def _handle_analyze_trade_patterns(self, params: dict) -> dict:
        return await self.be.analyze_trade_patterns(**params)

    async def _handle_get_trading_signal(self, params: dict) -> dict:
        return await self.be.get_trading_signal()

    # --- Trading ---

    async def _handle_place_order(self, params: dict) -> dict:
        orders = params.get("orders")
        if orders:
            return await self._handle_bulk_orders(orders)
        return await self.be.place_order(params)

    async def _handle_bulk_orders(self, orders: list[dict]) -> dict:
        results = []
        for order in orders:
            try:
                result = await self.be.place_order(order)
                results.append(result)
            except Exception as e:
                results.append({"symbol": order.get("symbol"), "error": str(e)})

        succeeded = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]
        return {
            "results": results,
            "summary": {
                "total": len(orders),
                "succeeded": len(succeeded),
                "failed": len(failed),
            },
        }

    async def _handle_cancel_conditional_order(self, params: dict) -> dict:
        return await self.be.cancel_conditional_order(params["order_id"])

    # --- Scheduling ---

    async def _handle_create_conditional_order(self, params: dict) -> dict:
        return await self.be.create_conditional_order(params)

    async def _handle_create_price_alert(self, params: dict) -> dict:
        ctype = "price_above" if params["direction"] == "above" else "price_below"
        return await self.be.create_conditional_order({
            "condition_type": ctype,
            "parameters": {"symbol": params["symbol"], "threshold": params["target_price"]},
            "action": {"type": "alert", "symbol": params["symbol"]},
        })

    async def _handle_list_active_conditions(self, params: dict) -> dict:
        return await self.be.list_active_conditions()

    # --- Behavioural ---

    async def _handle_get_alerts(self, params: dict) -> dict:
        return await self.be.get_alerts()

    async def _handle_get_risk_metrics(self, params: dict) -> dict:
        return await self.be.get_risk_metrics()

    async def _handle_get_coaching_insights(self, params: dict) -> dict:
        return await self.be.get_coaching_insights(params.get("period", "30d"))
