# Taiwan Stock Monopoly Game

Welcome to the Taiwan Stock Monopoly Game, a unique blend of **RPG character progression, stock market simulation, entrepreneurship, and high-stakes gambling**. Your ultimate goal is to become the "World's Richest Person" in a dynamic virtual Taiwan.

## Game Overview

*   **Core Goal**: Accumulate wealth and status through various paths – legitimate investment, high-risk speculation, or even entrepreneurship and politics.
*   **Time System**: Experience accelerated wealth growth with a **1 real-world hour = 1 in-game day** progression. The game primarily uses historical Taiwan stock market data (2014-2024) for its main mode, allowing for strategic play based on past events.
*   **Dual-Time Mode**:
    *   **Main Mode (24/7 Historical Play)**: Progress your character and wealth at an accelerated pace using past market data.
    *   **Live Mirroring Tournament (活動模式)**: Compete in real-time against other players during actual Taiwan stock market hours (09:00 - 13:30 UTC+8), using your main mode funds to enter and win valuable rewards.

## Key Features

*   **Character Progression**: Start as one of four unique destinies (Academic Elite, Lucky Gambler, Wealthy Heir, Underdog), each with distinct starting assets, stats, and talents. Evolve through multiple career paths including Investor, Gambler, Real Estate Speculator, Influencer, and Politician.
*   **Dynamic Economy**: Engage with a simulated stock market, banking systems (loans, high-interest debt), real estate, and entrepreneurial ventures.
*   **Interactive Gambling**: Test your luck in PvE (Blackjack) and PvP (Old Maid) games, with betting and real-time player interaction.
*   **Meaningful Progression**: Invest in luxury items like real estate, supercars, and elite trading terminals, all of which can serve as collateral or provide game bonuses.
*   **Phased Development**: The game is being developed in phases, starting with an MVP and expanding to include more complex systems like entrepreneurship, social influence, political power, and a succession system for long-term play.

## Technical Stack

*   **Frontend**: Next.js (React) with Tailwind CSS and ECharts for a mobile-first web experience.
*   **Backend**: Python with FastAPI and WebSockets for handling real-time game logic, historical data updates, and PvP synchronization.
*   **Database**: PostgreSQL for storing player data, historical stock information, and game states.

## Current Development Focus (Immediate Action Items)

1.  **Historical Data Ingestion**: Cleaning and storing 10 years of historical trading data for 50 major Taiwan stocks.
2.  **Game Time Engine**: Implementing the backend scheduler for 1-hour = 1-day progression, including interest calculations and attribute updates.
3.  **Character Creation Flow**: Developing the UI and logic for selecting one of the four starting destinies and assigning initial assets.
4.  **PvP WebSocket Prototype**: Testing real-time card-drawing functionality for the Old Maid PvP game.
