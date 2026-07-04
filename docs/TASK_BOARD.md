# Task Board

## Status Legend

- `pending`: not started
- `in_progress`: active work
- `blocked`: waiting on a dependency
- `done`: completed and verified

## Current Focus

| ID | Task | Status | Notes | Last Update |
|---|---|---:|---|---|
| TB-001 | MVP backend core loop | in_progress | Core loop is now playable via create character -> advance day -> work/gamble -> buy/sell -> finish day. Needs hardening. Loans are deferred for now. | 2026-07-04 |
| TB-002 | Market simulation foundation | done | Added dataset pipeline, stratified/full calibration, and runtime market generation. | 2026-07-04 |
| TB-003 | Market dataset pipeline | done | Sample, stratified, and full outputs are generated from real Taiwan market data. | 2026-07-04 |
| TB-004 | Runtime market integration | done | Time engine can fall back to simulated bars when a price is missing. | 2026-07-04 |
| TB-005 | Player gameplay APIs | in_progress | Minimal create/read, day advance, work, gamble, buy/sell, and portfolio endpoints were added. Loans remain deferred. | 2026-07-04 |
| TB-006 | PvE blackjack | pending | Not yet connected to the current MVP flow. | 2026-07-04 |
| TB-007 | PvP old maid | pending | WebSocket lobby and card flow still deferred. | 2026-07-04 |
| TB-008 | Test coverage and CI | in_progress | Added smoke coverage for `/trade`, a core gameplay cycle, and portfolio/negative-path regression checks; broader coverage still pending. | 2026-07-04 |

## Recommended Next Steps

1. Harden the player action APIs so the MVP loop is actually playable.
2. Verify the core flow stays limited to create character -> advance one day -> work/gamble -> buy/sell stock -> finish day.
3. Add smoke tests for one full day tick and one buy/sell cycle.
