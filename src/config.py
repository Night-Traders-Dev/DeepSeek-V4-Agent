"""
config.py — Central configuration. All tunables live here.
"""
import pathlib

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = pathlib.Path(__file__).parent
SECRET_PATH = BASE_DIR.parent / "secret"
SYSPROMPT_PATH = BASE_DIR.parent / "SysPrompt"
WORKSPACE   = pathlib.Path.cwd()   # All file tools are scoped to this dir

# ── API ───────────────────────────────────────────────────────────────────────
API_URL         = "https://api.puter.com/drivers/call"
MODEL           = "deepseek/deepseek-v4-pro"
REQUEST_TIMEOUT = 90          # seconds per HTTP request
MAX_TOOL_ITERATIONS = 12      # hard cap on agentic loops per agent

API_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent":   "Mozilla/5.0 (OS-Dev-Agent/2.0)",
    "Origin":       "https://puter.com",
    "Referer":      "https://puter.com/",
}

# ── Loaders ───────────────────────────────────────────────────────────────────
def load_token() -> str:
    if not SECRET_PATH.exists():
        raise FileNotFoundError(f"'secret' file not found: {SECRET_PATH}")
    return SECRET_PATH.read_text("utf-8").replace('\n', '').replace('\r', '').replace('"', '').replace("'", "")


def load_orchestrator_prompt() -> str:
    if SYSPROMPT_PATH.exists():
        return SYSPROMPT_PATH.read_text("utf-8").strip()
    return (
        "You are a senior engineering orchestrator managing a team of expert AI agents. "
        "Break down complex tasks and delegate precisely."
    )
