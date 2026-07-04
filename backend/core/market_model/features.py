from __future__ import annotations

import pandas as pd


def normalize_price_history_frame(
    df: pd.DataFrame,
    *,
    stock_column: str = "stock_id",
    date_column: str = "game_date",
    close_column: str = "close_price",
    volume_column: str = "trading_volume",
) -> pd.DataFrame:
    frame = df.copy()
    rename_map = {}
    if stock_column not in frame.columns and "stock_ticker" in frame.columns:
        rename_map["stock_ticker"] = stock_column
    if date_column not in frame.columns and "date" in frame.columns:
        rename_map["date"] = date_column
    if close_column not in frame.columns and "close" in frame.columns:
        rename_map["close"] = close_column
    if volume_column not in frame.columns and "volume" in frame.columns:
        rename_map["volume"] = volume_column
    if rename_map:
        frame = frame.rename(columns=rename_map)

    required = [stock_column, date_column, close_column]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required price columns: {', '.join(missing)}")

    frame[stock_column] = frame[stock_column].astype(str).str.strip()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    frame = frame.dropna(subset=[date_column, stock_column, close_column])
    frame = frame.sort_values([stock_column, date_column]).reset_index(drop=True)

    if volume_column not in frame.columns:
        frame[volume_column] = 0

    frame[close_column] = pd.to_numeric(frame[close_column], errors="coerce")
    frame[volume_column] = pd.to_numeric(frame[volume_column], errors="coerce").fillna(0)
    frame = frame.dropna(subset=[close_column])
    return frame


def add_rolling_market_features(
    df: pd.DataFrame,
    *,
    stock_column: str = "stock_id",
    date_column: str = "game_date",
    close_column: str = "close_price",
    volume_column: str = "trading_volume",
) -> pd.DataFrame:
    frame = normalize_price_history_frame(
        df,
        stock_column=stock_column,
        date_column=date_column,
        close_column=close_column,
        volume_column=volume_column,
    )

    frame["daily_return"] = frame.groupby(stock_column)[close_column].pct_change().fillna(0.0)
    frame["notional_volume"] = frame[close_column] * frame[volume_column]

    grouped = frame.groupby(stock_column, group_keys=False)
    frame["rolling_5_return"] = grouped["daily_return"].transform(lambda s: s.rolling(5, min_periods=1).mean())
    frame["rolling_20_return"] = grouped["daily_return"].transform(lambda s: s.rolling(20, min_periods=1).mean())
    frame["rolling_5_volatility"] = grouped["daily_return"].transform(
        lambda s: s.rolling(5, min_periods=2).std(ddof=0)
    )
    frame["rolling_20_volatility"] = grouped["daily_return"].transform(
        lambda s: s.rolling(20, min_periods=2).std(ddof=0)
    )
    frame["rolling_volume_mean"] = grouped[volume_column].transform(lambda s: s.rolling(20, min_periods=1).mean())
    frame["rolling_notional_volume_mean"] = grouped["notional_volume"].transform(
        lambda s: s.rolling(20, min_periods=1).mean()
    )
    frame["rolling_drawdown"] = grouped[close_column].transform(_rolling_drawdown)
    return frame


def add_market_regime_labels(df: pd.DataFrame, *, date_column: str = "game_date") -> pd.DataFrame:
    frame = df.copy()
    if date_column not in frame.columns:
        raise ValueError(f"Missing required date column: {date_column}")

    daily = frame.groupby(date_column)["daily_return"].agg(["mean", "std"]).reset_index()
    daily = daily.sort_values(date_column)
    daily["market_score"] = daily["mean"].rolling(20, min_periods=5).mean().fillna(daily["mean"])
    daily["market_volatility"] = daily["std"].rolling(20, min_periods=5).mean().fillna(daily["std"].fillna(0.0))

    q20 = daily["market_score"].quantile(0.2)
    q40 = daily["market_score"].quantile(0.4)
    q60 = daily["market_score"].quantile(0.6)
    q80 = daily["market_score"].quantile(0.8)

    def classify(score: float, volatility: float) -> str:
        if pd.isna(score):
            return "sideways"
        if volatility >= daily["market_volatility"].quantile(0.9) and score < q20:
            return "panic"
        if score <= q20:
            return "bear"
        if score <= q40:
            return "sideways"
        if score <= q60:
            return "sideways"
        if score <= q80:
            return "rebound"
        return "bull"

    daily["regime_label"] = [classify(score, volatility) for score, volatility in zip(daily["market_score"], daily["market_volatility"])]
    frame = frame.merge(daily[[date_column, "regime_label", "market_score", "market_volatility"]], on=date_column, how="left")
    return frame


def _rolling_drawdown(series: pd.Series) -> pd.Series:
    running_max = series.cummax()
    return (series / running_max) - 1.0

