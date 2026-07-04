from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import MetaData, Table, delete, insert, select, update
from sqlalchemy.orm import Session

from . import time_engine
from .time_engine import get_current_game_date, advance_game_date, get_todays_stock_data, simulate_and_store_market_bar


gameplay_metadata = MetaData()
player_assets_table = Table("player_assets", gameplay_metadata, autoload_with=time_engine.engine)


class PlayerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    destiny: str = Field(min_length=1, max_length=50)
    intelligence: int = Field(default=0, ge=0, le=100)
    luck: int = Field(default=0, ge=0, le=100)
    work_ethic: int = Field(default=0, ge=0, le=100)
    leadership: int = Field(default=0, ge=0, le=100)
    analysis: int = Field(default=0, ge=0, le=100)
    cash: int = Field(default=10000, ge=0)
    stamina: int = Field(default=100, ge=0, le=100)


class WorkActionRequest(BaseModel):
    player_id: int
    effort: int = Field(default=1, ge=1, le=3)


class GambleActionRequest(BaseModel):
    player_id: int
    stake: int = Field(ge=1)


class TradeActionRequest(BaseModel):
    player_id: int
    stock_ticker: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=1)
    game_date: date | None = None


def create_player(db: Session, payload: PlayerCreateRequest) -> dict[str, Any]:
    stmt = (
        insert(time_engine.player_profile_table)
        .values(
            name=payload.name,
            destiny=payload.destiny,
            intelligence=payload.intelligence,
            luck=payload.luck,
            work_ethic=payload.work_ethic,
            leadership=payload.leadership,
            analysis=payload.analysis,
            cash=payload.cash,
            stamina=payload.stamina,
        )
        .returning(*time_engine.player_profile_table.c)
    )
    row = db.execute(stmt).mappings().one()
    db.commit()
    return dict(row)


def get_player(db: Session, player_id: int) -> dict[str, Any]:
    row = db.execute(
        select(time_engine.player_profile_table).where(time_engine.player_profile_table.c.player_id == player_id)
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return dict(row)


def list_players(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(select(time_engine.player_profile_table).order_by(time_engine.player_profile_table.c.player_id.asc())).mappings().all()
    return [dict(row) for row in rows]


def advance_one_day(db: Session) -> dict[str, Any]:
    current_date = get_current_game_date(db)
    next_date = current_date + timedelta(days=1)
    advance_game_date(db, next_date)

    players = db.execute(select(time_engine.player_profile_table)).mappings().all()
    updated_players = 0
    for row in players:
        new_stamina = min(100, int(row["stamina"] or 0) + 5)
        db.execute(
            update(time_engine.player_profile_table)
            .where(time_engine.player_profile_table.c.player_id == row["player_id"])
            .values(stamina=new_stamina)
        )
        updated_players += 1

    db.commit()
    return {
        "current_game_date": current_date.isoformat(),
        "next_game_date": next_date.isoformat(),
        "players_updated": updated_players,
    }


def finish_day(db: Session, player_id: int) -> dict[str, Any]:
    player = get_player(db, player_id)
    current_date = get_current_game_date(db)
    holdings = list_player_positions(db, player_id)
    return {
        "status": "completed",
        "game_date": current_date.isoformat(),
        "player": player,
        "positions": holdings,
    }


def perform_work(db: Session, payload: WorkActionRequest) -> dict[str, Any]:
    player = get_player(db, payload.player_id)
    stamina_cost = 10 * payload.effort
    if int(player["stamina"] or 0) < stamina_cost:
        raise HTTPException(status_code=400, detail="Not enough stamina")

    payout = int(
        round(
            1000
            + (int(player["work_ethic"] or 0) * 120)
            + (int(player["intelligence"] or 0) * 40)
            + (int(player["analysis"] or 0) * 30)
            + (int(player["leadership"] or 0) * 20)
        )
    )
    new_cash = int(player["cash"] or 0) + payout
    new_stamina = int(player["stamina"] or 0) - stamina_cost

    db.execute(
        update(time_engine.player_profile_table)
        .where(time_engine.player_profile_table.c.player_id == payload.player_id)
        .values(cash=new_cash, stamina=new_stamina)
    )
    db.commit()

    return {
        "player_id": payload.player_id,
        "action": "work",
        "earned_cash": payout,
        "cash": new_cash,
        "stamina": new_stamina,
    }


def perform_gamble(db: Session, payload: GambleActionRequest) -> dict[str, Any]:
    player = get_player(db, payload.player_id)
    cash = int(player["cash"] or 0)
    if payload.stake > cash:
        raise HTTPException(status_code=400, detail="Stake exceeds current cash")

    current_date = get_current_game_date(db)
    seed = f"{payload.player_id}:{payload.stake}:{current_date.isoformat()}"
    rng = random.Random(seed)
    luck = int(player["luck"] or 0)
    win_chance = min(0.9, max(0.1, 0.35 + (luck * 0.005)))
    win = rng.random() < win_chance

    cash_delta = payload.stake if win else -payload.stake
    new_cash = cash + cash_delta

    db.execute(
        update(time_engine.player_profile_table)
        .where(time_engine.player_profile_table.c.player_id == payload.player_id)
        .values(cash=new_cash)
    )
    db.commit()

    return {
        "player_id": payload.player_id,
        "action": "gamble",
        "stake": payload.stake,
        "result": "win" if win else "lose",
        "cash_delta": cash_delta,
        "cash": new_cash,
    }


def buy_stock(db: Session, payload: TradeActionRequest) -> dict[str, Any]:
    game_date = payload.game_date or get_current_game_date(db)
    player = get_player(db, payload.player_id)
    stock_ticker = _normalize_stock_ticker(payload.stock_ticker)
    price_info = get_todays_stock_data(db, stock_ticker, game_date)
    if not price_info:
        price_info = simulate_and_store_market_bar(db, stock_id=stock_ticker, game_date=game_date)
    if not price_info:
        raise HTTPException(status_code=404, detail="Stock price not available")

    price = float(price_info["close_price"])
    total_cost = int(round(price * payload.quantity))
    cash = int(player["cash"] or 0)
    if total_cost > cash:
        raise HTTPException(status_code=400, detail="Not enough cash")

    current_position = _get_player_stock_position(db, payload.player_id, stock_ticker)
    if current_position is None:
        asset_details = {
            "stock_id": stock_ticker,
            "quantity": payload.quantity,
            "avg_price": price,
        }
        db.execute(
            insert(player_assets_table).values(
                player_id=payload.player_id,
                asset_type="stock",
                asset_details=asset_details,
            )
        )
    else:
        new_quantity = int(current_position["quantity"]) + payload.quantity
        existing_quantity = int(current_position["quantity"])
        existing_avg_price = float(current_position["avg_price"])
        new_avg_price = ((existing_avg_price * existing_quantity) + (price * payload.quantity)) / new_quantity
        db.execute(
            update(player_assets_table)
            .where(player_assets_table.c.asset_id == current_position["asset_id"])
            .values(
                asset_details={
                    "stock_id": stock_ticker,
                    "quantity": new_quantity,
                    "avg_price": round(new_avg_price, 4),
                }
            )
        )

    new_cash = cash - total_cost
    db.execute(
        update(time_engine.player_profile_table)
        .where(time_engine.player_profile_table.c.player_id == payload.player_id)
        .values(cash=new_cash)
    )
    db.commit()

    return {
        "player_id": payload.player_id,
        "action": "buy",
        "stock_ticker": stock_ticker,
        "quantity": payload.quantity,
        "price": price,
        "total_cost": total_cost,
        "cash": new_cash,
    }


def sell_stock(db: Session, payload: TradeActionRequest) -> dict[str, Any]:
    game_date = payload.game_date or get_current_game_date(db)
    player = get_player(db, payload.player_id)
    stock_ticker = _normalize_stock_ticker(payload.stock_ticker)
    current_position = _get_player_stock_position(db, payload.player_id, stock_ticker)
    if current_position is None:
        raise HTTPException(status_code=404, detail="No stock position found")

    owned_quantity = int(current_position["quantity"])
    if payload.quantity > owned_quantity:
        raise HTTPException(status_code=400, detail="Not enough shares")

    price_info = get_todays_stock_data(db, stock_ticker, game_date)
    if not price_info:
        price_info = simulate_and_store_market_bar(db, stock_id=stock_ticker, game_date=game_date)
    if not price_info:
        raise HTTPException(status_code=404, detail="Stock price not available")

    price = float(price_info["close_price"])
    proceeds = int(round(price * payload.quantity))
    new_cash = int(player["cash"] or 0) + proceeds
    remaining = owned_quantity - payload.quantity

    if remaining <= 0:
        db.execute(delete(player_assets_table).where(player_assets_table.c.asset_id == current_position["asset_id"]))
    else:
        existing_avg_price = float(current_position["avg_price"])
        db.execute(
            update(player_assets_table)
            .where(player_assets_table.c.asset_id == current_position["asset_id"])
            .values(
                asset_details={
                    "stock_id": stock_ticker,
                    "quantity": remaining,
                    "avg_price": round(existing_avg_price, 4),
                }
            )
        )

    db.execute(
        update(time_engine.player_profile_table)
        .where(time_engine.player_profile_table.c.player_id == payload.player_id)
        .values(cash=new_cash)
    )
    db.commit()

    return {
        "player_id": payload.player_id,
        "action": "sell",
        "stock_ticker": stock_ticker,
        "quantity": payload.quantity,
        "price": price,
        "proceeds": proceeds,
        "cash": new_cash,
        "remaining_quantity": max(remaining, 0),
    }


def list_player_positions(db: Session, player_id: int | None = None) -> list[dict[str, Any]]:
    stmt = select(player_assets_table).where(player_assets_table.c.asset_type == "stock")
    if player_id is not None:
        stmt = stmt.where(player_assets_table.c.player_id == player_id)
    rows = db.execute(stmt.order_by(player_assets_table.c.player_id.asc(), player_assets_table.c.asset_id.asc())).mappings().all()
    positions: list[dict[str, Any]] = []
    for row in rows:
        details = row.get("asset_details") or {}
        positions.append(
            {
                "asset_id": row["asset_id"],
                "player_id": row["player_id"],
                "stock_id": details.get("stock_id"),
                "quantity": int(details.get("quantity") or 0),
                "avg_price": float(details.get("avg_price") or 0.0),
            }
        )
    return positions


def get_player_snapshot(db: Session, player_id: int) -> dict[str, Any]:
    player = get_player(db, player_id)
    positions = list_player_positions(db, player_id)
    current_date = get_current_game_date(db)
    return {
        "player": player,
        "game_date": current_date.isoformat(),
        "positions": positions,
    }


def get_player_portfolio(db: Session, player_id: int) -> dict[str, Any]:
    player = get_player(db, player_id)
    game_date = get_current_game_date(db)
    positions = list_player_positions(db, player_id)

    enriched_positions: list[dict[str, Any]] = []
    total_market_value = 0.0
    total_cost_basis = 0.0
    for position in positions:
        stock_id = _normalize_stock_ticker(str(position.get("stock_id") or ""))
        price_info = get_todays_stock_data(db, stock_id, game_date)
        if not price_info:
            price_info = simulate_and_store_market_bar(db, stock_id=stock_id, game_date=game_date)
        current_price = float(price_info["close_price"]) if price_info else 0.0
        quantity = int(position["quantity"])
        avg_price = float(position["avg_price"])
        cost_basis = avg_price * quantity
        market_value = current_price * quantity
        total_cost_basis += cost_basis
        total_market_value += market_value
        enriched_positions.append(
            {
                **position,
                "current_price": round(current_price, 4),
                "market_value": round(market_value, 4),
                "cost_basis": round(cost_basis, 4),
                "unrealized_pnl": round(market_value - cost_basis, 4),
            }
        )

    return {
        "player": player,
        "game_date": game_date.isoformat(),
        "cash": int(player["cash"] or 0),
        "positions": enriched_positions,
        "totals": {
            "cost_basis": round(total_cost_basis, 4),
            "market_value": round(total_market_value, 4),
            "unrealized_pnl": round(total_market_value - total_cost_basis, 4),
            "net_worth": round(float(player["cash"] or 0) + total_market_value, 4),
        },
    }


def _get_player_stock_position(db: Session, player_id: int, stock_ticker: str) -> dict[str, Any] | None:
    row = db.execute(
        select(player_assets_table).where(
            player_assets_table.c.player_id == player_id,
            player_assets_table.c.asset_type == "stock",
        )
    ).mappings().all()
    for entry in row:
        details = entry.get("asset_details") or {}
        if str(details.get("stock_id") or "").strip() == stock_ticker:
            return {
                "asset_id": entry["asset_id"],
                "quantity": int(details.get("quantity") or 0),
                "avg_price": float(details.get("avg_price") or 0.0),
            }
    return None


def _normalize_stock_ticker(stock_ticker: str) -> str:
    return stock_ticker.strip().upper()
