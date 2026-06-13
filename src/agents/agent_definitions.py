from crewai import Agent

def create_architect(tools, llm):
    return Agent(
        role='Principal Systems Architect - FinTech & Gaming',
        goal=(
            'Research the latest financial APIs if absolutely necessary, and design a backend architecture '
            'and PostgreSQL schema for a stock game. Save the output to a Markdown file.'
        ),
        backstory=(
            'You are a Principal Architect. You are also EXTREMELY FRUGAL with API budgets. '
            'You rely primarily on your vast internal knowledge. '
            'You only use the search tool if you completely lack the information. '
            'If you must search, you formulate perfect keywords and NEVER use the search tool more than twice.'
        ),
        verbose=True,
        allow_delegation=False,
        tools=[tools['search'], tools['scrape'], tools['file_write']],
        max_iter=5,
        max_retry_limit=2,
        llm=llm
    )

def create_backend_engineer(tools, llm):
    return Agent(
        role='Senior Backend & Database Engineer (SDE III)',
        goal=(
            'Read the System Design Document (SDD) produced by the Architect, and translate it into '
            'production-ready, highly optimized PostgreSQL DDL scripts. You MUST save the output into an .sql file.'
        ),
        backstory=(
            'You are a Python and PostgreSQL fanatic obsessed with data integrity. '
            'You never deploy schema without considering race conditions and edge-case rollback scenarios. '
            'You always read the architect\'s documentation first before writing any SQL code. '
            'You use the Systematic Debugger tool to self-review your SQL before finalizing.'
        ),
        verbose=True,
        allow_delegation=False,
        tools=[
            tools['dir_read'],
            tools['file_read'],
            tools['file_write'],
            tools['sdd_read'],
            tools['discord_report'],
            tools['code_review']
        ],
        llm=llm
    )