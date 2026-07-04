from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from backend.core.market_model.service import build_market_feature_dataset

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:your_password@localhost:5432/taiwan_stock_game_mvp",
)
BUILD_MODE = os.getenv("MARKET_BUILD_MODE", "sample").strip().lower()
TARGET_ROWS = int(os.getenv("MARKET_TARGET_ROWS", "100000"))
OUTPUT_PATH = Path(os.getenv("MARKET_FEATURE_OUTPUT", str(ROOT_DIR / "data" / f"market_features_{BUILD_MODE}.csv")))
CALIBRATION_OUTPUT = Path(os.getenv("MARKET_CALIBRATION_OUTPUT", str(ROOT_DIR / "data" / f"market_calibration_{BUILD_MODE}.json")))
LIMIT_ROWS = int(os.getenv("MARKET_FEATURE_LIMIT_ROWS", "0"))


def main() -> None:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as db:
        dataset = build_market_feature_dataset(
            db,
            limit_rows=LIMIT_ROWS or None,
            build_mode=BUILD_MODE,
            target_rows=None if BUILD_MODE == "full" else TARGET_ROWS,
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT_PATH, index=False)
    from backend.core.market_model.service import export_calibration_profile

    export_calibration_profile(dataset, CALIBRATION_OUTPUT)
    print(f"Saved {len(dataset)} rows to {OUTPUT_PATH}")
    print(f"Saved calibration profile to {CALIBRATION_OUTPUT}")


if __name__ == "__main__":
    main()
