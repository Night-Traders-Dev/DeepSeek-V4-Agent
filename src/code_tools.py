"""
tools/code_tools.py — Python execution and static analysis.

SECURITY: code runs in an isolated subprocess with a hard timeout and
output cap. The temp file is cleaned up after every run.
"""
from __future__ import annotations
import ast
import json
import pathlib
import subprocess
import sys
import tempfile
from registry import Tool, ToolParam

EXEC_TIMEOUT    = 30        # seconds
MAX_OUTPUT_BYTES = 50_000   # 50 KB output cap per stream


# ── Implementations ───────────────────────────────────────────────────────────

def _run_python(code: str, timeout: int = EXEC_TIMEOUT) -> dict:
    """Execute a Python script in a fresh subprocess; capture stdout + stderr."""
    tmp = pathlib.Path(tempfile.mktemp(suffix=".py"))
    try:
        tmp.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(tmp)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success":    result.returncode == 0,
            "stdout":     result.stdout[:MAX_OUTPUT_BYTES],
            "stderr":     result.stderr[:MAX_OUTPUT_BYTES],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timed out after {timeout}s"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        tmp.unlink(missing_ok=True)


def _analyze_code(code: str) -> dict:
    """
    Parse Python source with the AST module to extract:
    imports, functions (args + docstring), classes (methods + docstring).
    Does NOT execute the code.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"success": False, "error": f"SyntaxError: {exc}"}

    result: dict = {
        "success":          True,
        "imports":          [],
        "functions":        [],
        "classes":          [],
        "global_var_names": [],
    }

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            result["imports"] += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = ", ".join(a.name for a in node.names)
            result["imports"].append(f"from {node.module} import {names}")
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            result["functions"].append({
                "name":      node.name,
                "line":      node.lineno,
                "args":      [a.arg for a in node.args.args],
                "docstring": ast.get_docstring(node) or "",
                "async":     isinstance(node, ast.AsyncFunctionDef),
            })
        elif isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            result["classes"].append({
                "name":      node.name,
                "line":      node.lineno,
                "bases":     [ast.unparse(b) for b in node.bases],
                "methods":   methods,
                "docstring": ast.get_docstring(node) or "",
            })
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result["global_var_names"].append(target.id)

    return result


def _check_syntax(code: str) -> dict:
    """Fast syntax validation — no execution, returns error location on failure."""
    try:
        ast.parse(code)
        return {"success": True, "valid": True, "message": "Syntax OK"}
    except SyntaxError as exc:
        return {
            "success": True,
            "valid":   False,
            "error":   str(exc),
            "line":    exc.lineno,
            "offset":  exc.offset,
            "text":    exc.text,
        }


# ── Tool definitions ──────────────────────────────────────────────────────────

RUN_PYTHON_TOOL = Tool(
    name="run_python",
    description=(
        "WHEN: Use to execute Python code and observe actual runtime output. "
        "Use to test logic, validate algorithms, run scripts, verify fixes, "
        "or demo that generated code works before handing it to the user. "
        "HOW: Provide a complete, self-contained Python script. "
        "stdout and stderr are captured (50 KB cap). Hard 30-second timeout. "
        "Do NOT use for code that requires interactive stdin or modifies system state."
    ),
    fn=_run_python,
    params={
        "code":    ToolParam("string",  "Complete, runnable Python source code"),
        "timeout": ToolParam("integer", "Max seconds before kill (default: 30)", required=False),
    },
)

ANALYZE_CODE_TOOL = Tool(
    name="analyze_code",
    description=(
        "WHEN: Use to understand the structure of existing Python code before editing it, "
        "to list all functions and classes in a file, or to extract signatures for documentation. "
        "Faster and safer than run_python because nothing is executed. "
        "HOW: Provide the Python source as a string (read_file first, then pass content here). "
        "Returns imports, functions (with args + docstrings), classes, and global variable names."
    ),
    fn=_analyze_code,
    params={
        "code": ToolParam("string", "Python source code to analyse statically"),
    },
)

CHECK_SYNTAX_TOOL = Tool(
    name="check_syntax",
    description=(
        "WHEN: Use before writing code to a file to confirm there are no syntax errors. "
        "Much faster than run_python — no subprocess needed. "
        "HOW: Provide the Python source. Returns valid=true or the exact error with line/offset."
    ),
    fn=_check_syntax,
    params={
        "code": ToolParam("string", "Python source code to syntax-check"),
    },
)

CODE_TOOLS = [RUN_PYTHON_TOOL, ANALYZE_CODE_TOOL, CHECK_SYNTAX_TOOL]
