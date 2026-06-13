# Backend Schema & API Implementation Plan

> **For agentic workers:** REQUIRED SUB‑SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task‑by‑task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production‑ready PostgreSQL schema and a FastAPI backend that serves the OpenAPI spec, with full test coverage and Discord‑based sprint notifications.

**Architecture:** The backend will run as a Docker container, connect to the `db/init_schema.sql` PostgreSQL instance, expose REST endpoints defined in `api_spec.yaml`, and report progress via the existing Discord webhook. Tests run in CI using a temporary PostgreSQL container.

**Tech Stack:** Python 3.11, FastAPI, asyncpg, Pydantic, pytest‑asyncio, Docker, GitHub Actions, Discord webhook.

---

### Task 1: Verify DB schema

**Files:**
- Modify: `db/init_schema.sql` (no change, just verification)
- Create: `tests/db/test_schema.py`

- [ ] **Step 1: Write a failing test**
```python
import asyncpg, asyncio
import os

async def test_schema_tables_exist():
    conn = await asyncpg.connect(os.getenv("TEST_DATABASE_URL"))
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    table_names = {r['tablename'] for r in tables}
    expected = {"users","auth_providers","assets","asset_prices","portfolios","positions","transactions","ledger_entries","games","quests","player_quests","rewards","leaderboards","leaderboard_entries","notifications"}
    assert expected.issubset(table_names)
    await conn.close()
```
- [ ] **Step 2: Run the test (should fail because DB not created yet)**
```bash
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/testdb
pytest tests/db/test_schema.py::test_schema_tables_exist -vv
```
- Expected: connection error or missing tables → FAIL.
- [ ] **Step 3: Run migration script**
```bash
psql $TEST_DATABASE_URL -f db/init_schema.sql
```
- [ ] **Step 4: Re‑run the test (should now PASS)**
```bash
pytest tests/db/test_schema.py::test_schema_tables_exist -vv
```
- Expected: PASS.
- [ ] **Step 5: Commit**
```bash
git add db/init_schema.sql tests/db/test_schema.py
git commit -m "test: verify PostgreSQL schema creation"
```

### Task 2: Add migration helper utility

**Files:**
- Create: `utils/migrate.py`

- [ ] **Step 1: Write the helper**
```python
import subprocess, os

def run_migration():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    result = subprocess.run(["psql", db_url, "-f", "db/init_schema.sql"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Migration failed: {result.stderr}")
    print("✅ Migration succeeded")
```
- [ ] **Step 2: Add a simple unit test**
```python
import os, subprocess

def test_run_migration(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/testdb")
    # Use a temporary empty DB – call the function and expect no exception
    from utils.migrate import run_migration
    run_migration()
```
- [ ] **Step 3: Run the test** (will invoke `psql` – ensure the test DB exists).
- [ ] **Step 4: Commit**
```bash
git add utils/migrate.py tests/db/test_migration.py
git commit -m "feat: migration helper with test"
```

### Task 3: Generate / verify OpenAPI spec

**Files:**
- Verify existing `api_spec.yaml` (no changes needed now).
- Create: `tests/api/test_openapi.py`

- [ ] **Step 1: Write contract validation test**
```python
import yaml, jsonschema, pathlib

def test_openapi_contract():
    spec_path = pathlib.Path('api_spec.yaml')
    spec = yaml.safe_load(spec_path.read_text())
    # Minimal validation – ensure required top‑level keys exist
    required = {"openapi", "info", "paths"}
    assert required.issubset(set(spec.keys()))
```
- [ ] **Step 2: Run the test** (should PASS).
- [ ] **Step 3: Commit**
```bash
git add tests/api/test_openapi.py
git commit -m "test: basic OpenAPI contract validation"
```

### Task 4: Implement FastAPI server

**Files:**
- Create: `backend/app.py`
- Create: `backend/models.py`
- Create: `backend/routes.py`
- Create: `backend/__init__.py`
- Modify: `docker-compose.yml` (add `backend` service)

- [ ] **Step 1: Write a failing test for the `/market` endpoint**
```python
import httpx, asyncio, os

async def test_market_endpoint():
    async with httpx.AsyncClient(base_url=os.getenv('API_URL', 'http://localhost:8000')) as client:
        r = await client.get('/market')
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
```
- [ ] **Step 2: Run the test (should FAIL – server not up).**
- [ ] **Step 3: Scaffold FastAPI app**
```python
# backend/app.py
import uvicorn
from fastapi import FastAPI
from .routes import router as api_router

app = FastAPI(title="Taiwan Stock Monopoly API")
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)
```
- [ ] **Step 4: Add a simple router**
```python
# backend/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get('/market')
async def market():
    # Placeholder – return static list for now
    return [{"symbol": "2330.TW", "price": 600.0}]
```
- [ ] **Step 5: Run the server locally (`uvicorn backend.app:app --reload`) and re‑run the test – should now PASS.**
- [ ] **Step 6: Commit server code**
```bash
git add backend/
git commit -m "feat: FastAPI skeleton with /market endpoint"
```

### Task 5: Add full CRUD endpoints (assets, trade, portfolio)
*(You can extend this task later; for Sprint 2 we only need the core `/market` and `/trade` endpoints. The rest can be added in subsequent sprints.)*

- [ ] **Step 1: Extend `backend/routes.py` with `/trade` POST**
```python
from pydantic import BaseModel

class TradeRequest(BaseModel):
    user_id: str
    asset_id: str
    side: str  # "buy" or "sell"
    quantity: float

@router.post('/trade')
async def trade(req: TradeRequest):
    # In a real implementation this would call the DB layer.
    return {"status": "submitted", "detail": req.dict()}
```
- [ ] **Step 2: Write failing test for `/trade`**
```python
async def test_trade_endpoint():
    async with httpx.AsyncClient(base_url=os.getenv('API_URL', 'http://localhost:8000')) as client:
        payload = {"user_id": "123", "asset_id": "asset-xyz", "side": "buy", "quantity": 10}
        r = await client.post('/trade', json=payload)
        assert r.status_code == 200
        assert r.json()['status'] == 'submitted'
```
- [ ] **Step 3: Run test (FAIL), then re‑run server, then PASS.**
- [ ] **Step 4: Commit**
```bash
git add backend/routes.py tests/backend/test_trade.py
git commit -m "feat: add /trade endpoint with basic validation"
```

### Task 6: Extend CI pipeline for backend

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Add a Docker‑Compose step to start PostgreSQL and the backend**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: testdb
    ports: [5432:5432]
    options: --health-cmd "pg_isready -U postgres" --health-interval 10s --health-timeout 5s --health-retries 5
```
- [ ] **Step 2: Add a step to run migrations before tests**
```yaml
- name: Run DB migrations
  run: |
    python -c "import utils.migrate; utils.migrate.run_migration()"
  env:
    DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
```
- [ ] **Step 3: Add pytest command for backend tests**
```yaml
- name: Run backend tests
  run: |
    pytest tests/backend -vv
```
- [ ] **Step 4: Commit CI changes**
```bash
git add .github/workflows/ci.yml
git commit -m "ci: add backend test steps and PostgreSQL service"
```

### Task 7: Discord notifications for backend milestones

**Files:**
- Create: `backend/utils/discord_notify.py`

- [ ] **Step 1: Write a thin wrapper around `discord_report_tool`**
```python
from main import discord_report_tool

def announce(message: str):
    result = discord_report_tool(message)
    if "Failed" in result:
        raise RuntimeError(f"Discord notification failed: {result}")
    return result
```
- [ ] **Step 2: Call `announce` at start/end of backend server**
```python
# backend/app.py (add near bottom)
from .utils.discord_notify import announce

announce("🚀 Backend server starting…")
```
- At graceful shutdown (FastAPI shutdown event) announce completion.
- [ ] **Step 3: Write a test that monkey‑patches `discord_report_tool` and ensures `announce` returns success.**
- [ ] **Step 4: Commit**
```bash
git add backend/utils/discord_notify.py backend/app.py tests/backend/test_discord_notify.py
git commit -m "feat: Discord notifications for backend lifecycle"
```

### Task 8: End‑to‑End verification

- [ ] **Start Docker Compose (`docker compose up -d`)** – services: `postgres`, `backend`.
- [ ] **Run the full test suite** (`pytest -vv`). All should pass.
- [ ] **Check Discord channel** – you should see:
  1. “Backend server starting…”
  2. Final sprint‑review embed listing all backend tasks with ✅.
- [ ] **Commit final verification note**
```bash
git add docs/sprint_review_examples.md
git commit -m "docs: add backend end‑to‑end verification screenshots"
```

---

### How to Run This Plan
1. **Create a new branch** for the sprint (e.g., `backend-schema-api`).
2. **Execute each `[ ]` step in order**, committing after every step.
3. **Push** the branch to GitHub and open a PR targeting `develop`.
4. **CI will run** the new backend jobs and the Discord webhook will post the sprint‑review embed automatically.

---

**When the plan file is saved to `plans/2026-06-13-backend-schema-api.md`, the next execution will pick it up automatically and the sub‑agent workflow will handle each task in isolation.**