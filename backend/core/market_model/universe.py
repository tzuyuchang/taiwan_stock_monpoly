from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from .schema import StockUniverseRecord


def _read_csv_with_fallback(path: Path) -> pd.DataFrame:
    encodings = ("utf-8-sig", "utf-8", "cp950", "big5")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception as exc:  # pragma: no cover - fallback path
            last_error = exc
    raise ValueError(f"Failed to read {path} with supported encodings") from last_error


def normalize_stock_overview_frame(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Stock overview file not found: {csv_path}")

    df = _read_csv_with_fallback(csv_path)
    df.columns = [str(col).strip().lower() for col in df.columns]

    if "stock_id" not in df.columns:
        candidate_columns = ["ticker", "symbol", "證券代號"]
        for candidate in candidate_columns:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "stock_id"})
                break

    if "stock_id" not in df.columns:
        raise ValueError(f"Could not find a stock_id column in {csv_path}")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    for column in ("stock_id", "stock_name", "industry_category", "type"):
        if column in df.columns:
            df[column] = df[column].astype(str).str.strip()

    return df


def load_stock_universe_records(path: str | Path) -> list[StockUniverseRecord]:
    df = normalize_stock_overview_frame(path)
    records: list[StockUniverseRecord] = []
    for row in df.to_dict(orient="records"):
        listing_date = row.get("date")
        if pd.isna(listing_date):
            listing_date = None
        elif isinstance(listing_date, str):
            listing_date = pd.to_datetime(listing_date, errors="coerce")
            listing_date = listing_date.date() if not pd.isna(listing_date) else None

        records.append(
            StockUniverseRecord(
                stock_id=str(row.get("stock_id", "")).strip(),
                stock_name=_clean_optional_text(row.get("stock_name")),
                industry_category=_clean_optional_text(row.get("industry_category")),
                stock_type=_clean_optional_text(row.get("type")),
                listing_date=listing_date,
            )
        )
    return [record for record in records if record.stock_id]


def summarize_universe(records: Iterable[StockUniverseRecord]) -> dict[str, object]:
    stock_types: dict[str, int] = {}
    industry_categories: dict[str, int] = {}
    total = 0

    for record in records:
        total += 1
        if record.stock_type:
            stock_types[record.stock_type] = stock_types.get(record.stock_type, 0) + 1
        if record.industry_category:
            industry_categories[record.industry_category] = industry_categories.get(record.industry_category, 0) + 1

    return {
        "total_records": total,
        "stock_types": dict(sorted(stock_types.items(), key=lambda item: (-item[1], item[0]))),
        "industry_categories": dict(sorted(industry_categories.items(), key=lambda item: (-item[1], item[0]))),
    }


def _clean_optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None

