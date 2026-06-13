import asyncpg, os
import pytest

@pytest.mark.asyncio
async def test_schema_tables_exist():
    db_url = os.getenv('TEST_DATABASE_URL')
    assert db_url, "TEST_DATABASE_URL env var not set"
    conn = await asyncpg.connect(db_url)
    rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    tables = {r['tablename'] for r in rows}
    expected = {"users","auth_providers","assets","asset_prices","portfolios","positions","transactions","ledger_entries","games","quests","player_quests","rewards","leaderboards","leaderboard_entries","notifications"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
    await conn.close()
