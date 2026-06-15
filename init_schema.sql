```sql
-- init_schema.sql

-- ==============================
-- 1. players
-- ==============================
CREATE TABLE players (
    player_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username           VARCHAR(50) NOT NULL UNIQUE,
    email              VARCHAR(255) NOT NULL UNIQUE,
    password_hash      TEXT NOT NULL,
    created_at         TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    last_login_at      TIMESTAMP WITH TIME ZONE,
    status             VARCHAR(20) NOT NULL DEFAULT 'active',        -- active, suspended, banned, etc.
    country_code       CHAR(2),                                        -- ISO 3166‑1 alpha‑2
    language_preference VARCHAR(10) DEFAULT 'en'                     -- e.g., en, zh, ja
);

-- ==============================
-- 2. market_data
-- ==============================
CREATE TABLE market_data (
    market_data_id    BIGSERIAL PRIMARY KEY,
    instrument_id    VARCHAR(20) NOT NULL,          -- e.g., stock ticker, crypto symbol
    price            NUMERIC(20,8) NOT NULL,
    volume           BIGINT NOT NULL,
    bid_price        NUMERIC(20,8),
    ask_price        NUMERIC(20,8),
    data_timestamp   TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT uq_market_instrument_timestamp UNIQUE (instrument_id, data_timestamp)
);

-- ==============================
-- 3. portfolios
-- ==============================
CREATE TABLE portfolios (
    portfolio_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    name             VARCHAR(100) NOT NULL,
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    total_value      NUMERIC(20,8) NOT NULL DEFAULT 0,
    CONSTRAINT uq_portfolio_per_player UNIQUE (player_id, name)
);

-- ==============================
-- 4. transactions
-- ==============================
CREATE TABLE transactions (
    transaction_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id     UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    instrument_id    VARCHAR(20) NOT NULL,
    side             VARCHAR(4) NOT NULL CHECK (side IN ('BUY','SELL')),
    quantity         NUMERIC(20,8) NOT NULL CHECK (quantity > 0),
    price            NUMERIC(20,8) NOT NULL CHECK (price > 0),
    executed_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    fee              NUMERIC(20,8) NOT NULL DEFAULT 0,
    -- optional link to market_data for audit
    market_data_id   BIGINT REFERENCES market_data(market_data_id)
);

-- Indexes for fast lookup
CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id);
CREATE INDEX idx_transactions_instrument ON transactions(instrument_id);
CREATE INDEX idx_transactions_executed_at ON transactions(executed_at);

-- ==============================
-- 5. events
-- ==============================
CREATE TABLE events (
    event_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(100) NOT NULL,
    description      TEXT,
    start_time       TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time         TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type       VARCHAR(50) NOT NULL,                     -- e.g., "tournament", "promotion"
    reward_points    INTEGER NOT NULL DEFAULT 0,
    status           VARCHAR(20) NOT NULL DEFAULT 'upcoming'  -- upcoming, active, finished, cancelled
);

-- ==============================
-- 6. achievements
-- ==============================
CREATE TABLE achievements (
    achievement_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(100) NOT NULL,
    description      TEXT,
    criteria_json    JSONB NOT NULL,                         -- flexible definition of criteria
    reward_type      VARCHAR(30) NOT NULL,                    -- e.g., "badge", "currency", "item"
    reward_value     NUMERIC(20,8) DEFAULT 0,
    created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- ==============================
-- 7. player_events (junction: which player participated / earned)
-- ==============================
CREATE TABLE player_events (
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    event_id         UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    joined_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    earned_points    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, event_id)
);

-- ==============================
-- 8. player_achievements (junction: which player earned which achievement)
-- ==============================
CREATE TABLE player_achievements (
    player_id        UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    achievement_id   UUID NOT NULL REFERENCES achievements(achievement_id) ON DELETE CASCADE,
    earned_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    PRIMARY KEY (player_id, achievement_id)
);

-- ==============================
-- 9. portfolio_holdings (snapshot of current holdings per portfolio)
-- ==============================
CREATE TABLE portfolio_holdings (
    portfolio_id     UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    instrument_id    VARCHAR(20) NOT NULL,
    quantity         NUMERIC(20,8) NOT NULL CHECK (quantity >= 0),
    avg_price        NUMERIC(20,8) NOT NULL CHECK (avg_price >= 0),
    last_updated     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    PRIMARY KEY (portfolio_id, instrument_id)
);

-- ==============================
-- 10. audit_log (generic event log)
-- ==============================
CREATE TABLE audit_log (
    log_id           BIGSERIAL PRIMARY KEY,
    actor_type       VARCHAR(20) NOT NULL,               -- e.g., 'player', 'system'
    actor_id         UUID,
    action           VARCHAR(100) NOT NULL,
    details_json     JSONB,
    occurred_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
```

*All tables are designed with referential integrity, appropriate defaults, and indexes for common query paths.*