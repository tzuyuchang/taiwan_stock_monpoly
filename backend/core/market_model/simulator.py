from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .schema import MarketSimulationConfig


@dataclass
class SimulatedBar:
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    regime_label: str
    drift: float
    shock: float


class MarketSimulator:
    def __init__(self, config: MarketSimulationConfig | None = None, rng: random.Random | None = None) -> None:
        self.config = config or MarketSimulationConfig()
        self.rng = rng or random.Random()

    def simulate_next_close(
        self,
        *,
        previous_close: float,
        market_return: float = 0.0,
        sector_return: float = 0.0,
        stock_beta: float = 1.0,
        sector_beta: float = 1.0,
        volatility: float = 1.0,
        regime_label: str = "sideways",
        event_shock: float = 0.0,
        liquidity_penalty: float = 0.0,
    ) -> tuple[float, float, float]:
        regime_multiplier = self.config.regime_volatility_multiplier.get(regime_label, 1.0)
        drift = (
            market_return * stock_beta * self.config.market_beta_weight
            + sector_return * sector_beta * self.config.sector_beta_weight
            + event_shock * self.config.event_shock_weight
            - liquidity_penalty * self.config.illiquid_slippage_penalty
        )
        sigma = max(0.0001, self.config.base_daily_volatility * max(volatility, 0.2) * regime_multiplier)
        shock = self.rng.gauss(0.0, sigma)
        move = max(-self.config.max_daily_move, min(self.config.max_daily_move, drift + shock))
        next_close = max(self.config.min_price, previous_close * (1.0 + move))
        return next_close, drift, shock

    def simulate_bar(
        self,
        *,
        previous_close: float,
        market_return: float = 0.0,
        sector_return: float = 0.0,
        stock_beta: float = 1.0,
        sector_beta: float = 1.0,
        volatility: float = 1.0,
        regime_label: str = "sideways",
        event_shock: float = 0.0,
        liquidity_penalty: float = 0.0,
        base_volume: int = 100_000,
    ) -> SimulatedBar:
        close_price, drift, shock = self.simulate_next_close(
            previous_close=previous_close,
            market_return=market_return,
            sector_return=sector_return,
            stock_beta=stock_beta,
            sector_beta=sector_beta,
            volatility=volatility,
            regime_label=regime_label,
            event_shock=event_shock,
            liquidity_penalty=liquidity_penalty,
        )

        open_price = previous_close
        spread = abs(close_price - open_price)
        high_price = max(open_price, close_price) + max(spread * 0.25, open_price * 0.002)
        low_price = max(self.config.min_price, min(open_price, close_price) - max(spread * 0.25, open_price * 0.002))
        volume_multiplier = 1.0 + min(3.0, abs(drift + shock) * 15.0)
        if regime_label in {"panic", "bear"}:
            volume_multiplier *= 1.15
        volume = max(1, int(base_volume * volume_multiplier))
        return SimulatedBar(
            open_price=round(open_price, 2),
            high_price=round(high_price, 2),
            low_price=round(low_price, 2),
            close_price=round(close_price, 2),
            volume=volume,
            regime_label=regime_label,
            drift=drift,
            shock=shock,
        )

