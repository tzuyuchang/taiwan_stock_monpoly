# Project Context

## One-Line Goal

Build a Taiwan stock-market RPG where players progress through work, investing, loans, gambling, and time progression in a persistent game world.

## Product Vision

The game is a hybrid RPG, stock-market simulation, entrepreneurship, and gambling experience set in a virtualized Taiwan economy.

Core pillars:

- historical-data-driven stock trading
- compressed time progression: 1 real hour = 1 in-game day
- persistent player progression
- banking and debt pressure
- gambling and social competition
- future expansion into real estate, influence, and politics

## Current MVP Scope

Phase 1 focuses on the core loop:

- character creation
- manual day progression
- historical stock trading
- basic work/income loop
- PvE and PvP gambling placeholders

## Current Technical Stack

- Frontend: Next.js, React, Tailwind CSS, ECharts
- Backend: Python, FastAPI
- Database: PostgreSQL
- Data/ETL: pandas, SQLAlchemy, FinMind, yfinance
- Real-time: WebSockets planned and partially represented in design docs

## Database Snapshot

Observed current state:

- `finmind_taiwan_stock_price` is the main populated source table
- `game_state` has a single active row
- most gameplay tables are still empty or not yet used

Primary schema files:

- `db/init_schema.sql`
- `backend/core/time_engine.py`
- `scraper/fetch_finmind_data.py`

## Market Simulation Layer

The repo now has a dedicated market simulation foundation:

- `backend/core/market_model/`
- `docs/market_simulation_foundation.md`

Current approach:

- sample, stratified, and full dataset generation
- regime calibration
- sector and liquidity buckets
- runtime fallback generation for missing bars

Current outputs:

- `data/market_features.csv`
- `data/market_features_stratified.csv`
- `data/market_features_full.csv`
- `data/market_calibration_stratified.json`
- `data/market_calibration_full.json`

## Important Architectural Decisions

- Use a layered stochastic market simulator instead of pure price prediction.
- Treat raw FinMind data as source data, not the final gameplay dataset.
- Keep the market runtime deterministic enough for repeatable gameplay.
- Use docs to preserve project memory across short sessions.
- Defer loan and repayment mechanics until after the core daily loop is stable.
- Keep the MVP loop manual until the core actions are stable; scheduler automation is optional.

## What To Ignore For Now

Defer these until the core loop is stable:

- full real estate system
- influencer/media manipulation
- politician/legal system
- advanced social systems
- large frontend polish

## Working Mode

When starting new work, use this context to avoid re-reading the entire repository.
