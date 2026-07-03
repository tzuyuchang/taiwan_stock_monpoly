from __future__ import annotations

import logging
import os
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.getenv("FM_API_KEY")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:your_password@localhost:5432/taiwan_stock_game_mvp",
)
BASE_URL = "https://api.finmindtrade.com/api/v4/data"
DATASET = os.getenv("FINMIND_DATASET", "TaiwanStockPrice")
SOURCE_NAME = DATASET

STOCK_OVERVIEW_CSV = Path(
    os.getenv("STOCK_OVERVIEW_CSV", str(ROOT_DIR / "data" / "taiwan_stock_overview.csv"))
)

REQUEST_DELAY_SECONDS = int(os.getenv("FINMIND_REQUEST_DELAY_SECONDS", "10"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("FINMIND_REQUEST_TIMEOUT_SECONDS", "20"))
MAX_RETRIES = int(os.getenv("FINMIND_MAX_RETRIES", "3"))
CHUNK_SIZE = int(os.getenv("FINMIND_DB_CHUNK_SIZE", "1000"))
DRY_RUN = os.getenv("FINMIND_DRY_RUN", "0") == "1"
LIMIT_STOCKS = int(os.getenv("FINMIND_LIMIT_STOCKS", "0"))
STOCK_TYPE = os.getenv("FINMIND_STOCK_TYPE", "twse").strip().lower()
EXCLUDED_INDUSTRY_CATEGORIES = {
    "受益證券",
    "存託憑證",
    "etn",
    "創新板股票",
    "創新版股票",
}

END_DATE = date.today()
START_DATE = END_DATE - timedelta(days=8 * 365)
START_DATE_STR = START_DATE.strftime("%Y-%m-%d")
END_DATE_STR = END_DATE.strftime("%Y-%m-%d")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def normalize_stock_id_column(df: pd.DataFrame) -> pd.DataFrame:
    if "stock_id" in df.columns:
        return df

    candidate_columns = ["證券代號", "ticker", "Ticker", "symbol"]
    for column in candidate_columns:
        if column in df.columns:
            return df.rename(columns={column: "stock_id"})

    return df.rename(columns={df.columns[0]: "stock_id"})


def read_stock_list(filepath: Path) -> list[str]:
    if not filepath.exists():
        raise FileNotFoundError(f"Stock overview file not found: {filepath}")

    df = pd.read_csv(filepath)
    df = normalize_stock_id_column(df)

    if "stock_id" not in df.columns:
        raise ValueError(f"Could not find a stock id column in {filepath}")

    if "type" in df.columns:
        df["type"] = df["type"].astype(str).str.strip().str.lower()
        df = df[df["type"] == STOCK_TYPE]
    else:
        logging.warning("No 'type' column found in %s; skipping stock type filter.", filepath)

    if "industry_category" in df.columns:
        df["industry_category"] = df["industry_category"].astype(str).str.strip()
        df = df[~df["industry_category"].str.lower().isin(EXCLUDED_INDUSTRY_CATEGORIES)]
    else:
        logging.warning("No 'industry_category' column found in %s; skipping special instrument filter.", filepath)

    stock_ids = (
        df["stock_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .tolist()
    )
    return stock_ids


def ensure_table_exists(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS finmind_taiwan_stock_price (
                    id BIGSERIAL PRIMARY KEY,
                    stock_id VARCHAR(20) NOT NULL,
                    game_date DATE NOT NULL,
                    trading_volume BIGINT,
                    trading_money BIGINT,
                    open_price NUMERIC(12, 4),
                    high_price NUMERIC(12, 4),
                    low_price NUMERIC(12, 4),
                    close_price NUMERIC(12, 4),
                    spread NUMERIC(12, 4),
                    trading_turnover NUMERIC(12, 6),
                    source_name VARCHAR(50) NOT NULL DEFAULT 'TaiwanStockPrice',
                    retrieved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (stock_id, game_date, source_name)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_finmind_taiwan_stock_price_stock_date
                    ON finmind_taiwan_stock_price (stock_id, game_date)
                """
            )
        )


def fetch_finmind_data(
    dataset: str,
    stock_id: str,
    start_date: str,
    end_date: str,
    api_key: str,
) -> list[dict] | str | None:
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "dataset": dataset,
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logging.info("Fetching %s -> %s (attempt %s/%s)", dataset, stock_id, attempt, MAX_RETRIES)
            resp = requests.get(
                BASE_URL,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            if resp.status_code == 402:
                logging.error("FinMind rate limit reached for %s: %s", stock_id, resp.text[:200])
                return "RATE_LIMIT"

            if resp.status_code in {429, 500, 502, 503, 504}:
                logging.warning(
                    "Transient HTTP error for %s: %s %s",
                    stock_id,
                    resp.status_code,
                    resp.text[:200],
                )
                if attempt < MAX_RETRIES:
                    time.sleep(min(60, REQUEST_DELAY_SECONDS * attempt))
                    continue
                return None

            if resp.status_code != 200:
                logging.error("HTTP error for %s: %s %s", stock_id, resp.status_code, resp.text[:200])
                return None

            payload = resp.json()
            data = payload.get("data", [])
            if data:
                logging.info("Fetched %s rows for %s", len(data), stock_id)
                return data

            logging.info("No rows returned for %s", stock_id)
            return None

        except requests.exceptions.RequestException as exc:
            logging.warning("Request failed for %s: %s", stock_id, exc)
            if attempt < MAX_RETRIES:
                time.sleep(min(60, REQUEST_DELAY_SECONDS * attempt))
                continue
            return None

    return None


def normalize_price_frame(raw_rows: list[dict], stock_id: str) -> pd.DataFrame:
    df = pd.DataFrame(raw_rows)
    if df.empty:
        return df

    rename_map = {
        "date": "game_date",
        "Trading_Volume": "trading_volume",
        "Trading_money": "trading_money",
        "open": "open_price",
        "max": "high_price",
        "min": "low_price",
        "close": "close_price",
        "spread": "spread",
        "Trading_turnover": "trading_turnover",
    }
    df = df.rename(columns=rename_map)

    required_columns = [
        "stock_id",
        "game_date",
        "trading_volume",
        "trading_money",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "spread",
        "trading_turnover",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = None

    df["stock_id"] = stock_id
    df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date

    numeric_columns = [
        "trading_volume",
        "trading_money",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "spread",
        "trading_turnover",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["game_date", "stock_id"])
    df = df.astype(object).where(pd.notna(df), None)
    return df[required_columns]


def chunked(items: list[dict], chunk_size: int) -> Iterable[list[dict]]:
    for idx in range(0, len(items), chunk_size):
        yield items[idx : idx + chunk_size]


def upsert_rows(engine, table, rows: list[dict]) -> int:
    if not rows:
        return 0

    total_written = 0
    with engine.begin() as conn:
        for batch in chunked(rows, CHUNK_SIZE):
            stmt = pg_insert(table).values(batch)
            update_columns = {
                "trading_volume": stmt.excluded.trading_volume,
                "trading_money": stmt.excluded.trading_money,
                "open_price": stmt.excluded.open_price,
                "high_price": stmt.excluded.high_price,
                "low_price": stmt.excluded.low_price,
                "close_price": stmt.excluded.close_price,
                "spread": stmt.excluded.spread,
                "trading_turnover": stmt.excluded.trading_turnover,
                "retrieved_at": func.now(),
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["stock_id", "game_date", "source_name"],
                set_=update_columns,
            )
            conn.execute(stmt)
            total_written += len(batch)

    return total_written


def main() -> None:
    if not API_KEY:
        raise RuntimeError("FM_API_KEY is missing from .env or environment variables.")

    stock_ids = read_stock_list(STOCK_OVERVIEW_CSV)
    if LIMIT_STOCKS > 0:
        stock_ids = stock_ids[:LIMIT_STOCKS]
    logging.info("Loaded %s stock ids from %s", len(stock_ids), STOCK_OVERVIEW_CSV)
    logging.info("Target dataset: %s", DATASET)
    logging.info("Date range: %s -> %s", START_DATE_STR, END_DATE_STR)
    logging.info("Stock type filter: %s", STOCK_TYPE)
    if LIMIT_STOCKS > 0:
        logging.info("Stock limit enabled: first %s stocks only", LIMIT_STOCKS)

    if DRY_RUN:
        logging.info("Dry-run enabled. No API calls or database writes will be performed.")
        logging.info("Database URL is configured: %s", bool(DATABASE_URL))
        logging.info("Would create/load table: finmind_taiwan_stock_price")
        logging.info("Sample stock ids: %s", ", ".join(stock_ids[:5]) if stock_ids else "(none)")
        return

    engine = create_engine(DATABASE_URL, future=True)
    ensure_table_exists(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine, only=["finmind_taiwan_stock_price"])
    table = metadata.tables["finmind_taiwan_stock_price"]

    total_written = 0
    total_stocks = 0

    for stock_id in stock_ids:
        total_stocks += 1
        logging.info("Processing %s/%s: %s", total_stocks, len(stock_ids), stock_id)

        raw_data = fetch_finmind_data(
            DATASET,
            stock_id,
            START_DATE_STR,
            END_DATE_STR,
            API_KEY,
        )

        if raw_data == "RATE_LIMIT":
            logging.error("Stopping because FinMind rate limit was reached.")
            break

        if not raw_data:
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        frame = normalize_price_frame(raw_data, stock_id)
        if frame.empty:
            logging.info("No clean rows to store for %s", stock_id)
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        records = frame.to_dict(orient="records")
        for record in records:
            record["source_name"] = SOURCE_NAME

        written = upsert_rows(engine, table, records)
        total_written += written
        logging.info("Stored %s rows for %s", written, stock_id)

        time.sleep(REQUEST_DELAY_SECONDS)

    logging.info("Finished. Total rows written: %s", total_written)


if __name__ == "__main__":
    main()
