"""
tools/shell_tools.py — Shell command execution with safety guardrails.

SECURITY:
  - Dangerous commands are intercepted and require interactive confirmation.
  - All commands run inside WORKSPACE (or a validated subdirectory).
  - Hard 60-second timeout on every invocation.
  - install_packages sanitises the package string before calling pip.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
from registry import Tool, ToolParam
from config import WORKSPACE

SHELL_TIMEOUT    = 60
MAX_OUTPUT_BYTES = 100_000   # 100 KB

# Patterns that warrant an interactive confirmation prompt
DANGEROUS_PATTERNS = [
    r"rm\s+-[a-z]*r",          # rm -r / rm -rf
    r"rmdir",
    r"mkfs",
    r"dd\s+if=",
    r"chmod\s+777",
    r">\s*/dev/",
    r":\(\)\s*\{.*\}",         # fork bomb
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bsudo\b",
    r"\bsu\s",
    r"curl\s+.*\|\s*sh",
    r"wget\s+.*\|\s*sh",
    r">\s*/etc/",
]

_DANGER_RE = re.compile("|".join(DANGEROUS_PATTERNS), re.IGNORECASE)


def _is_dangerous(cmd: str) -> bool:
    return bool(_DANGER_RE.search(cmd))


# ── Implementations ───────────────────────────────────────────────────────────

def _run_shell(command: str, cwd: str | None = None) -> dict:
    """Run a bash command, optionally in a workspace subdirectory."""
    if _is_dangerous(command):
        print(f"\n⚠️  Dangerous command detected: {command}")
        answer = input("   Approve and run? [y/N]: ").strip().lower()
        if answer != "y":
            return {"success": False, "error": "Command blocked by user."}

    work_dir = WORKSPACE.resolve()
    if cwd:
        candidate = (WORKSPACE / cwd).resolve()
        # Sandbox check
        if str(candidate).startswith(str(work_dir)):
            work_dir = candidate

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=SHELL_TIMEOUT,
            cwd=str(work_dir),
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        return {
            "success":    result.returncode == 0,
            "stdout":     result.stdout[:MAX_OUTPUT_BYTES],
            "stderr":     result.stderr[:MAX_OUTPUT_BYTES],
            "returncode": result.returncode,
            "command":    command,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timed out after {SHELL_TIMEOUT}s"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _git_status() -> dict:
    """Return short git status plus the 5 most recent commits."""
    status = _run_shell("git status --short 2>&1 && echo '---' && git log --oneline -5 2>&1")
    return status


def _install_packages(packages: str) -> dict:
    """pip install <packages> — input is sanitised before execution."""
    if not re.match(r'^[\w\-\.\[\],=<>!; ]+$', packages):
        return {"success": False, "error": "Suspicious characters in package names — rejected."}
    return _run_shell(f"pip install {packages}")


# ── Tool definitions ──────────────────────────────────────────────────────────

RUN_SHELL_TOOL = Tool(
    name="run_shell",
    description=(
        "WHEN: Use for any terminal operation that file_tools or code_tools can't handle — "
        "git commits/push/pull, running build systems (make, npm, cargo), test runners (pytest, jest), "
        "linters (ruff, eslint), moving/renaming files, creating directories, or any CLI tool. "
        "HOW: Provide a bash command string. Runs in the workspace root by default; "
        "pass cwd to run in a subdirectory. "
        "Dangerous commands (rm -rf, sudo, etc.) pause and ask for your confirmation. "
        "stdout/stderr captured; 60-second timeout."
    ),
    fn=_run_shell,
    params={
        "command": ToolParam("string", "Bash command to execute"),
        "cwd":     ToolParam("string", "Workspace-relative subdirectory to run in (optional)", required=False),
    },
)

GIT_STATUS_TOOL = Tool(
    name="git_status",
    description=(
        "WHEN: Call at the start of any task to understand what has changed. "
        "Shows modified/staged/untracked files and the last 5 commits. "
        "HOW: No arguments required."
    ),
    fn=lambda: _git_status(),
    params={},
)

INSTALL_PACKAGES_TOOL = Tool(
    name="install_packages",
    description=(
        "WHEN: Use when a Python import fails because a package is missing, "
        "or when the user asks to install dependencies. "
        "HOW: Provide a space-separated list of package specs "
        "(e.g. 'requests httpx' or 'fastapi==0.110.0 uvicorn'). Uses pip."
    ),
    fn=_install_packages,
    params={
        "packages": ToolParam("string", "Space-separated pip package specs"),
    },
)

SHELL_TOOLS = [RUN_SHELL_TOOL, GIT_STATUS_TOOL, INSTALL_PACKAGES_TOOL]
