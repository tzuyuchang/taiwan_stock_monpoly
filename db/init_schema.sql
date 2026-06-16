-- Table for managing the current game date and global state
CREATE TABLE IF NOT EXISTS game_state (
    id SERIAL PRIMARY KEY,
    game_day DATE NOT NULL, -- Renamed from current_date
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial game state if the table is empty
-- Using a more explicit check and insert sequence
INSERT INTO game_state (game_day, created_at)
SELECT CURRENT_DATE, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM game_state WHERE id = 1); -- Check specifically for the first row (id=1)

-- Table to store player profiles and core attributes
CREATE TABLE IF NOT EXISTS player_profile (
    player_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    destiny VARCHAR(50) NOT NULL,
    intelligence INT DEFAULT 0,
    luck INT DEFAULT 0,
    work_ethic INT DEFAULT 0,
    leadership INT DEFAULT 0,
    analysis INT DEFAULT 0,
    cash BIGINT DEFAULT 0,
    stamina INT DEFAULT 100,
    housing VARCHAR(100) DEFAULT 'Rooftop Rental',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store historical stock data (used for simulation)
CREATE TABLE IF NOT EXISTS historical_stock_data (
    id SERIAL PRIMARY KEY,
    stock_ticker VARCHAR(10) NOT NULL,
    game_date DATE NOT NULL,
    open_price DECIMAL(12, 2),
    high_price DECIMAL(12, 2),
    low_price DECIMAL(12, 2),
    close_price DECIMAL(12, 2),
    volume BIGINT,
    event_type VARCHAR(50),
    event_impact DECIMAL(10, 2),
    UNIQUE (stock_ticker, game_date)
);

-- Table to store bank loans (credit and loan shark)
CREATE TABLE IF NOT EXISTS bank_loans (
    loan_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES player_profile(player_id) ON DELETE CASCADE,
    loan_type VARCHAR(50) NOT NULL,
    principal BIGINT NOT NULL,
    interest_rate_daily DECIMAL(5, 4) NOT NULL,
    current_balance BIGINT NOT NULL,
    start_date DATE NOT NULL,
    due_date DATE,
    is_defaulted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to manage PvP game lobbies (e.g., for Old Maid)
CREATE TABLE IF NOT EXISTS pvp_lobbies (
    lobby_id SERIAL PRIMARY KEY,
    game_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'waiting',
    max_players INT DEFAULT 2,
    current_players INT DEFAULT 0,
    bet_amount BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store player assets (stocks, properties, items)
CREATE TABLE IF NOT EXISTS player_assets (
    asset_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES player_profile(player_id) ON DELETE CASCADE,
    asset_type VARCHAR(50) NOT NULL,
    asset_details JSONB,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store player inventory items (consumables, gear, etc.)
CREATE TABLE IF NOT EXISTS player_inventory (
    inventory_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES player_profile(player_id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    quantity INT DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store player stats (base and current values)
CREATE TABLE IF NOT EXISTS player_stats (
    stat_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES player_profile(player_id) ON DELETE CASCADE,
    stat_name VARCHAR(50) NOT NULL,
    base_value INT DEFAULT 0,
    current_value INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (player_id, stat_name)
);

-- Optional: Add indexes for performance on frequently queried columns
-- CREATE INDEX idx_player_profile_cash ON player_profile (cash);
-- CREATE INDEX idx_historical_stock_data_date_ticker ON historical_stock_data (game_date, stock_ticker);
-- CREATE INDEX idx_bank_loans_player_id ON bank_loans (player_id, is_defaulted);
-- CREATE INDEX idx_player_assets_player_id ON player_assets (player_id);
-- CREATE INDEX idx_player_stats_player_id ON player_stats (player_id, stat_name);