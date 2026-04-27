"""
src/refactor_loop.py — Runs an autonomous refactor loop in a sandbox.
"""
import threading
import time
from sandbox import setup_sandbox, revert_sandbox, commit_and_merge
from orchestrator import Orchestrator

class RefactorLoop(threading.Thread):
    def __init__(self, token: str):
        super().__init__(daemon=True)
        self.token = token
        self.running = False

    def run(self):
        self.running = True
        setup_sandbox()
        orch = Orchestrator(self.token)
        self.completed_tasks = []
        self.current_task = "None"

        while self.running:
            # 1. Ask Orchestrator for refactoring task
            self.current_task = "Identifying debt"
            completed_str = ", ".join(self.completed_tasks)
            prompt = f"Identify one new technical debt item NOT in this list: [{completed_str}] and refactor it in the sandbox."
            result = orch.chat(prompt)

            # 2. Check if refactor succeeded
            if "success" in result.lower():
                self.completed_tasks.append(result.split(":")[-1].strip())
                commit_and_merge()
            else:
                revert_sandbox()

            self.current_task = "Idle"
            time.sleep(60)

