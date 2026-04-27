"""
agents/base_agent.py — Core agentic loop shared by every expert and the orchestrator.

Responsibilities:
  1. Construct API payloads (messages + tool schemas).
  2. Parse both Puter-format and OpenAI-format responses.
  3. Run the tool-call loop until the model produces a text-only response.
  4. Stream the final user-facing response to stdout.
"""
from __future__ import annotations
import json
import sys
import requests
from registry import ToolRegistry, Tool
import config


class BaseAgent:
    """
    All agents extend this class.

    Subclasses define:
      - ``name``          – displayed in log output
      - ``system_prompt`` – expert persona and rules
      - call ``register_tools(tools)`` in ``__init__``
    """

    def __init__(self, name: str, system_prompt: str, token: str) -> None:
        self.name          = name
        self.system_prompt = system_prompt
        self.registry      = ToolRegistry()
        self._headers      = {**config.API_HEADERS, "Authorization": f"Bearer {token}"}

    # ── Tool registration ─────────────────────────────────────────────────────

    def register_tools(self, tools: list[Tool]) -> None:
        for tool in tools:
            self.registry.register(tool)

    # ── API layer ─────────────────────────────────────────────────────────────

    def _call(self, messages: list[dict]) -> dict | None:
        """Collects a full streaming response and returns it as a parsed dict."""

        payload: dict = {
            "interface": "puter-chat-completion",
            "driver":    "openai",
            "method":    "complete",
            "args": {
                "model":    config.MODEL,
                "messages": messages,
                "stream":   True,
            }
        }

        schemas = self.registry.schemas()
        if schemas:
            payload["tools"]       = schemas
            payload["tool_choice"] = "auto"

        full_text = []
        try:
            resp = requests.post(
                config.API_URL,
                headers=self._headers,
                json=payload,
                timeout=config.REQUEST_TIMEOUT,
                stream=True,
            )
            resp.raise_for_status()

            for raw in resp.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    text = chunk.get("text") or chunk.get("reasoning") or ""
                    if not text and "choices" in chunk:
                        text = chunk["choices"][0].get("delta", {}).get("content", "") or ""
                    if text:
                        full_text.append(text)
                except json.JSONDecodeError:
                    continue

            return {"text": "".join(full_text)}

        except requests.HTTPError as exc:
            print(f"\n[{self.name}] HTTP {exc.response.status_code}: {exc.response.text[:400]}")
        except Exception as exc:
            print(f"\n[{self.name}] Request error: {exc}")
        return None



    def _stream(self, messages: list[dict]) -> str:
        """
        Streaming API call — prints tokens to stdout as they arrive.
        Returns the complete assembled text.
        Strips tool schemas for the final answer pass (no tool calls during streaming).
        """
        payload = {"model": config.MODEL, "messages": messages, "stream": True}
        full: list[str] = []

        try:
            resp = requests.post(
                config.API_URL,
                headers=self._headers,
                json=payload,
                timeout=config.REQUEST_TIMEOUT,
                stream=True,
            )
            resp.raise_for_status()

            for raw in resp.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                    # Puter SSE format: {"text": "..."} or {"reasoning": "..."}
                    text = chunk.get("text") or chunk.get("reasoning") or ""
                    # OpenAI SSE format: choices[0].delta.content
                    if not text and "choices" in chunk:
                        text = chunk["choices"][0].get("delta", {}).get("content", "") or ""
                    if text:
                        sys.stdout.write(text)
                        sys.stdout.flush()
                        full.append(text)
                except json.JSONDecodeError:
                    continue

        except Exception as exc:
            print(f"\n[{self.name}] Stream error: {exc}")

        print()   # terminal newline
        return "".join(full)

    # ── Response parsing ──────────────────────────────────────────────────────

    def _parse_response(self, data: dict) -> tuple[str, list[dict]]:
        """
        Returns (text_content, tool_calls).
        Handles both Puter and OpenAI response shapes, including nested 'result'.
        """
        if not data:
            return "", []

        # OpenAI format: {"choices": [{"message": {...}}]}
        if "choices" in data:
            msg        = data["choices"][0].get("message", {})
            text       = msg.get("content") or ""
            tool_calls = msg.get("tool_calls") or []
            return text, tool_calls

        # Puter simple format: {"text": "..."}
        if "text" in data:
            return data["text"], []

        # Puter nested: {"result": {...}}
        if "result" in data:
            return self._parse_response(data["result"])

        return str(data), []

    # ── Agentic loop ──────────────────────────────────────────────────────────

    def run(self, task: str, verbose: bool = True) -> str:
        """
        Execute a task with the full tool-use loop.

        - Loops until the model emits a text-only response (no tool_calls).
        - Streams the final response to stdout if ``verbose=True``.
        - Returns the final text string (used by the orchestrator).
        """
        messages: list[dict] = [
            {"role": "system",  "content": self.system_prompt},
            {"role": "user",    "content": task},
        ]

        for iteration in range(config.MAX_TOOL_ITERATIONS):
            data = self._call(messages)
            if data is None:
                return f"[{self.name}] API call failed."

            text, tool_calls = self._parse_response(data)

            # ── No tool calls → final answer ──────────────────────────────────
            if not tool_calls:
                if verbose:
                    print(f"\n[{self.name}]: ", end="", flush=True)
                    # Re-issue as a streaming call so the user sees tokens arrive
                    return self._stream(messages + [{"role": "assistant", "content": text}])
                return text or f"[{self.name}] (empty response)"

            # ── Tool calls → execute and loop ─────────────────────────────────
            if verbose:
                for tc in tool_calls:
                    fn   = tc.get("function", {})
                    args = fn.get("arguments", "")[:100]
                    print(f"  🔧 [{self.name}] {fn.get('name')}({args}{'...' if len(fn.get('arguments',''))>100 else ''})")

            # Append assistant message (may include reasoning text)
            messages.append({
                "role":       "assistant",
                "content":    text or "",
                "tool_calls": tool_calls,
            })

            # Execute each tool and collect results
            for tc in tool_calls:
                result = self.registry.dispatch(
                    tc["function"]["name"],
                    tc["function"].get("arguments", "{}"),
                )
                if verbose:
                    preview = result[:200] + "…" if len(result) > 200 else result
                    print(f"     ↳ {preview}")

                messages.append({
                    "role":        "tool",
                    "tool_call_id": tc["id"],
                    "content":     result,
                })

        return f"[{self.name}] Reached max tool iterations ({config.MAX_TOOL_ITERATIONS})."
