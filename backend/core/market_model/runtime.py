from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import insert, select, text
from sqlalchemy.orm import Session

from .schema import MarketSimulationConfig
from .simulator import MarketSimulator
from .universe import load_stock_universe_records

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_OVERVIEW_PATH = ROOT_DIR / "data" / "taiwan_stock_overview.csv"
DEFAULT_CALIBRATION_PATH = ROOT_DIR / "data" / "market_calibration_full.json"


def load_market_runtime_config(calibration_path: str | Path | None = None) -> MarketSimulationConfig:
    path = Path(calibration_path) if calibration_path else DEFAULT_CALIBRATION_PATH
    if not path.exists():
        return MarketSimulationConfig()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return MarketSimulationConfig()

    return MarketSimulationConfig(
        base_daily_volatility=_safe_float(payload.get("return_stats", {}).get("std"), 0.018) or 0.018,
    )


def build_market_simulator(calibration_path: str | Path | None = None) -> MarketSimulator:
    return MarketSimulator(config=load_market_runtime_config(calibration_path))


def get_stock_universe_lookup(overview_path: str | Path | None = None) -> dict[str, dict[str, object]]:
    path = Path(overview_path) if overview_path else DEFAULT_OVERVIEW_PATH
    records = load_stock_universe_records(path)
    lookup: dict[str, dict[str, object]] = {}
    for record in records:
        lookup[record.stock_id] = asdict(record)
    return lookup


def get_market_date_seed(stock_id: str, game_date: date) -> int:
    digest = hashlib.sha256(f"{stock_id}:{game_date.isoformat()}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def fetch_latest_source_price(db: Session, table_name: str, stock_id: str, game_date: date) -> float | None:
    query = text(
        f"""
        SELECT close_price
        FROM public."{table_name}"
        WHERE stock_ticker = :stock_id
          AND game_date < :game_date
        ORDER BY game_date DESC
        LIMIT 1
        """
    )
    result = db.execute(query, {"stock_id": stock_id, "game_date": game_date}).scalar_one_or_none()
    if result is not None:
        return float(result)

    query = text(
        f"""
        SELECT close_price
        FROM public.finmind_taiwan_stock_price
        WHERE stock_id = :stock_id
          AND game_date <= :game_date
        ORDER BY game_date DESC
        LIMIT 1
        """
    )
    result = db.execute(query, {"stock_id": stock_id, "game_date": game_date}).scalar_one_or_none()
    if result is not None:
        return float(result)
    return None


def fetch_source_bar(db: Session, stock_id: str, game_date: date) -> dict[str, object] | None:
    query = text(
        """
        SELECT stock_id, game_date, trading_volume, trading_money, open_price, high_price, low_price, close_price, spread, trading_turnover
        FROM public.finmind_taiwan_stock_price
        WHERE stock_id = :stock_id
          AND game_date <= :game_date
        ORDER BY game_date DESC
        LIMIT 1
        """
    )
    row = db.execute(query, {"stock_id": stock_id, "game_date": game_date}).mappings().first()
    if row is None:
        return None
    return dict(row)


def simulate_and_store_market_bar(
    db: Session,
    *,
    stock_id: str,
    game_date: date,
    source_table: str = "historical_stock_data",
    calibration_path: str | Path | None = None,
    overview_path: str | Path | None = None,
) -> dict[str, object] | None:
    existing = db.execute(
        text(
            f"""
            SELECT stock_ticker, game_date, open_price, high_price, low_price, close_price, volume, event_type, event_impact
            FROM public."{source_table}"
            WHERE stock_ticker = :stock_id AND game_date = :game_date
            LIMIT 1
            """
        ),
        {"stock_id": stock_id, "game_date": game_date},
    ).mappings().first()
    if existing is not None:
        return dict(existing)

    previous_close = fetch_latest_source_price(db, source_table, stock_id, game_date)
    source_bar = fetch_source_bar(db, stock_id, game_date)
    if previous_close is None and source_bar is not None:
        previous_close = _safe_float(source_bar.get("close_price"), 1.0)
    if previous_close is None:
        previous_close = 1.0

    simulator = build_market_simulator(calibration_path)
    universe = get_stock_universe_lookup(overview_path)
    stock_meta = universe.get(stock_id, {})

    regime_label = _select_regime_label(game_date, calibration_path)
    market_return = _regime_market_return(regime_label)
    sector_return = _sector_drift(stock_meta.get("sector") or stock_meta.get("industry_category"), game_date)
    market_cap_bucket = (stock_meta.get("market_cap_bucket") or "small").lower()
    liquidity_bucket = (stock_meta.get("liquidity_bucket") or "low").lower()

    stock_beta = {"small": 1.2, "mid": 1.0, "large": 0.75}.get(market_cap_bucket, 1.0)
    sector_beta = 1.0
    volatility = {"low": 0.8, "medium": 1.0, "high": 1.25}.get(liquidity_bucket, 1.0)
    liquidity_penalty = {"low": 1.0, "medium": 0.4, "high": 0.1}.get(liquidity_bucket, 0.4)
    event_shock = _deterministic_event_shock(stock_id, game_date)
    base_volume = int(_safe_float(source_bar.get("trading_volume"), 100_000) if source_bar else 100_000)

    bar = simulator.simulate_bar(
        previous_close=previous_close,
        market_return=market_return,
        sector_return=sector_return,
        stock_beta=stock_beta,
        sector_beta=sector_beta,
        volatility=volatility,
        regime_label=regime_label,
        event_shock=event_shock,
        liquidity_penalty=liquidity_penalty,
        base_volume=base_volume,
    )

    row = {
        "stock_ticker": stock_id,
        "game_date": game_date,
        "open_price": bar.open_price,
        "high_price": bar.high_price,
        "low_price": bar.low_price,
        "close_price": bar.close_price,
        "volume": bar.volume,
        "event_type": regime_label,
        "event_impact": round(bar.close_price - bar.open_price, 4),
    }
    db.execute(
        text(
            f"""
            INSERT INTO public."{source_table}"
                (stock_ticker, game_date, open_price, high_price, low_price, close_price, volume, event_type, event_impact)
            VALUES
                (:stock_ticker, :game_date, :open_price, :high_price, :low_price, :close_price, :volume, :event_type, :event_impact)
            """
        ),
        row,
    )
    return row


def _select_regime_label(game_date: date, calibration_path: str | Path | None = None) -> str:
    path = Path(calibration_path) if calibration_path else DEFAULT_CALIBRATION_PATH
    labels = ["bull", "bear", "sideways", "panic", "rebound"]
    probabilities = [0.2] * len(labels)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            counts = payload.get("regime_counts", {})
            raw_weights = [int(counts.get(label, 0)) for label in labels]
            flattened = [math.sqrt(weight + 1.0) for weight in raw_weights]
            total = sum(flattened) or 1.0
            normalized = [weight / total for weight in flattened]
            probabilities = [0.7 * weight + 0.3 / len(labels) for weight in normalized]
        except Exception:
            probabilities = [0.2] * len(labels)

    rng = random.Random(get_market_date_seed("regime", game_date))
    return rng.choices(labels, weights=probabilities, k=1)[0]


def _regime_market_return(regime_label: str) -> float:
    return {
        "bull": 0.012,
        "bear": -0.012,
        "sideways": 0.001,
        "panic": -0.028,
        "rebound": 0.018,
    }.get(regime_label, 0.0)


def _sector_drift(sector: object | None, game_date: date) -> float:
    if not sector:
        return 0.0
    seed = get_market_date_seed(str(sector), game_date)
    rng = random.Random(seed)
    return rng.uniform(-0.008, 0.008)


def _deterministic_event_shock(stock_id: str, game_date: date) -> float:
    seed = get_market_date_seed(stock_id, game_date)
    rng = random.Random(seed)
    if rng.random() < 0.08:
        return rng.uniform(-0.04, 0.04)
    return 0.0


def _safe_float(value: object | None, default: float) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default
