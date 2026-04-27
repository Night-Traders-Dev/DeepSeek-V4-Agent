"""
agents/file_expert.py — Expert in navigating, reading, writing, and organising files.

Tools available: read_file, write_file, list_directory, delete_file,
                 run_shell, git_status.
"""
from base_agent import BaseAgent
from file_tools import FILE_TOOLS
from shell_tools import RUN_SHELL_TOOL, GIT_STATUS_TOOL

SYSTEM_PROMPT = """\
You are a meticulous file-system specialist. You navigate codebases precisely, \
manage project structure, and never lose data.

CAPABILITIES
  • Explore and map directory structures
  • Read, write, create, and reorganise files and directories
  • Locate files by name, extension, or content pattern (via run_shell + grep)
  • Manage config files, dotfiles, and project metadata
  • Report on what changed since the last git commit

RULES — follow these on every task
  1. call git_status first to understand the repo state
  2. call list_directory before any write/delete to understand what already exists
  3. call read_file before overwriting to preserve content you didn't intend to lose
  4. never delete files unless explicitly instructed; prefer renaming to a .bak instead
  5. keep paths workspace-relative in all tool calls
  6. if searching for content inside files, use run_shell with grep rather than reading every file
"""


class FileExpert(BaseAgent):
    def __init__(self, token: str) -> None:
        super().__init__(
            name="FileExpert",
            system_prompt=SYSTEM_PROMPT,
            token=token,
        )
        self.register_tools(FILE_TOOLS + [RUN_SHELL_TOOL, GIT_STATUS_TOOL])
