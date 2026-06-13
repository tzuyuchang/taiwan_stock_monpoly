# Taiwan Stock Simulation Game Backend

Multi‑agent system powered by CrewAI that automatically generates a PostgreSQL schema for a stock‑trading simulation game.

## 🔠 語言切換
本專案同時提供 **英文** / **繁體中文** 兩種閱讀模式。GitHub 頁面左上角可直接切換。

---

## 🇬🇧 English

### Features
- **Principal Systems Architect** agent researches (max 2 Google searches) & writes a System Design Document (SDD) in Markdown.
- **Senior Backend & Database Engineer** agent generates production‑ready PostgreSQL DDL, performs self‑review with a systematic review tool, and reports progress to Discord.
- Built‑in **Discord Progress Reporter** tool pushes status updates to the PM channel.
- Built‑in **Systematic Code Reviewer** tool checks SQL for anti‑patterns (SELECT *, missing NOT NULL, unsafe DROP TABLE, etc.).
- Clean separation of concerns: agents, tasks, and tools reside in `src/`.
- Core outputs (`system_design_doc.md`, `init_schema.sql`) are stored under `src/`.

### Installation
1. Clone the repo (or copy the folder).
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set env vars:
   ```bash
   set OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   set SERPER_API_KEY=your-serper-dev-key
   set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/xxxxxx
   ```
   (PowerShell: `$env:VAR="value"`; Linux/macOS: `export VAR=value`)

### Usage
```bash
python main.py
```
After run you'll find:
- `src/system_design_doc.md` – generated SDD.
- `src/init_schema.sql` – reviewed PostgreSQL DDL.
Status updates are sent to Discord.

### Development
- **Testing**: `pytest` (add tests under `tests/`).
- **Lint / typecheck**: `flake8 src`、`mypy src`.
- **Extending**: Add agents in `src/agents/`, tasks in `src/tasks/`, tools in `src/tools/`.

### License
MIT – see `LICENSE`.

### Credits
- [CrewAI](https://crewai.com)
- [crewai‑tools](https://github.com/joaomdmoura/crewAI-tools)
- OpenRouter

---

## 🇨🇳 繁體中文

### 功能特色
- 主系統架構師代理研究（最多 2 次 Google 搜尋）並以 Markdown 撰寫系統設計說明書（SDD）。
- 後端與資料庫工程師代理根據 SDD 產生 PostgreSQL 物件定義，並使用系統化審查工具自檢程式碼，最後透過 Discord 進度報告。
- 內建 **Discord 進度報告** 工具即時推播狀態至 PM 頻道。
- 內建 **系統化程式碼審查** 工具針對 SQL 常見反模式（SELECT *、忘記 NOT NULL、危險 DROP TABLE 等）進行檢查。
- 清晰分層：代理、任務與工具皆放於 `src/` 內。
- 主產出 (`system_design_doc.md`, `init_schema.sql`) 存放在 `src/`。

### 安裝
1. 下載或複製本專案。
2. （可選）建立虛擬環境：
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```
3. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```
4. 設定環境變數：
   ```bash
   set OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   set SERPER_API_KEY=your-serper-dev-key
   set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/xxxxxx
   ```
   （PowerShell：`$env:VAR="value"`；Linux/macOS：`export VAR=value`）

### 使用方式
```bash
python main.py
```
執行後會在 `src/` 下產生：
- `system_design_doc.md` – 系統設計說明書。
- `init_schema.sql` – 已審查過的 PostgreSQL DDL。

### 開發維護
- **測試**：使用 `pytest` (新增 `tests/` 套件)。
- **靜態分析**：`flake8 src`、`mypy src`。
- **擴充**：在 `src/agents/` 加入新代理，在 `src/tasks/` 新增任務，或在 `src/tools/` 加入工具。

### 授權
MIT – 請參閱 `LICENSE`。

### 感謝
- [CrewAI](https://crewai.com)
- [crewai‑tools](https://github.com/joaomdmoura/crewAI-tools)
- OpenRouter
