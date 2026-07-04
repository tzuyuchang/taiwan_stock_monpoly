from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from .features import add_market_regime_labels, add_rolling_market_features
from .schema import StockUniverseRecord
from .universe import load_stock_universe_records, summarize_universe

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_STOCK_OVERVIEW_CSV = ROOT_DIR / "data" / "taiwan_stock_overview.csv"


def load_stock_universe_records_safe(path: str | Path | None = None) -> list[StockUniverseRecord]:
    target = Path(path) if path else DEFAULT_STOCK_OVERVIEW_CSV
    return load_stock_universe_records(target)


def build_market_feature_dataset(
    db: Session,
    *,
    limit_rows: int | None = None,
    source_table: str = "finmind_taiwan_stock_price",
    overview_path: str | Path | None = None,
    build_mode: str = "sample",
    target_rows: int | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    overview_df = _load_universe_metadata(overview_path)

    query = f"""
        SELECT *
        FROM public."{source_table}"
        ORDER BY 1 ASC
    """
    if limit_rows is not None:
        query += f" LIMIT {int(limit_rows)}"

    raw_df = pd.read_sql(text(query), db.bind)
    if raw_df.empty:
        return raw_df

    if "stock_ticker" in raw_df.columns and "stock_id" not in raw_df.columns:
        raw_df = raw_df.rename(columns={"stock_ticker": "stock_id"})
    if "trading_volume" not in raw_df.columns and "volume" in raw_df.columns:
        raw_df = raw_df.rename(columns={"volume": "trading_volume"})
    if "close_price" not in raw_df.columns and "close" in raw_df.columns:
        raw_df = raw_df.rename(columns={"close": "close_price"})

    frame = add_rolling_market_features(raw_df, stock_column="stock_id", date_column="game_date", close_column="close_price", volume_column="trading_volume")
    frame = add_market_regime_labels(frame, date_column="game_date")
    if not overview_df.empty:
        frame = _attach_universe_metadata(frame, overview_df)

    frame = _attach_proxy_profiles(frame)
    frame = _apply_sampling_mode(
        frame,
        build_mode=build_mode,
        target_rows=target_rows,
        random_state=random_state,
    )

    return frame


def get_market_simulation_summary(db: Session, *, overview_path: str | Path | None = None) -> dict[str, object]:
    overview_records = load_stock_universe_records_safe(overview_path)
    overview_summary = summarize_universe(overview_records)

    total_finmind_rows = db.execute(text('SELECT COUNT(*) FROM public."finmind_taiwan_stock_price"')).scalar_one()
    total_historical_rows = db.execute(text('SELECT COUNT(*) FROM public."historical_stock_data"')).scalar_one()
    min_date, max_date = db.execute(
        text('SELECT MIN(game_date), MAX(game_date) FROM public."finmind_taiwan_stock_price"')
    ).one()
    distinct_stock_ids = db.execute(text('SELECT COUNT(DISTINCT stock_id) FROM public."finmind_taiwan_stock_price"')).scalar_one()

    return {
        "overview": overview_summary,
        "price_tables": {
            "finmind_taiwan_stock_price_rows": total_finmind_rows,
            "historical_stock_data_rows": total_historical_rows,
            "distinct_stock_ids": distinct_stock_ids,
            "game_date_min": min_date.isoformat() if min_date else None,
            "game_date_max": max_date.isoformat() if max_date else None,
        },
        "feature_ready": total_finmind_rows > 0,
    }


def build_market_calibration_profile(frame: pd.DataFrame) -> dict[str, object]:
    if frame.empty:
        return {
            "rows": 0,
            "distinct_stocks": 0,
            "date_range": {"min": None, "max": None},
            "regime_counts": {},
            "sector_counts": {},
            "market_cap_bucket_counts": {},
            "liquidity_bucket_counts": {},
            "return_stats": {},
        }

    return_series = frame["daily_return"].dropna()
    return {
        "rows": int(len(frame)),
        "distinct_stocks": int(frame["stock_id"].nunique()) if "stock_id" in frame.columns else 0,
        "date_range": {
            "min": _safe_iso(frame["game_date"].min()) if "game_date" in frame.columns else None,
            "max": _safe_iso(frame["game_date"].max()) if "game_date" in frame.columns else None,
        },
        "regime_counts": _series_counts(frame, "regime_label"),
        "sector_counts": _series_counts(frame, "sector"),
        "market_cap_bucket_counts": _series_counts(frame, "market_cap_bucket"),
        "liquidity_bucket_counts": _series_counts(frame, "liquidity_bucket"),
        "return_stats": {
            "mean": float(return_series.mean()) if not return_series.empty else None,
            "std": float(return_series.std(ddof=0)) if not return_series.empty else None,
            "p01": float(return_series.quantile(0.01)) if not return_series.empty else None,
            "p05": float(return_series.quantile(0.05)) if not return_series.empty else None,
            "p50": float(return_series.quantile(0.5)) if not return_series.empty else None,
            "p95": float(return_series.quantile(0.95)) if not return_series.empty else None,
            "p99": float(return_series.quantile(0.99)) if not return_series.empty else None,
        },
    }


def export_calibration_profile(frame: pd.DataFrame, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    profile = build_market_calibration_profile(frame)
    output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def _bucket_from_series(series: pd.Series, labels: list[str]) -> pd.Series:
    if series.empty:
        return pd.Series(dtype="object")

    valid = series.dropna()
    if valid.empty:
        return pd.Series([labels[0]] * len(series), index=series.index)

    try:
        buckets = pd.qcut(valid.rank(method="first"), q=min(len(labels), valid.nunique()), labels=labels[: min(len(labels), valid.nunique())])
        result = pd.Series(index=series.index, dtype="object")
        result.loc[valid.index] = buckets.astype(str)
        result = result.fillna(labels[0])
        return result
    except Exception:
        return pd.Series([labels[0]] * len(series), index=series.index)


def _load_universe_metadata(overview_path: str | Path | None = None) -> pd.DataFrame:
    overview_records = load_stock_universe_records_safe(overview_path)
    overview_df = pd.DataFrame([record.__dict__ for record in overview_records])
    if overview_df.empty:
        return pd.DataFrame(
            columns=[
                "stock_id",
                "stock_name",
                "industry_category",
                "stock_type",
                "listing_date",
                "sector",
                "market_cap_bucket",
                "liquidity_bucket",
            ]
        )

    overview_df["listing_date"] = pd.to_datetime(overview_df["listing_date"], errors="coerce")
    overview_df = (
        overview_df.sort_values(["stock_id", "listing_date"], na_position="last")
        .drop_duplicates(subset=["stock_id"], keep="last")
        .reset_index(drop=True)
    )
    overview_df["sector"] = overview_df["sector"].fillna(overview_df["industry_category"])
    return overview_df


def _attach_universe_metadata(frame: pd.DataFrame, overview_df: pd.DataFrame) -> pd.DataFrame:
    if overview_df.empty:
        return frame

    metadata_columns = ["stock_id", "stock_name", "industry_category", "stock_type", "sector", "market_cap_bucket", "liquidity_bucket"]
    merge_df = overview_df[metadata_columns].copy()
    merge_df = merge_df.rename(
        columns={
            "market_cap_bucket": "market_cap_bucket_universe",
            "liquidity_bucket": "liquidity_bucket_universe",
            "stock_type": "stock_type_universe",
            "sector": "sector_universe",
        }
    )
    frame = frame.merge(merge_df, on="stock_id", how="left")
    for column in ["sector", "stock_type", "market_cap_bucket", "liquidity_bucket"]:
        if column not in frame.columns:
            frame[column] = pd.NA

    frame["sector"] = frame["sector"].fillna(frame["sector_universe"])
    frame["stock_type"] = frame["stock_type"].fillna(frame["stock_type_universe"])
    frame["market_cap_bucket"] = frame["market_cap_bucket"].fillna(frame["market_cap_bucket_universe"])
    frame["liquidity_bucket"] = frame["liquidity_bucket"].fillna(frame["liquidity_bucket_universe"])
    frame = frame.drop(
        columns=[
            c
            for c in [
                "sector_universe",
                "stock_type_universe",
                "market_cap_bucket_universe",
                "liquidity_bucket_universe",
            ]
            if c in frame.columns
        ]
    )
    return frame


def _attach_proxy_profiles(frame: pd.DataFrame) -> pd.DataFrame:
    stock_profile = (
        frame.groupby("stock_id", as_index=False)
        .agg(
            proxy_market_cap=("notional_volume", "median"),
            proxy_liquidity=("trading_volume", "median"),
            proxy_close=("close_price", "median"),
        )
    )
    stock_profile["market_cap_bucket_proxy"] = _bucket_from_series(stock_profile["proxy_market_cap"], ["small", "mid", "large"])
    stock_profile["liquidity_bucket_proxy"] = _bucket_from_series(stock_profile["proxy_liquidity"], ["low", "medium", "high"])
    total_proxy_market_cap = stock_profile["proxy_market_cap"].sum()
    stock_profile["market_cap_share_proxy"] = (
        stock_profile["proxy_market_cap"] / total_proxy_market_cap if total_proxy_market_cap else 0.0
    )

    frame = frame.merge(
        stock_profile[
            [
                "stock_id",
                "proxy_market_cap",
                "proxy_liquidity",
                "market_cap_bucket_proxy",
                "liquidity_bucket_proxy",
                "market_cap_share_proxy",
            ]
        ],
        on="stock_id",
        how="left",
    )

    for column in ["market_cap_bucket", "liquidity_bucket"]:
        if column not in frame.columns:
            frame[column] = pd.NA

    frame["market_cap_bucket"] = frame["market_cap_bucket"].fillna(frame["market_cap_bucket_proxy"])
    frame["liquidity_bucket"] = frame["liquidity_bucket"].fillna(frame["liquidity_bucket_proxy"])
    frame = frame.drop(columns=["market_cap_bucket_proxy", "liquidity_bucket_proxy"])
    return frame


def _apply_sampling_mode(
    frame: pd.DataFrame,
    *,
    build_mode: str,
    target_rows: int | None,
    random_state: int,
) -> pd.DataFrame:
    if frame.empty:
        return frame

    mode = build_mode.strip().lower()
    if mode == "full" or target_rows is None:
        return frame
    if mode == "sample":
        return frame.sample(n=min(target_rows, len(frame)), random_state=random_state).sort_values(["stock_id", "game_date"]).reset_index(drop=True)
    if mode == "stratified":
        return _stratified_sample(frame, target_rows=target_rows, random_state=random_state)
    raise ValueError(f"Unknown build_mode: {build_mode}")


def _stratified_sample(frame: pd.DataFrame, *, target_rows: int, random_state: int) -> pd.DataFrame:
    if target_rows >= len(frame):
        return frame.sort_values(["stock_id", "game_date"]).reset_index(drop=True)

    working = frame.copy()
    working["trade_year"] = pd.to_datetime(working["game_date"]).dt.year.astype("Int64")
    stratify_columns = ["sector", "market_cap_bucket", "liquidity_bucket", "trade_year"]
    for column in stratify_columns:
        if column not in working.columns:
            working[column] = "unknown"
    working[stratify_columns] = working[stratify_columns].fillna("unknown").astype(str)

    strata = working.groupby(stratify_columns, dropna=False)
    strata_keys = list(strata.groups.keys())
    if not strata_keys:
        return working.drop(columns=["trade_year"]).sort_values(["stock_id", "game_date"]).reset_index(drop=True)

    base_allocation = max(1, target_rows // len(strata_keys))
    remainder = target_rows - base_allocation * len(strata_keys)
    sampled_parts: list[pd.DataFrame] = []

    for index, (_, group) in enumerate(strata):
        n = min(len(group), base_allocation + (1 if index < remainder else 0))
        sampled_parts.append(group.sample(n=n, random_state=random_state + index))

    sampled = pd.concat(sampled_parts, ignore_index=True)
    if len(sampled) > target_rows:
        sampled = sampled.sample(n=target_rows, random_state=random_state)
    sampled = sampled.sort_values(["stock_id", "game_date"]).reset_index(drop=True)
    return sampled.drop(columns=["trade_year"], errors="ignore")


def _series_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in frame.columns:
        return {}
    counts = Counter(frame[column].fillna("unknown").astype(str))
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _safe_iso(value: object) -> str | None:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
