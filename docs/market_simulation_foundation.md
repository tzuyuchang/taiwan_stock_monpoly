# Market Simulation Foundation

This document defines the first implementation layer for the game's synthetic Taiwan stock market.

## Goal

Build a market system that feels structurally similar to the real Taiwan market:

- market-wide regime shifts
- sector rotation
- large-cap vs small-cap behavior
- liquidity-aware price impact
- event-driven jumps
- historical-data-driven calibration

The objective is not price prediction. The objective is a believable game-world market generator.

## Recommended Modeling Stack

### 1. Market Regime Layer

Use a hidden-state model to classify each day into one of a few market regimes:

- bull
- bear
- sideways
- panic
- rebound

Recommended baseline:

- Hidden Markov Model for regime detection
- or a simpler threshold-based regime classifier for the first version

### 2. Sector Layer

Each stock should inherit behavior from its sector:

- electronics
- semiconductor
- financials
- transport
- steel
- biotech
- etc.

Recommended baseline:

- factor model
- rolling sector return averages
- sector beta to the market index

### 3. Asset Layer

Each stock should have static or slowly changing attributes:

- market-cap bucket
- liquidity bucket
- volatility bucket
- float size bucket
- sector
- listing category

These attributes control:

- how often the stock jumps
- how hard it can move in one day
- how much slippage it creates
- how much it influences the index

### 4. Event Layer

Model discrete events separately:

- earnings
- dividends
- splits
- macro news
- policy changes
- sector shocks

Recommended baseline:

- Poisson jump process
- event shock table
- sentiment multiplier

### 5. Microstructure Layer

Use liquidity-aware movement and trading friction:

- large-cap stocks move less
- small-cap stocks move more
- low-liquidity stocks have worse slippage
- sector correlation should persist during stress

## Data Inputs

Primary source tables:

- `finmind_taiwan_stock_price`
- `historical_stock_data`
- `game_state`
- `player_profile`

Reference metadata:

- `data/taiwan_stock_overview.csv`

Recommended additional fields to prepare later:

- market cap
- float shares
- sector code
- index weight
- dividend history
- split history
- news sentiment

## Derived Dataset Columns

Minimum feature set:

- `stock_id`
- `game_date`
- `close_price`
- `daily_return`
- `rolling_5_return`
- `rolling_20_return`
- `rolling_5_volatility`
- `rolling_20_volatility`
- `rolling_volume_mean`
- `rolling_notional_volume_mean`
- `sector`
- `stock_type`
- `market_cap_bucket`
- `liquidity_bucket`
- `regime_label`

## Calibration Targets

When you validate the generator, check:

- return distribution fat tails
- volatility clustering
- sector correlation stability
- index concentration
- small-cap vs large-cap dispersion
- event-day jumps
- liquidity impact

## Implementation Order

1. Build a universe loader from the stock overview CSV.
2. Build a feature dataset exporter from price history.
3. Implement regime classification.
4. Implement a stochastic simulator with sector and liquidity modifiers.
5. Connect the simulator to the backend time engine later.

## Staged Workflow

### Stage 1: Development Sample

Use a small raw limit to validate the pipeline quickly.

```powershell
$env:MARKET_BUILD_MODE='sample'
$env:MARKET_FEATURE_LIMIT_ROWS='100000'
python backend/scripts/build_market_dataset.py
```

### Stage 2: Stratified Sample

Use the full universe, but sample rows across sector, cap bucket, liquidity bucket, and year.

```powershell
$env:MARKET_BUILD_MODE='stratified'
$env:MARKET_TARGET_ROWS='100000'
python backend/scripts/build_market_dataset.py
```

### Stage 3: Full Calibration

Use all available rows and export a calibration profile.

```powershell
$env:MARKET_BUILD_MODE='full'
python backend/scripts/build_market_dataset.py
```

### Stage 4: Runtime Integration

The time engine now reads simulated market bars on demand and stores them into `historical_stock_data` when a price is missing.
