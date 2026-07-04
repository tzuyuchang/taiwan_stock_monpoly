from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

RegimeLabel = Literal["bull", "bear", "sideways", "panic", "rebound"]


@dataclass(frozen=True)
class StockUniverseRecord:
    stock_id: str
    stock_name: str | None = None
    industry_category: str | None = None
    stock_type: str | None = None
    listing_date: date | None = None
    sector: str | None = None
    market_cap_bucket: str | None = None
    liquidity_bucket: str | None = None


@dataclass(frozen=True)
class MarketRegime:
    label: RegimeLabel
    score: float
    market_return: float
    market_volatility: float


@dataclass(frozen=True)
class MarketFeatureRow:
    stock_id: str
    game_date: date
    close_price: float
    daily_return: float
    rolling_5_return: float | None = None
    rolling_20_return: float | None = None
    rolling_5_volatility: float | None = None
    rolling_20_volatility: float | None = None
    rolling_volume_mean: float | None = None
    rolling_notional_volume_mean: float | None = None
    sector: str | None = None
    stock_type: str | None = None
    market_cap_bucket: str | None = None
    liquidity_bucket: str | None = None
    regime_label: str | None = None


@dataclass(frozen=True)
class MarketSimulationConfig:
    base_daily_volatility: float = 0.018
    market_beta_weight: float = 0.65
    sector_beta_weight: float = 0.35
    event_shock_weight: float = 1.0
    illiquid_slippage_penalty: float = 0.015
    min_price: float = 1.0
    max_daily_move: float = 0.15
    regime_volatility_multiplier: dict[str, float] = field(
        default_factory=lambda: {
            "bull": 0.85,
            "bear": 1.15,
            "sideways": 1.0,
            "panic": 1.8,
            "rebound": 1.25,
        }
    )

