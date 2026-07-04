# Decisions

## 2026-07-04 - Use a Layered Market Simulator

Decision:

- Use a layered stochastic market simulator instead of a pure predictive model.

Reason:

- The game needs believable market structure, not just next-day price prediction.
- Sector, liquidity, and regime effects are easier to control with a layered model.

## 2026-07-04 - Keep Raw FinMind Data Separate

Decision:

- Keep `finmind_taiwan_stock_price` as the raw source table.
- Generate feature datasets into `data/` for calibration and simulation work.

Reason:

- Raw data should remain reproducible and queryable.
- Feature generation can evolve without destroying source history.

## 2026-07-04 - Use Sample -> Stratified -> Full Workflow

Decision:

- Stage the data pipeline as sample, stratified, then full calibration.

Reason:

- Sample mode validates the pipeline quickly.
- Stratified mode protects distribution coverage.
- Full mode provides the final calibration baseline.

## 2026-07-04 - Runtime Fallback Generation

Decision:

- Let the time engine generate missing market bars at runtime and write them into `historical_stock_data`.

Reason:

- The game should remain playable even when a historical row is missing.
- This also bridges the simulator into the gameplay loop.

## 2026-07-04 - Use Docs as the Memory Layer

Decision:

- Make `AGENTS.md` plus the docs folder the primary session memory.

Reason:

- Future sessions can resume with minimal token cost.
- The repo state is preserved without rereading the full codebase.

## 2026-07-04 - Defer Loans in MVP Core Loop

Decision:

- Defer borrowing and repayment mechanics from the current MVP phase.

Reason:

- The immediate target is a playable daily loop, and loans are not required for that path.
- Deferring loans keeps the implementation and test surface smaller while the core flow is stabilized.

## 2026-07-04 - Keep Day Progression Manual for MVP

Decision:

- Make day advancement an explicit API action for the MVP loop.
- Keep the time-engine scheduler optional behind `ENABLE_TIME_ENGINE_SCHEDULER`.

Reason:

- The player-facing flow is easier to reason about when the user explicitly advances the day.
- Disabling automatic progression by default avoids the scheduler interfering with manual work, gambling, and trading actions during MVP validation.
