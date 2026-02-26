from __future__ import annotations

import httpx


class BEClient:
    """HTTP client for the BE service REST API.

    The AI service is stateless — all persistence is accessed through
    the BE service. This client wraps every BE endpoint the AI service needs.
    """

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    # --- Health ---

    async def health(self) -> dict:
        r = await self.client.get("/health")
        r.raise_for_status()
        return r.json()

    # --- Portfolio ---

    async def get_holdings(self, **params) -> dict:
        r = await self.client.get("/api/portfolio/holdings", params=params)
        r.raise_for_status()
        return r.json()

    async def get_balance(self) -> dict:
        r = await self.client.get("/api/portfolio/balance")
        r.raise_for_status()
        return r.json()

    async def get_portfolio_summary(self) -> dict:
        r = await self.client.get("/api/portfolio/summary")
        r.raise_for_status()
        return r.json()

    async def get_portfolio_history(self, period: str) -> dict:
        r = await self.client.get("/api/portfolio/history", params={"period": period})
        r.raise_for_status()
        return r.json()

    # --- Orders ---

    async def place_order(self, order_data: dict) -> dict:
        r = await self.client.post("/api/orders", json=order_data)
        r.raise_for_status()
        return r.json()

    async def get_transactions(self, **params) -> dict:
        r = await self.client.get("/api/orders", params=params)
        r.raise_for_status()
        return r.json()

    async def create_conditional_order(self, data: dict) -> dict:
        r = await self.client.post("/api/orders/conditions", json=data)
        r.raise_for_status()
        return r.json()

    async def cancel_conditional_order(self, order_id: str) -> dict:
        r = await self.client.delete(f"/api/orders/conditions/{order_id}")
        r.raise_for_status()
        return r.json()

    async def list_active_conditions(self) -> dict:
        r = await self.client.get("/api/orders/conditions")
        r.raise_for_status()
        return r.json()

    # --- Market ---

    async def get_price(self, symbol: str) -> dict:
        r = await self.client.get(f"/api/market/price/{symbol}")
        r.raise_for_status()
        return r.json()

    async def get_quote(self, symbol: str) -> dict:
        r = await self.client.get(f"/api/market/quote/{symbol}")
        r.raise_for_status()
        return r.json()

    async def get_price_history(self, symbol: str, period: str = "1d") -> dict:
        r = await self.client.get(f"/api/market/history/{symbol}", params={"period": period})
        r.raise_for_status()
        return r.json()

    # --- Analytics ---

    async def filter_trades(self, **params) -> dict:
        r = await self.client.get("/api/analytics/trades", params=params)
        r.raise_for_status()
        return r.json()

    async def aggregate_metrics(self, **params) -> dict:
        r = await self.client.get("/api/analytics/metrics", params=params)
        r.raise_for_status()
        return r.json()

    async def calculate_exposure(self, by: str) -> dict:
        r = await self.client.get("/api/analytics/exposure", params={"by": by})
        r.raise_for_status()
        return r.json()

    async def simulate_scenario(self, **params) -> dict:
        r = await self.client.post("/api/analytics/simulate", json=params)
        r.raise_for_status()
        return r.json()

    async def get_coaching_insights(self, period: str = "30d") -> dict:
        r = await self.client.get("/api/analytics/coaching", params={"period": period})
        r.raise_for_status()
        return r.json()

    async def analyze_trade_patterns(self, **params) -> dict:
        r = await self.client.get("/api/analytics/trade-patterns", params=params)
        r.raise_for_status()
        return r.json()

    async def get_trading_signal(self) -> dict:
        r = await self.client.get("/api/analytics/trading-signal")
        r.raise_for_status()
        return r.json()

    # --- Alerts ---

    async def get_alerts(self) -> dict:
        r = await self.client.get("/api/alerts")
        r.raise_for_status()
        return r.json()

    async def get_risk_metrics(self) -> dict:
        r = await self.client.get("/api/alerts/risk-metrics")
        r.raise_for_status()
        return r.json()

    # --- Wellbeing ---

    async def assess_wellbeing(self, conversation_id: str) -> dict:
        r = await self.client.get("/api/wellbeing/assess", params={"conversation_id": conversation_id})
        r.raise_for_status()
        return r.json()

    # --- Conversations ---

    async def create_conversation(self, title: str = "New Conversation") -> dict:
        r = await self.client.post("/api/conversations", json={"title": title})
        r.raise_for_status()
        return r.json()

    async def get_conversation(self, conversation_id: str) -> dict:
        r = await self.client.get(f"/api/conversations/{conversation_id}")
        r.raise_for_status()
        return r.json()

    async def get_messages(self, conversation_id: str, limit: int = 50) -> list:
        r = await self.client.get(
            f"/api/conversations/{conversation_id}/messages",
            params={"limit": limit},
        )
        r.raise_for_status()
        return r.json()

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_data: dict | None = None,
    ) -> dict:
        payload = {"role": role, "content": content}
        if tool_data is not None:
            payload["tool_data"] = tool_data
        r = await self.client.post(
            f"/api/conversations/{conversation_id}/messages",
            json=payload,
        )
        r.raise_for_status()
        return r.json()

    # --- Lifecycle ---

    async def close(self) -> None:
        await self.client.aclose()
