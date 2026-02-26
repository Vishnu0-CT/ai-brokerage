from __future__ import annotations


class InsufficientFundsError(Exception):
    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient funds: need {required}, have {available}")


class InsufficientHoldingsError(Exception):
    def __init__(self, symbol: str, requested: float, available: float):
        self.symbol = symbol
        self.requested = requested
        self.available = available
        super().__init__(f"Insufficient holdings for {symbol}: need {requested}, have {available}")


class SymbolNotFoundError(Exception):
    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Symbol not found: {symbol}")


class ConditionNotFoundError(Exception):
    def __init__(self, condition_id: str):
        self.condition_id = condition_id
        super().__init__(f"Condition not found: {condition_id}")


class PriceUnavailableError(Exception):
    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Price unavailable for: {symbol}")


class DailyLossLimitBreachedError(Exception):
    def __init__(self, current_loss: float, limit: float):
        self.current_loss = current_loss
        self.limit = limit
        super().__init__(
            f"Daily loss limit breached: current loss ₹{current_loss:,.0f} exceeds limit ₹{limit:,.0f}. Trading halted for today."
        )
