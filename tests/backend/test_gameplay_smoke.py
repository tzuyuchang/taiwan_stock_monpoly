from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import delete

from backend.core.gameplay import (
    PlayerCreateRequest,
    TradeActionRequest,
    WorkActionRequest,
    GambleActionRequest,
    create_player,
    advance_one_day,
    perform_work,
    perform_gamble,
    buy_stock,
    sell_stock,
    list_player_positions,
    get_player_portfolio,
    player_assets_table,
)
from backend.core.time_engine import get_db_session, player_profile_table


def test_core_gameplay_smoke_cycle():
    db = next(get_db_session())
    suffix = uuid4().hex[:8]
    ticker = f"SMOKE{suffix[:4].upper()}"

    try:
        player = create_player(
            db,
            PlayerCreateRequest(
                name=f"Smoke-{suffix}",
                destiny="tester",
                intelligence=10,
                luck=10,
                work_ethic=10,
                leadership=10,
                analysis=10,
                cash=50000,
                stamina=100,
            ),
        )

        day_result = advance_one_day(db)
        assert "next_game_date" in day_result

        work_result = perform_work(db, WorkActionRequest(player_id=player["player_id"], effort=1))
        assert work_result["earned_cash"] > 0

        gamble_result = perform_gamble(db, GambleActionRequest(player_id=player["player_id"], stake=1000))
        assert gamble_result["result"] in {"win", "lose"}

        buy_result = buy_stock(
            db,
            TradeActionRequest(
                player_id=player["player_id"],
                stock_ticker=ticker,
                quantity=1,
            ),
        )
        assert buy_result["quantity"] == 1

        positions_after_buy = list_player_positions(db, player["player_id"])
        assert len(positions_after_buy) == 1

        sell_result = sell_stock(
            db,
            TradeActionRequest(
                player_id=player["player_id"],
                stock_ticker=ticker,
                quantity=1,
            ),
        )
        assert sell_result["remaining_quantity"] == 0

        positions_after_sell = list_player_positions(db, player["player_id"])
        assert positions_after_sell == []
    finally:
        db.execute(delete(player_assets_table).where(player_assets_table.c.player_id == player["player_id"]))
        db.execute(delete(player_profile_table).where(player_profile_table.c.player_id == player["player_id"]))
        db.commit()
        db.close()


def test_buy_fails_when_cash_is_insufficient():
    db = next(get_db_session())
    suffix = uuid4().hex[:8]

    player = None
    try:
        player = create_player(
            db,
            PlayerCreateRequest(
                name=f"LowCash-{suffix}",
                destiny="tester",
                cash=0,
                stamina=100,
            ),
        )

        with pytest.raises(HTTPException) as exc_info:
            buy_stock(
                db,
                TradeActionRequest(
                    player_id=player["player_id"],
                    stock_ticker=f"LOW{suffix[:4].upper()}",
                    quantity=1,
                ),
            )

        assert exc_info.value.status_code == 400
    finally:
        if player is not None:
            db.execute(delete(player_assets_table).where(player_assets_table.c.player_id == player["player_id"]))
            db.execute(delete(player_profile_table).where(player_profile_table.c.player_id == player["player_id"]))
            db.commit()
        db.close()


def test_portfolio_summary_returns_cash_and_totals():
    db = next(get_db_session())
    suffix = uuid4().hex[:8]
    ticker = f"PORT{suffix[:4].upper()}"

    player = None
    try:
        player = create_player(
            db,
            PlayerCreateRequest(
                name=f"Portfolio-{suffix}",
                destiny="tester",
                cash=50000,
                stamina=100,
            ),
        )

        buy_stock(
            db,
            TradeActionRequest(
                player_id=player["player_id"],
                stock_ticker=ticker,
                quantity=1,
            ),
        )

        portfolio = get_player_portfolio(db, player["player_id"])

        assert portfolio["cash"] >= 0
        assert portfolio["totals"]["net_worth"] >= portfolio["cash"]
        assert portfolio["positions"]
        assert portfolio["positions"][0]["stock_id"] == ticker
        assert "current_price" in portfolio["positions"][0]
    finally:
        if player is not None:
            db.execute(delete(player_assets_table).where(player_assets_table.c.player_id == player["player_id"]))
            db.execute(delete(player_profile_table).where(player_profile_table.c.player_id == player["player_id"]))
            db.commit()
        db.close()
