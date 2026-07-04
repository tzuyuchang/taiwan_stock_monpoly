# AI Changelog

## 2026-07-04

- Added the market simulation foundation docs and code scaffold.
- Built a market dataset pipeline with sample, stratified, and full modes.
- Generated `market_features.csv`, `market_features_stratified.csv`, and `market_features_full.csv`.
- Generated calibration artifacts for stratified and full runs.
- Connected the market simulator to the time engine as a runtime fallback.
- Added a lightweight `/market-simulation/summary` backend endpoint.
- Created repo memory files to reduce future context loading cost.
- Narrowed the MVP core loop scope to exclude loans and repayment for this phase.
- Added minimal gameplay endpoints for player creation, manual day advance, work, gambling, and stock buy/sell.
- Made the time-engine scheduler optional so the MVP loop can stay manual during validation.
- Fixed gameplay/runtime issues uncovered by smoke tests, including missing schema alignment and fallback stock-bar insertion.
- Added passing smoke tests for `/trade` and the core create -> advance day -> work/gamble -> buy/sell loop.
- Added portfolio summary support and regression checks for insufficient cash and portfolio output.

## Format For Future Entries

- Date
- What changed
- Why it changed
- Any remaining follow-up
