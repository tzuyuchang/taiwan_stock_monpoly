# --------------------------------------------------------------
#  main.py  –  多角色開發工作流（依 final_game_design.md）
# --------------------------------------------------------------
import os
import requests
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

# --------------------------------------------------------------
# 0️⃣ 讀取環境變數
# --------------------------------------------------------------
load_dotenv()
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_key:
    raise ValueError("找不到 OPENROUTER_API_KEY！請檢查 .env 檔案。")
os.environ["OPENAI_API_KEY"] = openrouter_key

llm = LLM(
    model="openai/gpt-oss-120b:free",
    api_key=openrouter_key,
    base_url="https://openrouter.ai/api/v1",
)

# --------------------------------------------------------------
# 1️⃣ 內建工具：Discord Progress Reporter
# --------------------------------------------------------------
@tool("Discord Progress Reporter")
def discord_report_tool(message: str) -> str:
    """
    Send a progress report to the Discord webhook.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return "Error: DISCORD_WEBHOOK_URL not set."

    data = {
        "content": f"📢 **[AI 團隊回報]**\n{message}",
        "username": "AI 任務小幫手",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712038.png",
    }
    resp = requests.post(webhook_url, json=data)
    return "Successfully reported to Discord." if resp.status_code == 204 else f"Failed ({resp.status_code})"

# --------------------------------------------------------------
# 2️⃣ 其他工具
# --------------------------------------------------------------
search_tool = SerperDevTool()

# --------------------------------------------------------------
# 3️⃣ 代理人（Agents）設定
# --------------------------------------------------------------
# 3.1 Architect
architect = Agent(
    role="Principal Systems Architect - FinTech & Gaming",
    goal="Design overall system architecture, data model & cross‑platform strategy.",
    backstory=(
        "You are an experienced architect. Budget‑aware, you may use at most 2 Google searches."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[search_tool, discord_report_tool],
    max_iter=6,
    llm=llm,
)

# 3.2 Backend Engineer
backend_engineer = Agent(
    role="Senior Backend & Database Engineer (SDE III)",
    goal="Implement PostgreSQL schema, API layer and event‑card logic.",
    backstory=(
        "You love data integrity. Always notify the PM via Discord at start/end of each sub‑task."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[discord_report_tool],
    max_iter=12,
    llm=llm,
)

# 3.3 Frontend Engineer
frontend_engineer = Agent(
    role="Frontend Engineer – React Native / Unity",
    goal="Build UI screens, theme and interaction flow described in the design doc.",
    backstory=(
        "You follow the UI/UX spec precisely and report progress on Discord."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[discord_report_tool],
    max_iter=12,
    llm=llm,
)

# 3.4 Game Designer
game_designer = Agent(
    role="Game Designer – Mechanics & Events",
    goal="Define gameplay loops, event cards, achievement system and daily update flow.",
    backstory=(
        "You translate the final design into concrete mechanics and always keep PM informed."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[discord_report_tool],
    max_iter=8,
    llm=llm,
)

# 3.5 DevOps Engineer
devops_engineer = Agent(
    role="DevOps Engineer – CI/CD & Cloud Sync",
    goal="Set up CI pipeline, Discord webhook verification and cloud sync strategy.",
    backstory=(
        "You ensure every artifact is automatically built, tested and synchronized."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[discord_report_tool],
    max_iter=6,
    llm=llm,
)

# --------------------------------------------------------------
# 4️⃣ 任務（Tasks）定義
# --------------------------------------------------------------
# 4.1 Architect – System Design Document
architect_task = Task(
    description=(
        "1. Report start via Discord: \"開始撰寫系統設計文件。\"\n"
        "2. Draft a comprehensive markdown System Design Document covering:\n"
        "   • High‑level architecture (backend, frontend, sync)\n"
        "   • Database ER diagram (players, market data, portfolios, ledger)\n"
        "   • API spec (REST/GraphQL) for market data, trading, events\n"
        "   • Cross‑platform tech stack (React Native + Unity fallback)\n"
        "   • Daily / real‑time update pipeline\n"
        "   Use at most 2 Google searches.\n"
        "3. Report finish via Discord: \"系統設計文件已完成，已存檔 system_design_doc.md\""
    ),
    expected_output="A clean markdown file `system_design_doc.md`.",
    agent=architect,
    output_file="system_design_doc.md",
)

# 4.2 Backend – Schema
backend_schema_task = Task(
    description=(
        "1. Send Discord start: \"開始根據 SDD 撰寫 PostgreSQL schema。\"\n"
        "2. Read `system_design_doc.md` (the system will provide its content).\n"
        "3. Generate full `CREATE TABLE` statements for:\n"
        "   - players, market_data, portfolios, transactions, events, achievements\n"
        "4. Send Discord finish: \"PostgreSQL schema 完成，已存 `init_schema.sql`。\""
    ),
    expected_output="Pure PostgreSQL DDL saved as `init_schema.sql`.",
    agent=backend_engineer,
    output_file="init_schema.sql",
)

# 4.3 Backend – API Spec
backend_api_task = Task(
    description=(
        "1. Discord start: \"開始撰寫 API 規格 (OpenAPI 3.0)。\"\n"
        "2. Based on `system_design_doc.md` and the schema, produce `api_spec.yaml` covering:\n"
        "   • GET /market, GET /stock/{symbol}\n"
        "   • POST /trade, GET /portfolio, POST /event/trigger\n"
        "3. Discord finish: \"API 規格完成，已存 `api_spec.yaml`。\""
    ),
    expected_output="OpenAPI 3.0 YAML saved as `api_spec.yaml`.",
    agent=backend_engineer,
    output_file="api_spec.yaml",
)

# 4.4 Frontend – UI Components
frontend_ui_task = Task(
    description=(
        "1. Discord start: \"開始實作 UI 版面與主題。\"\n"
        "2. Generate React‑Native component files:\n"
        "   - `HomeScreen.jsx` (ranking, start button)\n"
        "   - `MarketScreen.jsx` (stock list, search, filter)\n"
        "   - `StockDetail.jsx` (K 線圖、買賣按鈕)\n"
        "   - `PortfolioScreen.jsx` (持股、資產圖表)\n"
        "   - `Theme.css` (藍/紅/金配色)\n"
        "3. Discord finish: \"UI 元件已完成，已存於 `src/ui/`。」"
    ),
    expected_output="JSX & CSS files under `src/ui/`.",
    agent=frontend_engineer,
    output_file="ui_components_report.txt",   # 只做報告，實際檔案寫在程式碼中
)

# 4.5 Game Designer – Mechanics
game_mechanics_task = Task(
    description=(
        "1. Discord start: \"開始撰寫遊戲機制與事件卡。\"\n"
        "2. Produce `game_mechanics.md` covering:\n"
        "   • Daily/real‑time update flow\n"
        "   • Event card types與範例\n"
        "   • 成就與獎勵系統\n"
        "3. Discord finish: \"機制文件完成，已存 `game_mechanics.md`。」"
    ),
    expected_output="Markdown file `game_mechanics.md`.",
    agent=game_designer,
    output_file="game_mechanics.md",
)

# 4.6 DevOps – CI / Sync
devops_task = Task(
    description=(
        "1. Discord start: \"開始建立 CI/CD 與雲端同步流程。\"\n"
        "2. Create GitHub Actions workflow `ci.yml` that:\n"
        "   - Lints Python/JS\n"
        "   - Runs unit tests (if any)\n"
        "   - Deploys schema & API to a staging Docker container\n"
        "3. Write `cloud_sync.md` describing how Discord webhook & Google 雲端同步在程式中使用。\n"
        "4. Discord finish: \"CI/CD 與同步說明已完成。」"
    ),
    expected_output="CI workflow `ci.yml` and sync documentation.",
    agent=devops_engineer,
    output_file="ci.yml",
)

# --------------------------------------------------------------
# 5️⃣ Crew 組成與執行
# --------------------------------------------------------------
dev_crew = Crew(
    agents=[architect, backend_engineer, frontend_engineer, game_designer, devops_engineer],
    tasks=[
        architect_task,
        backend_schema_task,
        backend_api_task,
        frontend_ui_task,
        game_mechanics_task,
        devops_task,
    ],
    process=Process.sequential,   # 依序完成，確保依賴關係正確
)

# --------------------------------------------------------------
# 6️⃣ 執行入口
# --------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 [系統啟動] PM 已下達任務，開發團隊開始執行...")
    result = dev_crew.kickoff()
    print("\n=== 🎉 Sprint 完成 ===")
    # result 為最終 Task 的輸出，可自行選擇印出或忽略