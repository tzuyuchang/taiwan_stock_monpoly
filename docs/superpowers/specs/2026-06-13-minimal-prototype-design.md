# Minimal Runnable Prototype Design (2026-06-13)

## Goal
Create the smallest possible local entry point that launches the game core, verifies that the main loop works, and provides a simple UI. The prototype must be startable with a single command (`python run_game.py`) and should not require external services (Discord, OpenRouter, PostgreSQL). It will use the existing design assets (`api_spec.yaml`, `init_schema.sql`, UI component specs) to stay DRY.

## Architecture Overview (Superpower: **Scalability & Modularity**)
```
run_game.py
├─ env loader (fallback defaults)          # Security: safe env handling
├─ sqlite_initializer.py   ← reads init_schema.sql
├─ fastapi_app (src/api/minimal.py)        # Minimal endpoints from api_spec.yaml
├─ static UI (src/ui/index.html)           # Simple market view & start button
└─ game_loop.py                              # Stub that simulates market ticks & a trade
```
All components are independent modules so they can be swapped later (e.g., replace SQLite with PostgreSQL, replace static HTML with React Native).

## Components
1. **run_game.py** – orchestrates startup:
   - Loads `.env` (if present) with defaults for `DB_PATH=./local.db`.
   - Calls `sqlite_initializer.initialize(db_path)`.
   - Starts FastAPI (`uvicorn src.api.minimal:app --port 8000`).
   - Fires `game_loop.start()` in a background thread.
   - Prints a friendly console banner.
   *Superpower applied:* **Error handling** – each step wrapped in try/except with clear logs.

2. **sqlite_initializer.py** – reads `init_schema.sql` and executes statements against a SQLite DB.
   - Uses `sqlite3` with `detect_types=sqlite3.PARSE_DECLTYPES` for proper type handling.
   - Idempotent: runs `IF NOT EXISTS` checks so repeated runs are safe.
   *Superpower applied:* **Performance** – SQLite is fast for local dev, zero network latency.

3. **src/api/minimal.py** – FastAPI router exposing only the endpoints needed for the prototype:
   - `GET /market` → returns static sample market data (or reads from DB if populated).
   - `POST /trade` → accepts a simple payload, writes a row to `transactions` table, returns success.
   - `GET /portfolio` → aggregates holdings for the demo user.
   *Superpower applied:* **Security** – request models validated with Pydantic; all inputs sanitized.

4. **src/ui/index.html** – minimal static page served by FastAPI's `StaticFiles` mount:
   - Shows a heading, a “Start Game” button, and a table placeholder for market data.
   - JavaScript fetches `/market` and populates the table.
   - A “Buy” button on each row triggers a `POST /trade`.
   *Superpower applied:* **Code reusability** – same HTML can later be replaced with React Native without changing the backend.

5. **game_loop.py** – background coroutine that:
   - Every 5 seconds updates a dummy market price in the DB.
   - Optionally logs a simulated trade.
   *Superpower applied:* **Resilience** – runs in its own thread, catches exceptions, and logs without crashing the server.

6. **Smoke test (`tests/smoke_test.py`)** – verifies that after launching `run_game.py` the `/market` endpoint returns HTTP 200 and a JSON list.
   - Uses `subprocess` to start the server, `httpx` for the request, and a timeout.
   - Cleans up the process after the check.
   *Superpower applied:* **Testing** – guarantees the prototype is runnable on any machine.

## Step‑by‑Step Startup Flow
1. `python run_game.py`
2. Env vars loaded → DB file created/initialized.
3. FastAPI starts on port 8000 and serves static UI.
4. Background market ticker begins.
5. User opens `http://localhost:8000/` → sees market table, can click **Buy**.
6. Console prints logs of market updates and trades.

## Success Criteria (Superpower: **Error handling & validation**)
- **Single command** launches without errors.
- UI loads and displays at least three market rows.
- Buying a stock updates the SQLite `transactions` table (verified via log).
- Smoke test passes (`pytest -q tests/smoke_test.py`).
- No external API keys or webhooks are required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Missing `.env` → crash | Provide default values and clear error messages. |
| SQLite file permission issues | Create DB in the project root; fall back to in‑memory if write fails. |
| Port 8000 already in use | Detect `OSError` on server start and suggest an alternate port. |
| UI fetch fails | Serve static files via FastAPI `StaticFiles`; ensure correct path mounting. |

---

*Design ready for review. Once approved, the implementation plan will be generated via the `writing-plans` skill.*