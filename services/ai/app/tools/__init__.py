from __future__ import annotations

from app.tools.market_data import MARKET_DATA_TOOLS
from app.tools.trading import TRADING_TOOLS
from app.tools.portfolio import PORTFOLIO_TOOLS
from app.tools.scheduling import SCHEDULING_TOOLS
from app.tools.behavioural import BEHAVIOURAL_TOOLS

ALL_TOOLS = (
    MARKET_DATA_TOOLS
    + TRADING_TOOLS
    + PORTFOLIO_TOOLS
    + SCHEDULING_TOOLS
    + BEHAVIOURAL_TOOLS
)
