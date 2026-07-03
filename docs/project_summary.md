# Project Canonical Summary

This document is the consolidated reference for the whole project. It merges the useful content from the separate docs in `docs/` into one source of truth so a future AI agent can understand the project by reading only this file.

## 1. What This Project Is

Taiwan Stock Monopoly Game is a hybrid RPG, stock-market simulation, entrepreneurship, and gambling game set in a virtualized Taiwan economy. The player’s long-term objective is to grow from a starting destiny into the “World’s Richest Person” through work, investing, borrowing, speculation, real estate, and other wealth-building or wealth-destroying choices. The game uses a compressed timeline where 1 real-world hour equals 1 in-game day, so players can progress quickly while still feeling the consequences of long-term financial planning.

The project currently has two layers of documentation:

1. The game product itself, which is the main focus of the current design.
2. An earlier internal automation/backend layer described in `README.md` and `docs/project_intro.md`, where CrewAI agents generate a system design document, PostgreSQL schema, SQL review output, and Discord progress reports.

This consolidated document treats the game product as the primary goal, while preserving the older automation/backend context as part of the repo’s history and tooling story.

## 2. Core Game Vision

The game is designed around a dynamic wealth ecosystem where money, time, and status all matter. Players can earn income through jobs, invest in historical Taiwan stock market data, take loans, gamble, buy property, and eventually unlock more advanced social and political power systems. The experience is intended to be strategic rather than purely idle: good decisions compound, bad decisions can create debt spirals, and the player’s chosen starting destiny strongly affects the opening strategy.

The design documents describe a phased roadmap:

1. Phase 1: MVP core loop with character creation, historical stock trading, banking, gambling, and time progression.
2. Phase 2: Capital expansion with real estate, entrepreneurship, and margin-style finance.
3. Phase 3: Social influence with influencer mechanics, media manipulation, and sentiment-driven markets.
4. Phase 4: Power/endgame with politics, legal consequences, succession, and live tournament modes.

## 3. Main Gameplay Loop

The core loop is built around:

1. Choose a starting destiny.
2. Advance time in the game world.
3. Earn or lose money through work, trading, loans, or gambling.
4. Spend money on survival, status, tools, and progression.
5. Unlock better opportunities, more complex careers, and stronger economic leverage.

The documents consistently emphasize that progression should feel meaningful. Wealth is not just a score: it unlocks better housing, better tools, loan access, and social advantages. At the same time, debt, living costs, and high-risk systems can punish overconfidence.

## 4. Time System And Modes

The project uses an accelerated time model:

1. 1 real-world hour equals 1 in-game day.
2. The main mode runs on historical Taiwan stock market data, roughly spanning 2014 to 2024 in the design docs.
3. A live mirroring tournament mode is planned for real Taiwan market hours, described as 09:00 to 13:30 UTC+8 in the design notes.

The purpose of this split is to support both long-term strategic play and real-time competition:

1. Main mode lets players make decisions using historical events and market behavior.
2. Live mirroring mode lets players compete against others during actual trading hours, using main-mode funds or progression as entry value.

The backend time engine is supposed to handle date advancement, daily interest, stamina recovery, and stock price updates on a scheduled basis.

## 5. Starting Destinies

The character creation design defines four main starting destinies:

1. Academic Elite
2. Chosen Gambler
3. Wealthy Heir
4. Underdog

Each destiny changes the opening assets, base stats, and early-game strategy.

### Academic Elite

High intelligence and analysis, low luck. Starts with moderate cash and a small stable stock position. The design gives this path advantages in learning and access to advanced trading tools.

### Chosen Gambler

High luck, low intelligence, low work ethic. Starts with limited cash and a speculative stock position. This path is tuned for casino-style systems, lottery, scratch cards, and random windfall events.

### Wealthy Heir

High leadership, low work ethic, low analysis. Starts with large cash reserves, no housing cost in the opening design, and a diversified portfolio. This path is powerful but carries expensive lifestyle pressure.

### Underdog

High work ethic, low luck. Starts with no cash and significant debt. This path is intended to reward grinding, stamina efficiency, and recovery from adversity.

## 6. Careers And Economy

The design documents describe a broader career ecosystem:

1. Worker / Investor
2. Real Estate Speculator
3. Influencer
4. Politician

For the MVP, the first meaningful careers are worker, investor, and gambler. Later phases extend into real estate, entrepreneurship, media manipulation, and political influence.

The economy includes:

1. Salary and work income.
2. Stocks and historical market trading.
3. Loans, bank debt, and underground loan sharks.
4. Gambling games with direct wealth transfer.
5. Housing and luxury assets as money sinks and collateral.

The game is designed so money always has pressure attached to it: if players do not deploy capital well, it is slowly eaten by debt, living costs, or risk.

## 7. MVP Systems

The MVP focus described across the docs is the core survival-and-growth loop:

1. Time engine and calendar advancement.
2. Historical stock market ingestion and trading.
3. Player profiles, stamina, cash, debt, and basic progression.
4. Banking and loan processing.
5. PvE Blackjack.
6. PvP Old Maid over WebSockets.
7. Housing, luxury items, and basic money sinks.

These systems are meant to prove the core game loop before expanding into the more ambitious phase-2 to phase-4 content.

## 8. Gambling And Social Play

The game includes gambling as a deliberate gameplay pillar rather than a side activity. The design documents name:

1. PvE Blackjack for quick solo play.
2. PvP Old Maid as a real-time multiplayer betting lobby using WebSockets.
3. Lottery and scratch-card style random events.

The gambling systems are tied to luck, player psychology, and direct wealth movement. PvP modes are also intended to include emoji or emote interactions for social pressure and bluffing.

## 9. Event Cards, Achievements, And Rewards

`docs/game_mechanics.md` adds a modular event-card system. Event cards can be:

1. Boosts
2. Penalties
3. Challenges
4. Gifts

Cards are stored as data objects and can apply temporary or conditional effects when triggered by actions such as trading, logging in, or completing quests.

The same document also describes:

1. Achievement tracking with per-user progress.
2. Reward types such as XP, tokens, items, and badges.
3. Login, trade, and profit streak bonuses.
4. Leaderboard-tied rewards.

These systems support a long-term progression loop beyond raw money.

## 10. Daily And Scheduled Jobs

The design includes regular batch jobs for game-state consistency and content refresh. Examples include:

1. End-of-day settlement.
2. Leaderboard refresh.
3. Risk and compliance export.
4. Backup.
5. Search index rebuild.
6. Cache eviction and warm-up.
7. Daily quest generation.
8. Daily card draw.
9. Streak evaluation.
10. Push summary notifications.

The intention is that the game world feels alive even when the player is not actively interacting with it.

## 11. Technology Stack

The repo’s design documents point to the following stack:

1. Frontend: Next.js, React, Tailwind CSS, ECharts.
2. Backend: Python with FastAPI.
3. Real-time: WebSockets.
4. Database: PostgreSQL with JSONB support.
5. ETL/Data ingestion: Python, `yfinance`, `pandas`, `SQLAlchemy`, and FinMind.
6. Environment/configuration: `.env` files, with Docker planned for containerization.

The frontend is described as mobile-first, lightweight, and optimized for crisp typography and fast UI. The backend is designed as a monolithic MVP backend with real-time hooks, not a full microservices architecture yet.

## 12. Data Sources And ETL

The historical market-data layer is important to the project and is supported by `docs/finmind.md`. That file documents the FinMind API, datasets, and usage patterns used to power Taiwan market ingestion.

The relevant datasets described there include:

1. Trading dates.
2. Daily stock prices.
3. Adjusted prices.
4. Tick data.
5. K-bars.
6. Weekly and monthly prices.
7. Dividend and split data.
8. News data.
9. Market indicators and institutional/chip datasets.

The project docs indicate that the ETL pipeline is intended to gather around 10 to 20 years of historical data, depending on the specific mode and implementation stage. The main goal is to support realistic historical trading, dividends, splits, and event-driven price behavior.

## 13. Backend Automation Context

`README.md` and `docs/project_intro.md` describe an earlier or parallel automation system based on CrewAI. In that description:

1. A principal systems architect agent writes the system design document.
2. A backend/database engineer agent generates PostgreSQL DDL and SQL review output.
3. A Discord reporter agent posts progress updates.
4. A systematic code reviewer checks SQL for anti-patterns.

That context still matters because it explains how some of the repository’s documentation and schema artifacts were generated. However, the game design now appears to be the main target product.

## 14. Current Project Status

From `development_progress.md` and the main README:

1. The project is in Phase 1 MVP work.
2. Backend foundations are the most developed area.
3. The time engine and basic stock-price simulation are already described as implemented or partly implemented.
4. Database connectivity and player/loan management are in place.
5. Historical stock ETL exists or is being refined.
6. Frontend onboarding / character creation is still early.
7. CI/CD, test coverage, and broader polish are still pending.

## 15. Repo Structure Context

The repository root contains:

1. `backend/`
2. `frontend/`
3. `scraper/`
4. `db/`
5. `data/`
6. `tests/`
7. `ci/`
8. `docs/`

This structure reinforces the overall shape of the project: a full-stack game with data ingestion, persistence, and tests, rather than a single-purpose app.

## 16. Important Design Constraints

The docs imply several stable constraints:

1. The game must support historical time travel style play.
2. Player progression must be persistent and stateful.
3. Real-time interactions require WebSockets.
4. Financial systems must feel consequential, especially debt and loans.
5. The content needs to scale from a small MVP into much larger systemic gameplay.
6. The historical data pipeline is a core dependency, not an optional add-on.

## 17. Notes On Documentation Consistency

Some source files are overlapping or partially inconsistent. The most important examples are:

1. The README/project intro text emphasizes a CrewAI-based backend automation workflow.
2. The game design docs emphasize the product vision of the stock-market RPG.
3. The system design doc is broader and more enterprise-like than the game docs.
4. `docs/final_game_design.md` is empty.

For future work, this file should be treated as the canonical merged overview. If the project changes direction, update this file first so future agents do not need to reconcile multiple competing descriptions.

The original source documents have been moved to `docs/archive/` for reference. They are no longer the primary reading path.

## 18. Practical Reading Order For Future Agents

If an AI agent only reads one file, it should read this one. It contains the consolidated meaning of:

1. `README.md`
2. `development_progress.md`
3. `docs/project_intro.md`
4. `docs/system_design_doc.md`
5. `docs/game_mechanics.md`
6. `docs/finmind.md`

If an agent needs a faster skim, it should read `docs/project_summary_one_pager.md` first.

## 19. Short Version

This is a Taiwan stock-market RPG with historical-data-driven trading, a compressed time system, persistent progression, banking and gambling mechanics, and a phased roadmap that starts with a playable MVP and grows into a larger economy, politics, and endgame power simulation.
