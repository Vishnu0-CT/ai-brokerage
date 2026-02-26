from __future__ import annotations

import asyncio
import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class PriceTick:
    symbol: str
    price: float
    bid: float
    ask: float
    volume: int
    high: float
    low: float
    timestamp: float  # unix timestamp


@dataclass
class PriceBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceStream(ABC):
    """Abstract base for price data sources. Swap SimulatedPriceStream for a real provider."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    def subscribe(self, callback: Callable[[PriceTick], None]) -> None: ...

    @abstractmethod
    def get_watched_symbols(self) -> set[str]: ...

    @abstractmethod
    def add_symbol(self, symbol: str) -> None: ...

    @abstractmethod
    def remove_symbol(self, symbol: str) -> None: ...


@dataclass
class _SymbolState:
    price: float
    high: float
    low: float
    volume: int = 0


class SimulatedPriceStream(PriceStream):
    """Generates simulated price ticks using geometric Brownian motion."""

    def __init__(
        self,
        seed_prices: dict[str, float],
        tick_interval: float = 1.5,
        volatility: float = 0.002,
        drift: float = 0.0,
    ) -> None:
        self._seed_prices = seed_prices
        self._tick_interval = tick_interval
        self._volatility = volatility
        self._drift = drift
        self._symbols: dict[str, _SymbolState] = {}
        self._watched: set[str] = set()
        self._callbacks: list[Callable[[PriceTick], None]] = []
        self._task: asyncio.Task | None = None
        self._running = False

        for symbol, price in seed_prices.items():
            self._symbols[symbol] = _SymbolState(price=price, high=price, low=price)
            self._watched.add(symbol)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def subscribe(self, callback: Callable[[PriceTick], None]) -> None:
        self._callbacks.append(callback)

    def get_watched_symbols(self) -> set[str]:
        return self._watched.copy()

    def add_symbol(self, symbol: str) -> None:
        self._watched.add(symbol)
        if symbol not in self._symbols:
            price = random.uniform(50, 5000)
            self._symbols[symbol] = _SymbolState(price=price, high=price, low=price)

    def remove_symbol(self, symbol: str) -> None:
        self._watched.discard(symbol)

    def inject_event(self, symbol: str, price_change_pct: float) -> None:
        """Inject a price event for demo purposes. E.g., inject_event("NIFTY", -0.05) = -5%."""
        if symbol in self._symbols:
            state = self._symbols[symbol]
            state.price *= 1 + price_change_pct
            state.price = max(state.price, 0.01)

    async def _run(self) -> None:
        while self._running:
            for symbol in list(self._watched):
                if symbol in self._symbols:
                    self._tick(symbol)
            await asyncio.sleep(self._tick_interval)

    def _tick(self, symbol: str) -> None:
        state = self._symbols[symbol]

        # Geometric Brownian Motion: dS = S * (mu*dt + sigma*dW)
        dt = self._tick_interval
        dw = random.gauss(0, math.sqrt(dt))
        change = state.price * (self._drift * dt + self._volatility * dw)
        state.price = max(state.price + change, 0.01)

        state.high = max(state.high, state.price)
        state.low = min(state.low, state.price)
        state.volume += random.randint(100, 5000)

        spread = state.price * 0.001  # 0.1% spread
        tick = PriceTick(
            symbol=symbol,
            price=round(state.price, 2),
            bid=round(state.price - spread / 2, 2),
            ask=round(state.price + spread / 2, 2),
            volume=state.volume,
            high=round(state.high, 2),
            low=round(state.low, 2),
            timestamp=time.time(),
        )

        for cb in self._callbacks:
            cb(tick)


class PriceService:
    """Wraps a PriceStream with caching and query methods."""

    def __init__(self, stream: PriceStream, cache_ttl: float = 30.0) -> None:
        self._stream = stream
        self._cache_ttl = cache_ttl
        self._latest: dict[str, PriceTick] = {}
        self._stream.subscribe(self._on_tick)

    def _on_tick(self, tick: PriceTick) -> None:
        self._latest[tick.symbol] = tick

    @property
    def stream(self) -> PriceStream:
        return self._stream

    async def start(self) -> None:
        await self._stream.start()

    async def stop(self) -> None:
        await self._stream.stop()

    async def get_price(self, symbol: str) -> PriceTick | None:
        tick = self._latest.get(symbol)
        if tick is None:
            return None
        if time.time() - tick.timestamp > self._cache_ttl:
            return None
        return tick

    async def get_quote(self, symbol: str) -> PriceTick | None:
        return await self.get_price(symbol)

    async def get_history(self, symbol: str, period: str = "1m") -> list[PriceBar]:
        """Generate simulated history. In real impl, this calls the provider."""
        tick = self._latest.get(symbol)
        if tick is None:
            return []

        bars = []
        base = tick.price
        days = {"1d": 1, "1w": 7, "1m": 30, "3m": 90}.get(period, 30)

        for i in range(days, 0, -1):
            noise = random.gauss(0, base * 0.02)
            close = base + noise - (i * base * 0.001)
            close = max(close, 0.01)
            bars.append(PriceBar(
                date=f"2026-{((2 * 30 - i) // 30) + 1:02d}-{((2 * 30 - i) % 30) + 1:02d}",
                open=round(close * (1 + random.uniform(-0.01, 0.01)), 2),
                high=round(close * (1 + abs(random.gauss(0, 0.015))), 2),
                low=round(close * (1 - abs(random.gauss(0, 0.015))), 2),
                close=round(close, 2),
                volume=random.randint(100000, 5000000),
            ))

        return bars
