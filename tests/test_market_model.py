from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.core.market_model.features import add_market_regime_labels, add_rolling_market_features
from backend.core.market_model.service import build_market_calibration_profile
from backend.core.market_model.simulator import MarketSimulator
from backend.core.market_model.universe import load_stock_universe_records, summarize_universe


def test_universe_loader_and_summary(tmp_path: Path) -> None:
    csv_path = tmp_path / "overview.csv"
    csv_path.write_text(
        "industry_category,stock_id,stock_name,type,date\n"
        "semiconductor,2330,TSMC,twse,2020-01-01\n"
        "financials,2881,Fubon,twse,2020-01-02\n",
        encoding="utf-8",
    )

    records = load_stock_universe_records(csv_path)
    summary = summarize_universe(records)

    assert len(records) == 2
    assert summary["total_records"] == 2
    assert summary["stock_types"]["twse"] == 2


def test_feature_generation_and_regime_labels() -> None:
    df = pd.DataFrame(
        {
            "stock_id": ["2330"] * 6 + ["2881"] * 6,
            "game_date": pd.date_range("2024-01-01", periods=6).tolist() * 2,
            "close_price": [100, 101, 102, 103, 104, 105, 50, 50.5, 51, 50.8, 51.2, 52],
            "trading_volume": [1000, 1100, 1200, 1150, 1300, 1250, 800, 810, 820, 830, 840, 850],
        }
    )

    features = add_rolling_market_features(df)
    labeled = add_market_regime_labels(features)

    assert "daily_return" in labeled.columns
    assert "regime_label" in labeled.columns
    assert labeled["rolling_5_return"].notna().any()


def test_market_simulator_returns_positive_price() -> None:
    sim = MarketSimulator()
    bar = sim.simulate_bar(previous_close=100.0, market_return=0.01, sector_return=0.005, volatility=1.2)

    assert bar.close_price >= 1.0
    assert bar.high_price >= bar.close_price
    assert bar.low_price <= bar.close_price


def test_calibration_profile_contains_basic_statistics() -> None:
    df = pd.DataFrame(
        {
            "stock_id": ["2330", "2330", "2881"],
            "game_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-01"]),
            "daily_return": [0.01, -0.02, 0.005],
            "regime_label": ["bull", "bear", "sideways"],
            "sector": ["semiconductor", "semiconductor", "financials"],
            "market_cap_bucket": ["large", "large", "mid"],
            "liquidity_bucket": ["high", "high", "medium"],
        }
    )

    profile = build_market_calibration_profile(df)

    assert profile["rows"] == 3
    assert profile["distinct_stocks"] == 2
    assert profile["regime_counts"]["bull"] == 1
    assert "mean" in profile["return_stats"]
