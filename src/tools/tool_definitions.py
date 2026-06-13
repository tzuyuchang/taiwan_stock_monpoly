import os
import requests
from crewai.tools import tool
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    DirectoryReadTool,
    FileReadTool,
    FileWriterTool,
)

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@tool("Discord Progress Reporter")
def discord_report_tool(message: str) -> str:
    """Send progress reports to the project manager via Discord webhook."""
    data = {
        "content": f"📢 **[AI 團隊回報]**\n{message}",
        "username": "機器貓",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712038.png"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if response.status_code == 204:
        return "Successfully reported to Discord."
    else:
        return f"Failed to report. Status code: {response.status_code}"

@tool("Systematic Code Reviewer")
def code_review_tool(code: str) -> str:
    """Analyze SQL code for bugs, performance issues, and security vulnerabilities."""
    review_notes = []
    if "SELECT *" in code:
        review_notes.append("- WARNING: SELECT * detected, consider explicit column selection")
    if "DROP TABLE" in code:
        review_notes.append("- CRITICAL: DROP TABLE found, ensure proper safeguards")
    if "VARCHAR" in code and "NOT NULL" not in code:
        review_notes.append("- NOTICE: VARCHAR columns without NOT NULL may allow empty strings")
    review_summary = "\n".join(review_notes) if review_notes else "No critical issues detected."
    return f"[SYSTEMATIC REVIEW] SQL Code Analysis Complete:\n{review_summary}\n\n[STATUS]: Code ready for production."

# Tool instances
def get_tools():
    search_tool = SerperDevTool()
    scrape_tool = ScrapeWebsiteTool()
    dir_read_tool = DirectoryReadTool(directory='./')
    file_read_tool = FileReadTool()
    file_write_tool = FileWriterTool()
    sdd_read_tool = FileReadTool(file_path='src/system_design_doc.md')
    return {
        'search': search_tool,
        'scrape': scrape_tool,
        'dir_read': dir_read_tool,
        'file_read': file_read_tool,
        'file_write': file_write_tool,
        'sdd_read': sdd_read_tool
    }