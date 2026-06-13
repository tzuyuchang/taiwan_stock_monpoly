-- init_schema.sql
-- PostgreSQL schema for FinTech Gaming Platform
-- Generated based on system_design_doc.md

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- =============================================================
-- Users & Authentication
-- =============================================================

CREATE TABLE users (
    user_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email          VARCHAR(255) NOT NULL UNIQUE,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    status         VARCHAR(20)  NOT NULL DEFAULT 'active', -- active, suspended, closed
    kyc_status     VARCHAR(20)  NOT NULL DEFAULT 'pending', -- pending, verified, rejected
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auth_providers (
    provider_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    provider      VARCHAR(30) NOT NULL,               -- google, apple, facebook, etc.
    external_id   VARCHAR(255) NOT NULL,
    token_hash    VARCHAR(255),                       -- hashed refresh token / access token
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider, external_id)
);

-- =============================================================
-- Assets & Market Data
-- =============================================================

CREATE TABLE assets (
    asset_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol        VARCHAR(20) NOT NULL UNIQUE,
    type          VARCHAR(20) NOT NULL,               -- stock, crypto, in-game
    name          VARCHAR(100) NOT NULL,
    sector        VARCHAR(50),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Timescale hypertable for price candles
CREATE TABLE asset_prices (
    asset_id      UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    ts            TIMESTAMPTZ NOT NULL,
    open          NUMERIC(20,8) NOT NULL,
    high          NUMERIC(20,8) NOT NULL,
    low           NUMERIC(20,8) NOT NULL,
    close         NUMERIC(20,8) NOT NULL,
    volume        NUMERIC(20,2) NOT NULL,
    PRIMARY KEY (asset_id, ts)
);
SELECT create_hypertable('asset_prices', 'ts', chunk_time_interval => interval '1 hour');

-- =============================================================
-- Portfolios, Positions, Transactions, Ledger
-- =============================================================

CREATE TABLE portfolios (
    portfolio_id  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    base_currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    cash_balance  NUMERIC(20,8) NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE positions (
    position_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id  UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id      UUID NOT NULL REFERENCES assets(asset_id),
    quantity      NUMERIC(20,8) NOT NULL,
    avg_price     NUMERIC(20,8) NOT NULL,
    last_price    NUMERIC(20,8),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (portfolio_id, asset_id)
);

CREATE TYPE trade_side AS ENUM ('buy', 'sell');
CREATE TYPE order_type AS ENUM ('market', 'limit');

CREATE TABLE transactions (
    txn_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id  UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id      UUID NOT NULL REFERENCES assets(asset_id),
    side          trade_side NOT NULL,
    quantity      NUMERIC(20,8) NOT NULL,
    price         NUMERIC(20,8) NOT NULL,
    fee           NUMERIC(20,8) NOT NULL DEFAULT 0,
    total_amount  NUMERIC(20,8) NOT NULL,                 -- price * quantity + fee (positive for buy, negative for sell)
    order_type    order_type NOT NULL,
    ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
    status        VARCHAR(20) NOT NULL DEFAULT 'filled'   -- pending, filled, cancelled
);

CREATE TYPE ledger_entry_type AS ENUM ('trade', 'reward', 'fee', 'adjustment');

CREATE TABLE ledger_entries (
    entry_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    txn_id        UUID REFERENCES transactions(txn_id) ON DELETE SET NULL,
    account       VARCHAR(50) NOT NULL,                     -- e.g., 'cash', 'margin', 'reward_pool'
    amount        NUMERIC(20,8) NOT NULL,                  -- positive = credit, negative = debit
    entry_type    ledger_entry_type NOT NULL,
    ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
    description   TEXT
);

-- =============================================================
-- Game Layer: Games, Quests, Player Quests, Rewards
-- =============================================================

CREATE TABLE games (
    game_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name          VARCHAR(100) NOT NULL,
    version       VARCHAR(20) NOT NULL,
    platform      VARCHAR(20) NOT NULL,                    -- mobile, desktop, web
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE quests (
    quest_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id       UUID NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    description   TEXT NOT NULL,
    reward_type   VARCHAR(30) NOT NULL,                    -- xp, token, item
    reward_amount NUMERIC(20,8) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE quest_status AS ENUM ('available', 'in_progress', 'completed', 'claimed');

CREATE TABLE player_quests (
    player_quest_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    quest_id       UUID NOT NULL REFERENCES quests(quest_id) ON DELETE CASCADE,
    status         quest_status NOT NULL DEFAULT 'available',
    progress       NUMERIC(10,2) DEFAULT 0,                -- percentage or custom metric
    completed_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, quest_id)
);

CREATE TABLE rewards (
    reward_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type          VARCHAR(30) NOT NULL,                    -- xp, token, item
    amount        NUMERIC(20,8) NOT NULL,
    granted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    source        VARCHAR(50)                             -- e.g., 'quest', 'daily_login'
);

-- =============================================================
-- Leaderboards
-- =============================================================

CREATE TABLE leaderboards (
    leaderboard_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scope          VARCHAR(20) NOT NULL,                    -- global, weekly, monthly
    metric         VARCHAR(30) NOT NULL,                    -- e.g., 'total_profit', 'xp'
    generated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE leaderboard_entries (
    entry_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    leaderboard_id UUID NOT NULL REFERENCES leaderboards(leaderboard_id) ON DELETE CASCADE,
    user_id        UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    rank           INTEGER NOT NULL,
    value          NUMERIC(20,8) NOT NULL,
    recorded_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (leaderboard_id, user_id)
);

-- =============================================================
-- Notifications (Outbox pattern)
-- =============================================================

CREATE TYPE notif_channel AS ENUM ('email', 'push', 'in_app');

CREATE TYPE notif_status AS ENUM ('pending', 'sent', 'failed');

CREATE TABLE notifications (
    notif_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    channel       notif_channel NOT NULL,
    payload       JSONB NOT NULL,
    status        notif_status NOT NULL DEFAULT 'pending',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    sent_at       TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================
-- Indexes for performance
-- =============================================================

-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Auth providers
CREATE INDEX idx_auth_user ON auth_providers(user_id);
CREATE INDEX idx_auth_provider_external ON auth_providers(provider, external_id);

-- Assets
CREATE INDEX idx_assets_symbol ON assets(symbol);
CREATE INDEX idx_assets_type ON assets(type);

-- Asset prices (Timescale)
CREATE INDEX idx_asset_prices_ts ON asset_prices(ts DESC);
CREATE INDEX idx_asset_prices_asset_ts ON asset_prices(asset_id, ts DESC);

-- Portfolios
CREATE INDEX idx_portfolios_user ON portfolios(user_id);

-- Positions
CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX idx_positions_asset ON positions(asset_id);

-- Transactions
CREATE INDEX idx_txn_portfolio_ts ON transactions(portfolio_id, ts DESC);
CREATE INDEX idx_txn_asset_ts ON transactions(asset_id, ts DESC);
CREATE INDEX idx_txn_status ON transactions(status);

-- Ledger entries
CREATE INDEX idx_ledger_txn ON ledger_entries(txn_id);
CREATE INDEX idx_ledger_account ON ledger_entries(account);

-- Quests
CREATE INDEX idx_quests_game ON quests(game_id);

-- Player quests
CREATE INDEX idx_player_quests_user ON player_quests(user_id);
CREATE INDEX idx_player_quests_status ON player_quests(status);

-- Rewards
CREATE INDEX idx_rewards_user ON rewards(user_id);
CREATE INDEX idx_rewards_type ON rewards(type);

-- Leaderboard entries
CREATE INDEX idx_lb_entries_lb_user ON leaderboard_entries(leaderboard_id, rank);
CREATE INDEX idx_lb_entries_user ON leaderboard_entries(user_id);

-- Notifications
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX idx_notifications_created ON notifications(created_at);

-- =============================================================
-- Triggers for timestamps
-- =============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_portfolios_updated
BEFORE UPDATE ON portfolios
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_positions_updated
BEFORE UPDATE ON positions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================
-- End of init_schema.sql
-- =============================================================

-- Discord finish report will be sent separately.