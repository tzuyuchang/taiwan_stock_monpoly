# Codex Working Rules

This repo uses a lightweight memory layer so future Codex sessions can resume work without rereading the entire codebase.

## Read First

In a new session, read these files in order:

1. `AGENTS.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/TASK_BOARD.md`
4. `docs/CHANGELOG_AI.md`
5. `docs/DECISIONS.md`

If the task is about one specific subsystem, only then read the related source files.

## Operating Rules

- Prefer updating the memory files before or after code changes.
- Keep updates short and factual.
- Do not duplicate large code blocks in the docs.
- Use the docs as the source of truth for project state, task status, and major decisions.
- Avoid rereading the whole repo unless the docs are insufficient or clearly stale.

## Update Rules

- After finishing a task, append a concise entry to `docs/CHANGELOG_AI.md`.
- If task status changes, update `docs/TASK_BOARD.md`.
- If a technical direction is chosen or changed, add an entry to `docs/DECISIONS.md`.
- If the project scope or architecture changes, update `docs/PROJECT_CONTEXT.md`.

## Project Identity

- Project: Taiwan Stock Monopoly Game
- Phase: MVP foundation and market simulation calibration
- Backend stack: FastAPI + PostgreSQL
- Core product goal: a believable Taiwan stock-market RPG with persistent progression

## Token Discipline

- Prefer the memory files over full codebase scans.
- Prefer summaries over full file dumps.
- Prefer targeted reads and small edits.

