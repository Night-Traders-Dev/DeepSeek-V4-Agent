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
API_URL         = "http://localhost:11434/api/chat"  # Local Ollama endpoint
MEMORY_PATH     = BASE_DIR.parent / ".memory"
AVAILABLE_MODELS = [
    "qwen2.5-coder:14b",
    "qwen2.5-coder:7b",
    "deepseek-coder:6.7b",
    "neural-chat:7b",
    "mistral:7b",
    "llama2:13b",
]
DEFAULT_USER_PROFILE = {
    "name": "Developer",
    "pronouns": "they/them",
    "role": "Software engineer",
    "company": "",
    "timezone": "",
    "bio": "A practical, detail-oriented software engineer who appreciates concise technical answers and clear explanations.",
    "preferences": "Use my name, remember my role and preferences, and keep recommendations actionable.",
    "theme": "default",
}
MODEL           = "qwen2.5-coder:14b"
TOOL_FALLBACK_MODELS = [
    "qwen2.5-coder:7b",
    "deepseek-coder:6.7b",
]
REQUEST_TIMEOUT = 90          # seconds per HTTP request
MAX_TOOL_ITERATIONS = 12      # hard cap on agentic loops per agent
MAX_ATTACHMENTS = 6
MAX_ATTACHMENT_CHARS = 120_000
MAX_TOTAL_ATTACHMENT_CHARS = 360_000

API_HEADERS = {
    "Content-Type": "application/json",
}

# ── Loaders ───────────────────────────────────────────────────────────────────
def load_token() -> str:
    # Ollama runs locally and does not require authentication
    return "ollama-local"


def load_orchestrator_prompt() -> str:
    if SYSPROMPT_PATH.exists():
        return SYSPROMPT_PATH.read_text("utf-8").strip()
    return (
        "You are a senior engineering orchestrator managing a team of expert AI agents. "
        "Break down complex tasks and delegate precisely."
    )
