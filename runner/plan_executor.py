import os, subprocess, shlex, time, json, pathlib, re
from typing import List, Tuple

# --------------------------------------------------------------
# Helper: Discord reporter (reuse the function defined in main.py)
# --------------------------------------------------------------
try:
    from main import discord_report_tool  # type: ignore
    # If imported object is a Tool, extract the underlying function
    if hasattr(discord_report_tool, "func"):
        discord_report_tool = discord_report_tool.func
except Exception:
    # Fallback – simple HTTP POST if import fails (for safety)
    import requests
    def discord_report_tool(message: str) -> str:
        webhook = os.getenv("DISCORD_WEBHOOK_URL")
        if not webhook:
            return "Error: DISCORD_WEBHOOK_URL not set"
        payload = {"content": message}
        resp = requests.post(webhook, json=payload)
        return "✅" if resp.status_code == 204 else f"❌ {resp.status_code}" 

# --------------------------------------------------------------
# Load the markdown plan and extract each "- [ ]" task line
# --------------------------------------------------------------
TASK_RE = re.compile(r"^- \[ \] (.+)$", re.MULTILINE)

def load_plan(plan_path: pathlib.Path) -> List[str]:
    """Parse the markdown plan and return a list of executable shell commands.

    The plan uses checklist items (`- [ ] …`) followed by a fenced code block
    containing the actual command (often marked with ```bash). This function
    extracts the code block that belongs to each checklist item.
    """
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    steps: List[str] = []
    i = 0
    while i < len(lines):
        task_match = TASK_RE.match(lines[i])
        if task_match:
            # Look ahead for the first fenced code block after this checklist line
            cmd_lines: List[str] = []
            j = i + 1
            while j < len(lines):
                line = lines[j].strip()
                # Stop if we encounter the next checklist item
                if TASK_RE.match(line):
                    break
                # Detect start of a fence (``` or ```bash etc.)
                if line.startswith("```"):
                    # Capture everything until the closing fence
                    j += 1
                    while j < len(lines) and not lines[j].strip().startswith("```"):
                        cmd_lines.append(lines[j])
                        j += 1
                    break  # stop after closing fence
                j += 1
            command = "\n".join(cmd_lines).strip()
            if command:
                steps.append(command)
            i = j
        else:
            i += 1
    return steps

# --------------------------------------------------------------
# Run a shell command with retries and Discord reporting on failure
# --------------------------------------------------------------
def run_cmd(cmd: str, cwd: pathlib.Path = pathlib.Path.cwd(), retries: int = 3) -> Tuple[int, str]:
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            result = subprocess.run(
                shlex.split(cmd),
                cwd=str(cwd),
                capture_output=True,
                text=True,
                env=os.environ,
            )
            out = result.stdout + result.stderr
            if result.returncode == 0:
                return 0, out
            else:
                discord_report_tool(
                    f"⚠️ Command failed (attempt {attempt}/{retries}): `{cmd}`\n```{out}```"
                )
                time.sleep(2 ** attempt)
        except Exception as exc:
            discord_report_tool(
                f"❌ Exception while running `{cmd}` (attempt {attempt}/{retries})\n{exc}"
            )
            time.sleep(2 ** attempt)
    return 1, f"Command failed after {retries} attempts: {cmd}"

# --------------------------------------------------------------
# Main executor – iterates over every step, reports to Discord, commits, pushes
# --------------------------------------------------------------
def execute_plan(plan_path: pathlib.Path) -> None:
    steps = load_plan(plan_path)
    total = len(steps)
    discord_report_tool(f"🚀 Starting plan **{plan_path.name}** – {total} steps.")

    for idx, raw in enumerate(steps, start=1):
        # Collapse multi‑line commands into one line (using &&)
        cmd = raw.replace("\n", " && ").strip()
        discord_report_tool(f"▶️ **Step {idx}/{total}** → `{cmd}`")
        # Skip non-executable descriptive steps (e.g., markdown headings)
        if cmd.strip().startswith('**') or not re.search(r'\w+', cmd):
            discord_report_tool(f"ℹ️ Skipping non‑command step {idx}/{total}: `{cmd}`")
            continue
        rc, out = run_cmd(cmd)
        if rc == 0:
            discord_report_tool(f"✅ **Step {idx}/{total}** succeeded.\n```{out}```")
        else:
            discord_report_tool(f"❌ **Step {idx}/{total}** failed – aborting.\n```{out}```")
            raise RuntimeError(f"Plan aborted at step {idx}")

    # ----------------------------------------------------------
    # Final Sprint Review embed (sent via Discord webhook directly)
    # ----------------------------------------------------------
    sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    run_url = os.getenv("GITHUB_RUN_URL", "https://github.com/tzuyuchang/taiwan_stock_monpoly/actions")
    embed = {
        "title": f"✅ Sprint **{plan_path.stem}** completed",
        "description": f"All {total} steps finished successfully.",
        "color": 0x00ff00,
        "fields": [
            {"name": "Commit", "value": sha, "inline": True},
            {"name": "Run URL", "value": run_url, "inline": True},
        ],
    }
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if webhook:
        import requests
        requests.post(webhook, json={"embeds": [embed]})
    else:
        print("⚠️ DISCORD_WEBHOOK_URL not set – cannot send final embed.")

# --------------------------------------------------------------
# If executed directly, run the default plan from the repo root
# --------------------------------------------------------------
if __name__ == "__main__":
    default = pathlib.Path(__file__).parents[1] / "plans" / "2026-06-13-backend-schema-api.md"
    if not default.exists():
        raise FileNotFoundError(f"Plan file not found: {default}")
    execute_plan(default)
