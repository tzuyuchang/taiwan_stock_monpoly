# Taiwan Stock Monopoly Game

Welcome to the Taiwan Stock Monopoly Game, a unique blend of **RPG character progression, stock market simulation, entrepreneurship, and high-stakes gambling**. Your ultimate goal is to become the "World's Richest Person" in a dynamic virtual Taiwan.

## Overall Project Progress / 項目整體進度

This project is progressing through phased development, focusing on establishing core mechanics and expanding features iteratively.

**Current Status:** Phase 1 (MVP Core) is underway, with significant advancements in the backend foundation.

**Completed & In Progress:**
*   **Backend Core:**
    *   Implemented robust Time Engine with correct date advancement and basic stock price simulation.
    *   Established database connectivity and player/loan data management.
    *   Developed the ETL script (`etl_yahoo_finance.py`) to ingest 20 years of historical stock data.
    *   Basic player stamina and loan processing logic is functional.
*   **Frontend:** Initial UI design for Character Creation is being planned.
*   **Database:** Core tables for player profiles, game state, and historical data are assumed to be set up.

**Key Milestones Achieved:**
*   Functional Time Engine with functional `/game-date` API.
*   Operational ETL pipeline for populating historical stock data.
*   Clear development roadmap and technical stack defined.

**中文 - 目前整體進度：**
項目正透過分階段開發推進，初期專注於建立核心機制並逐步擴展功能。

**目前狀態：** 第一階段（MVP 核心）進行中，後端基礎架構已取得顯著進展。

**已完成與進行中：**
*   **後端核心：**
    *   已實作穩健的時間引擎，具備正確的日期推進與基礎股票價格模擬功能。
    *   已建立資料庫連線與玩家/貸款資料管理。
    *   開發了 ETL 腳本 (`etl_yahoo_finance.py`)，用於載入 20 年歷史股票數據。
    *   基礎玩家體力與貸款處理邏輯已可運作。
*   **前端：** 角色創建介面的 UI 設計正在規劃中。
*   **資料庫：** 玩家資料、遊戲狀態和歷史數據的核心表格已假設設定完成。

**已達成的關鍵里程碑：**
*   功能性的時間引擎及運作正常的 `/game-date` API。
*   可操作的歷史數據 ETL 流程。
*   已定義清晰的開發路線圖與技術堆疊。

---

## Project Details / 項目內容

*   **Core Goal**: Accumulate wealth and status through various paths – legitimate investment, high-risk speculation, or even entrepreneurship and politics.
*   **Time System**: Experience accelerated wealth growth with a **1 real-world hour = 1 in-game day** progression. The game primarily uses historical Taiwan stock market data (2014-2024) for its main mode, allowing for strategic play based on past events.
*   **Dual-Time Mode**:
    *   **Main Mode (24/7 Historical Play)**: Progress your character and wealth at an accelerated pace using past market data.
    *   **Live Mirroring Tournament (活動模式)**: Compete in real-time against other players during actual Taiwan stock market hours (09:00 - 13:30 UTC+8), using your main mode funds to enter and win valuable rewards.
*   **Character Progression**: Start as one of four unique destinies (Academic Elite, Lucky Gambler, Wealthy Heir, Underdog), each with distinct starting assets, stats, and talents. Evolve through multiple career paths including Investor, Gambler, Real Estate Speculator, Influencer, and Politician.
*   **Dynamic Economy**: Engage with a simulated stock market, banking systems (loans, high-interest debt), real estate, and entrepreneurial ventures.
*   **Interactive Gambling**: Test your luck in PvE (Blackjack) and PvP (Old Maid) games, with betting and real-time player interaction.
*   **Meaningful Progression**: Invest in luxury items like real estate, supercars, and elite trading terminals, all of which can serve as collateral or provide game bonuses.
*   **Phased Development**: The game is being developed in phases, starting with an MVP and expanding to include more complex systems like entrepreneurship, social influence, political power, and a succession system for long-term play.

**中文 - 項目內容：**
*   **核心目標：** 透過多樣化路徑積累財富與地位——正規投資、高風險投機，甚至創業與從政。
*   **時間系統：** 以 **1 réel-heure = 1 遊戲日** 的速度體驗加速的財富增長。遊戲主要模式採用台灣股市歷史數據（2014-2024），讓玩家能基於過往趨勢進行策略性遊戲。
*   **雙時間模式：**
    *   **主模式（24/7 歷史模擬）：** 使用過去的市場數據，以加速節奏推進您的角色與財富。
    *   **即時市場鏡像競賽（活動模式）：** 在實際台灣股市交易時間（UTC+8 09:00 - 13:30）內，玩家可使用主模式資金報名參賽，與全伺服器玩家即時競技，贏取豐厚獎勵。
*   **角色成長：** 以四種獨特的「開局命運」（知識精英、天選之子、含金湯匙、絕地反擊）之一開始遊戲，每種命運都有不同的初始資產、屬性與天賦。可透過多種職業路徑發展，包括投資者、賭徒、房地產投機者、網紅和政治家。
*   **動態經濟：** 參與模擬股票市場、銀行系統（貸款、高利率債務）、房地產及創業等。
*   **互動式賭博：** 在 PvE（21點）和 PvP（抽鬼牌）遊戲中測試您的運氣，包含下注與即時玩家互動。
*   **有意義的資產擴張：** 投資房地產、超級跑車、高級交易終端等奢侈品，這些資產可作為抵押品或提供遊戲加成。
*   **分階段開發：** 遊戲將分階段開發，從 MVP 開始，逐步擴展至更複雜的系統，如創業、社群影響力、政治權力及繼承系統，以實現長期遊戲目標。

---

## Technology Stack / 技術棧

*   **Frontend**: Next.js (React) with Tailwind CSS and ECharts for a mobile-first web experience. Optimized for clean, fast UI with crisp typography, tabular data, and lightweight animations.
*   **Backend**: Python with FastAPI for building the API and handling asynchronous tasks. WebSockets are used for real-time features like PvP lobbies and time-engine synchronization.
*   **Database**: PostgreSQL with JSONB support for flexible data storage.
*   **Data Ingestion**: Python, `yfinance`, `pandas`, `SQLAlchemy` for ETL processes.
*   **Environment Management**: Docker (planned for containerization), `.env` files for configuration.

**中文 - 技術棧：**
*   **前端：** Next.js (React)，搭配 Tailwind CSS 與 ECharts，實現以行動裝置為優先的手機網頁 UI 體驗，強調清晰排版、表格數據及輕量動畫。
*   **後端：** Python，使用 FastAPI 建立 API 並處理異步任務。WebSocket 用於即時功能，如 PvP 遊戲房間及時間引擎同步。
*   **資料庫：** PostgreSQL，支援 JSONB 功能以提供彈性的資料儲存。
*   **數據導入：** Python，使用 `yfinance`, `pandas`, `SQLAlchemy` 執行 ETL 流程。
*   **環境管理：** Docker（規劃用於容器化），`.env` 檔案用於配置管理。

---

## Architecture / 架構

*   **Pattern**: Client-Server architecture.
*   **Backend**: Monolithic backend for MVP, designed with FastAPI to handle API requests and asynchronous operations. WebSockets integrated for real-time communication.
*   **Database Schema**: Core tables include `player_profile`, `historical_stock_data` (with K-lines, dividends, splits, news), `game_state`, `bank_loans`, and `pvp_lobbies`.
*   **Data Flow**: Player interactions trigger API calls to the backend. The Time Engine runs as a background task, periodically updating game state, player stats, loans, and stock prices based on historical data. Real-time features utilize WebSockets.

**中文 - 架構：**
*   **模式：** 用戶端-伺服器架構。
*   **後端：** MVP 階段採用單體式後端，使用 FastAPI 處理 API 請求與異步操作。整合 WebSocket 以實現即時通訊。
*   **資料庫結構：** 核心表格包含 `player_profile`, `historical_stock_data`（含 K 線、股利、拆股、新聞）、`game_state`, `bank_loans`, 和 `pvp_lobbies`。
*   **數據流：** 玩家互動觸發 API 請求至後端。時間引擎作為背景任務運行，定期根據歷史數據更新遊戲狀態、玩家屬性、貸款及股票價格。即時功能則透過 WebSocket 實現。

---

## CI/CD Plan / 持續整合與部署計畫

*   **Version Control**: Git (GitHub - `taiwan-stock-monopoly-game` repository).
*   **Continuous Integration (CI)**:
    *   **Trigger**: On every push to the `main` or `develop` branches, and on Pull Request creation.
    *   **Steps**:
        1.  Checkout code.
        2.  Set up Python environment (install dependencies from `requirements.txt`).
        3.  Run linters and formatters (e.g., `flake8`, `black`).
        4.  Execute unit tests (using `pytest`).
        5.  Run backend integration tests.
    *   **Tools**: GitHub Actions (planned).
*   **Continuous Deployment (CD)**:
    *   **Trigger**: Successful merge to the `main` branch.
    *   **Steps**:
        1.  Build Docker image (if Docker is implemented).
        2.  Push image to a container registry.
        3.  Deploy to staging environment.
        4.  (Optional) Manual approval for production deployment.
        5.  Deploy to production environment.
    *   **Tools**: GitHub Actions, Docker, cloud provider deployment service (e.g., AWS Elastic Beanstalk, Google Cloud Run).

**中文 - CI/CD 計畫：**
*   **版本控制：** Git (GitHub - `taiwan-stock-monopoly-game` 儲存庫)。
*   **持續整合 (CI)：**
    *   **觸發：** 每次推送到 `main` 或 `develop` 分支，以及創建 Pull Request 時。
    *   **步驟：**
        1.  檢出程式碼。
        2.  設定 Python 環境（安裝 `requirements.txt` 中的依賴）。
        3.  運行 Linter 與格式化工具（例如 `flake8`, `black`）。
        4.  執行單元測試（使用 `pytest`）。
        5.  執行後端整合測試。
    *   **工具：** GitHub Actions（規劃中）。
*   **持續部署 (CD)：**
    *   **觸發：** 成功合併至 `main` 分支後。
    *   **步驟：**
        1.  構建 Docker 映像（若已實作 Docker）。
        2.  將映像推送到容器註冊中心。
        3.  部署至 Staging 環境。
        4.  （可選）生產環境部署前的手動批准。
        5.  部署至生產環境。
    *   **工具：** GitHub Actions, Docker，雲端供應商部署服務（例如 AWS Elastic Beanstalk, Google Cloud Run）。