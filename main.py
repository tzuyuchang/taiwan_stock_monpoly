import os
import requests
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crewai_tools import SerperDevTool

# ==========================================
# 0. 環境變數與 LLM 設定
# ==========================================

llm = LLM(
    model="openai/openrouter/free", 
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# ==========================================
# 1. 自訂超能力：Discord 進度回報工具
# ==========================================
@tool("Discord Progress Reporter")
def discord_report_tool(message: str) -> str:
    """
    Use this tool to send progress reports or notifications to the PM in Discord.
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return "Error: Discord Webhook URL is missing."

    data = {
        "content": f"📢 **[AI 團隊回報]**\n{message}",
        "username": "AI 任務小幫手", 
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712038.png" 
    }
    
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        return "Successfully reported to Discord."
    else:
        return f"Failed to report. Status code: {response.status_code}"

# ==========================================
# 2. 實例化其他工具
# ==========================================
search_tool = SerperDevTool()

# ==========================================
# 3. 代理人設定 (Agents) 
# ==========================================

# 角色 1：首席系統架構師 (配備 Google 搜尋，負責出規格)
architect = Agent(
    role='Principal Systems Architect - FinTech & Gaming',
    goal='Design a backend architecture and PostgreSQL schema for a stock game.',
    backstory=(
        'You are a Principal Architect. You are extremely frugal with API budgets. '
        'If you must search, never use the search tool more than twice.'
    ),
    verbose=True,
    allow_delegation=False,
    tools=[search_tool],
    max_iter=5, # 嚴格限制思考次數
    llm=llm
)

# 角色 2：資深後端與資料庫工程師 (配備 Discord，負責寫 Code)
backend_engineer = Agent(
    role='Senior Backend & Database Engineer (SDE III)',
    goal='Translate the Architect\'s SDD into optimized PostgreSQL DDL scripts.',
    backstory=(
        'You are a database fanatic obsessed with data integrity. '
        'You must use the Discord Progress Reporter tool to notify your PM when you start and finish your job.'
    ),
    verbose=True,
    allow_delegation=False,
    tools=[discord_report_tool], # 只給他 Discord 工具，讀寫檔案由系統處理
    llm=llm
)

# ==========================================
# 4. 任務設定 (Tasks) - 融合 Discord 呼叫與系統存檔
# ==========================================

architect_task = Task(
    description=(
        'Draft the System Design Document (SDD) for the database layer of the Stock Game. '
        'Include: 1. Player profiles 2. Market Data 3. Player Portfolios 4. Transaction Ledger. '
        'BUDGET CONSTRAINT: MAXIMUM 2 Google searches.'
    ),
    expected_output='A clean Markdown document containing the SDD.',
    agent=architect,
    output_file='system_design_doc.md' # 系統接管存檔
)

db_engineer_task = Task(
    description=(
        '1. Use the Discord Progress Reporter tool to send: "PM, I am now writing the SQL script based on the SDD."\n'
        '2. Based strictly on the Architect\'s SDD from the previous task, write the complete PostgreSQL `CREATE TABLE` script.\n'
        '3. Use the Discord Progress Reporter tool to send: "PM, the SQL script is complete!"\n'
        'Do not output conversational text in the final answer, ONLY pure SQL code.'
    ),
    expected_output='Pure, valid PostgreSQL code.',
    agent=backend_engineer,
    output_file='init_schema.sql' # 系統接管存檔
)

# ==========================================
# 5. 組成團隊與執行 (Execution)
# ==========================================
dev_team = Crew(
    agents=[architect, backend_engineer],
    tasks=[architect_task, db_engineer_task],
    process=Process.sequential 
)

if __name__ == "__main__":
    print("🚀 [系統啟動] PM 指示已下達。AI 開發團隊開始工作...")
    result = dev_team.kickoff()
    print("\n====================================")
    print("🎯 Sprint 衝刺完成！")