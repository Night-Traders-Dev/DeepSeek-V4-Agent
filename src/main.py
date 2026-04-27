"""
main.py — Entry point for the multi-agent coding assistant.

Run with:
    python main.py

Expects:
    ../secret      — Puter auth token
    ../SysPrompt   — (optional) custom orchestrator system prompt override
"""
import sys
from orchestrator import Orchestrator
import config

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║           🤖  Multi-Agent Coding Assistant v2               ║
║           Powered by DeepSeek v4 Pro via Puter               ║
╠══════════════════════════════════════════════════════════════╣
║  Orchestrator  →  CodeExpert  /  FileExpert                  ║
║                →  ShellExpert /  DebugExpert                 ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:  exit | quit | /clear  (wipe conversation)        ║
╚══════════════════════════════════════════════════════════════╝
"""


def main() -> None:
    # ── Load token ────────────────────────────────────────────────────────────
    try:
        token = config.load_token()
    except FileNotFoundError as exc:
        print(f"❌  {exc}")
        sys.exit(1)

    print(BANNER)
    print(f"✅  Token:     {len(token)} chars (starts: {token[:4]}…)")
    print(f"🌐  Model:     {config.MODEL}")
    print(f"📁  Workspace: {config.WORKSPACE}")
    print(f"🔁  Max loops: {config.MAX_TOOL_ITERATIONS} per agent\n")

    orchestrator = Orchestrator(token=token)

    # ── REPL ──────────────────────────────────────────────────────────────────
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋  Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("👋  Goodbye!")
            break

        if user_input.lower() == "/clear":
            orchestrator._conversation.clear()
            print("🗑️   Conversation history cleared.\n")
            continue

        orchestrator.chat(user_input)
        print()   # blank line between turns


if __name__ == "__main__":
    main()
