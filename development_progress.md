# Development Progress Report - Taiwan Stock Monopoly Game

## 1. Project Overview & Lore

### 1.1. Story Background: "The Great Investment Era"
*"It is the best of times, it is the worst of times. Inflation devours the sweat of your labor, but capital never sleeps. Will you turn the tide through precise investments, or will you dominate the world through sheer, relentless work? The curtain has risen on the Great Investment Era—the choice is yours."*

This project is a hybrid **RPG simulation, stock market trading, business management, and high-stakes gambling** game. Set in a virtualized Taiwan, players will navigate the "Great Investment Era" with the ultimate, endless goal of becoming the "World's Richest Person."

### 1.2. Core Gameplay Loop & Time Mechanics
To balance realism with mobile game addictiveness, the game avoids a 1:1 real-time clock.
*   **Compressed Time System**: **1 Real-World Hour = 1 In-Game Day** (24 hours in real life equals nearly a month in-game). This pace prevents players from missing major market events while rapidly accelerating the feeling of wealth accumulation.
*   **Dual-Time Modes**:
    *   **Main Mode (24/7 Historical Fast-Forward)**: The primary game loop utilizes real historical data from the Taiwan stock market over the past 10 years (e.g., 2014–2024). Players can use their real-world knowledge of past market trends and news events to strategize.
    *   **Live Mirroring Tournament Mode (Active Trading Hours)**: A special competitive arena open only during actual Taiwan stock market hours (09:00 - 13:30). Players buy entry tickets using their Main Mode funds to compete against the entire server in a 1:1 live market environment for massive rewards.

---

## 2. Character Creation: Starting Destinies

At the beginning of the game, players must choose their "Starting Destiny." Each destiny dictates their initial assets, starting portfolio, base attributes, and unique passive traits, creating immense replayability and diverse early-game strategies.

### 2.1. The Academic Elite (知識就是力量)
*   **Initial Stats**: High Intelligence, High Analysis, Low Luck.
*   **Starting Assets**: $50,000 Cash, No Debt.
*   **Starting Portfolio**: 5 shares of a "Top Tech Blue-Chip" (e.g., TSMC analogue), representing stable, technology-driven growth.
*   **Unique Perks**:
    *   *Fast Learner*: Tuition costs and time required to upgrade Intelligence and Analysis stats are halved.
    *   *Academic Discount*: Receives a 20% discount on renting the "Elite Stock Terminal" (advanced charting tools).

### 2.2. The Chosen Gambler (天選之子)
*   **Initial Stats**: Max Luck, Low Intelligence, Low Work Ethic.
*   **Starting Assets**: $10,000 Cash.
*   **Starting Portfolio**: 100 shares of a "Highly Volatile Meme Stock" (representing high speculation).
*   **Unique Perks**:
    *   *God of Gamblers*: Slightly increased win rates and payouts in scratch cards and casino minigames.
    *   *Windfall*: Drastically increased chance of triggering positive random events or finding unexpected money daily.

### 2.3. The Wealthy Heir (含著金湯匙)
*   **Initial Stats**: High Leadership, Low Work Ethic, Low Analysis.
*   **Starting Assets**: $5,000,000 Cash, owns a "City Apartment" (no rent).
*   **Starting Portfolio**: A diversified portfolio of High-Yield Dividend ETFs.
*   **Unique Perks**:
    *   *Golden Shackles (Debuff)*: Lifestyle Quality is permanently locked to "Medium" or higher, resulting in massive unavoidable daily expenses.
    *   *Elite Network*: Instantly unlocks bank credit loans at the start of the game with a permanent 1% interest rate reduction.

### 2.4. The Underdog (絕地反擊)
*   **Initial Stats**: Max Work Ethic, Low Luck.
*   **Starting Assets**: **$0 Cash, $200,000 Debt** (Starts the game burdened by a credit loan and daily interest).
*   **Starting Portfolio**: None.
*   **Unique Perks**:
    *   *Grit*: Experience points (XP) and stat gains from "Working" are doubled, and stamina consumption is halved.
    *   *Resilience*: Suffers no additional stress debuffs when living expenses drop to the bare minimum, and possesses a higher physical resistance to Underground Loan Shark collection events.

---

## 3. Career Paths & Ecosystem

Players start in their chosen destiny and can pivot or combine various careers. The ecosystem creates a dynamic cycle of wealth transfer.

1.  **Worker / Investor (MVP)**: Earns stable salary, analyzes charts, and buys historical stocks.
2.  **Real Estate Speculator**: Buys land, collects rent from workers, and bribes politicians for favorable zoning laws. Uses property as collateral for stock market leverage.
3.  **Influencer**: Accumulates fans, hypes up "Meme Stocks," and dumps them on retail players.
4.  **Politician**: Manipulates policies, tips off speculators, and protects illegal operations.

---

## 4. MVP System Details (Phase 1 Focus)

To ensure a realistic development timeline, Phase 1 focuses heavily on the core loop: Work/Trade ↔ Gamble ↔ Consume.

### 4.1. Banking & Credit System
*   **Standard Banking**: Players can deposit money for passive interest or take out **Credit Loans** based on their Work Ethic stat and career tier. Defaulting ruins credit scores.
*   **Underground Loan Sharks**: If a player goes bankrupt (often via gambling), Loan Sharks will offer high-interest daily loans. Defaulting triggers physical collection events: stamina reduction, hospital bills, or forced liquidation of stocks.

### 4.2. Interactive Gambling Module
Designed to create a sharp contrast between honest, slow work and the thrilling risk of instant wealth.
*   **PvE - Blackjack**: A fast, text-and-button-based casino game against an NPC dealer for quick dopamine hits.
*   **PvP - Old Maid (Card Game)**: A real-time multiplayer betting lobby using WebSockets. Players take turns blindly drawing cards from each other to avoid the Joker. Includes an emoji system (sweating, laughing, crying) for psychological warfare. Wealth transfers directly between players.
*   **Lottery / Scratch Cards**: Low-cost daily dreams heavily influenced by the Luck stat.

### 4.3. Meaningful Money Sinks (Endgame Goals)
Wealth must translate into tangible power and prestige.
*   **Real Estate & Luxury Progression**:
    *   *Rooftop Studio (Rent)*: Terrible stamina recovery, caps Work Ethic growth.
    *   *City Apartment (Buy)*: Normal stamina recovery, unlocks Night School (boosts Intelligence).
    *   *Luxury Mansion (Buy)*: Grants passive Social/Luck stats, unlocks **Bank VVIP Channel** (massive loan limits, lowest interest rates).
    *   *Supercars / Watches*: Act as high-value collateral for margin trading and provide stat checks for high-end social events.
*   **Elite Stock Terminal License**: A monthly subscription that unlocks technical indicators (MACD, RSI) and provides a 3-day foresight warning for historical corporate news events.
*   **Dynamic Titles & Leaderboards**: Real-time server ranking by net worth. Unlocking achievements displays titles next to the player's name (e.g., [God of Stocks], [Gambling King], [Defaulter]).

---

## 5. Phased Development Roadmap

```text
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: MVP Core (Foundations & Initial Loop)              │
│ - 4 Starting Destinies & Initial Portfolios                 │
│ - Careers: Worker, Investor, Gambler                        │
│ - 1 Hour = 1 Game Day (10-Year Historical Data Engine)      │
│ - PvE Blackjack & PvP Old Maid (WebSockets)                 │
│ - Banking (Loans/Sharks) & Housing/Luxury Sinks             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Capital Expansion (V2.0)                           │
│ - Career: Real Estate Speculator (Zoning events, rent)      │
│ - Entrepreneurship (Founding companies, hiring NPCs)        │
│ - Advanced Banking: Margin Trading (Long/Short), Collateral │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Social & Public Opinion (V3.0)                     │
│ - Career: Influencer (Fan accumulation, Merchandise)        │
│ - Media System: Pay for PR/News to manipulate stock prices  │
│ - Meme Stock IPOs driven entirely by social sentiment       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Power & Endgame (V4.0)                             │
│ - Career: Politician (Lobbying, Insider info, Bribes)       │
│ - Legal System: Imprisonment, Asset Seizures, Account Wipes │
│ - Succession System: Pass down a % of hidden wealth to an   │
│   heir if the main character is jailed.                     │
│ - Live Mirroring Tournament Mode (Real-world sync events)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Technical Architecture & Tech Stack

*   **Architecture**: Client-Server pattern. Monolithic backend for MVP, employing WebSockets for real-time card-drawing synchronization and fast-forward calendar updates.
*   **Frontend**: Next.js (React) + Tailwind CSS + ECharts. Optimized for a clean, fast mobile-web UI. Relies on crisp typography, tabular data, and lightweight animations rather than heavy 3D graphics.
*   **Backend**: Python (FastAPI). Utilizes async capabilities to handle WebSocket state machines (PvP lobbies) and the historical data time-engine.
*   **Database**: PostgreSQL with JSONB support.
    *   `historical_stock_data`: Stores 10 years of daily K-lines and news for 50 major Taiwan tickers.
    *   `player_profile`: Tracks stats, destiny, cash, debt, properties, and stock inventory.
    *   `pvp_lobbies`: Manages real-time state for Old Maid matches.

---

## 7. Immediate Next Steps (Action Items)

1.  **Historical Data ETL**: Build a script to scrape and clean 10 years of daily K-line data and major market news for 50 representative Taiwan stocks, storing them in PostgreSQL.
2.  **Time-Engine Implementation**: Develop the FastAPI background scheduler that automatically advances the virtual calendar by 1 day every 60 real-world minutes, calculating daily interest, stamina recovery, and stock price updates.
3.  **Destiny & Character Creation UI**: Design the frontend onboarding flow allowing players to select one of the 4 Destinies and receive their specific starting perks/portfolios.
4.  **WebSocket Prototype**: Build a barebones prototype of the PvP "Old Maid" backend logic to ensure real-time connection stability and state management.