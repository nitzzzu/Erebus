"""Agno Toolkit implementing the smolagents-inspired CodeAgent pattern.

Instead of defining separate tools for every operation (read file, search,
run shell, etc.), the CodeAgent exposes a **single** ``run_code_agent`` tool.
The LLM writes a Python code snippet that chains any number of built-in
helper functions — file I/O, shell commands, web search, HTTP requests,
data parsing — in one execution pass.

This is dramatically more efficient than calling tools one at a time:

* **Fewer LLM round-trips** — a single code block can do what normally
  takes 5-10 sequential tool calls.
* **Natural chaining** — use loops, conditionals, variables, and functions
  to compose operations.
* **Full Python** — the snippet runs in a real Python subprocess with
  access to the entire standard library.
* **Persistent state** — a ``state`` dict survives across calls within the
  same session for multi-step workflows.

Inspired by HuggingFace smolagents (https://github.com/huggingface/smolagents)
but adapted for the Agno framework and Erebus architecture.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 120  # code agent gets more time by default
_MAX_OUTPUT = 50_000

# The bootstrap script is injected before user code.  It:
# 1. Deserialises the persistent ``state`` dict from a temp file.
# 2. Imports all built-in helper functions into the global namespace.
# 3. Runs the user code.
# 4. Serialises ``state`` back so the next call can pick it up.
# 5. Captures the last expression value (if any) and prints a
#    structured result envelope so the outer tool can parse it.

_BOOTSTRAP_TEMPLATE = """\
# -- CodeAgent bootstrap --
import json as _json, sys as _sys, os as _os, traceback as _tb

# Restore persistent state from temp file
_state_path = {state_path!r}
try:
    with open(_state_path, "r") as _f:
        state = _json.load(_f)
except Exception:
    state = {{}}

# Configure builtins module
_os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
_sys.path.insert(0, {builtins_dir!r})
import _code_agent_builtins as _builtins
_builtins._AGENTIC_FETCH_URL = {agentic_fetch_url!r}
_builtins._WORKSPACE_PATH = {workspace_path!r}

# Inject all built-in functions into global namespace
for _name, _obj in _builtins.BUILTINS_CATALOG.items():
    globals()[_name] = _obj

# Make state available
globals()["state"] = state

# -- User code --
_result = None
_is_final = False

try:
{indented_code}
except _builtins._FinalAnswerSignal as _fa:
    _result = _fa.value
    _is_final = True
except Exception:
    _tb.print_exc()

# -- Save state & emit result envelope --
try:
    with open(_state_path, "w") as _f:
        _json.dump(state, _f)
except Exception:
    pass

# Structured result
_envelope = {{
    "is_final": _is_final,
    "result": _result,
}}
print("\\n__CODE_AGENT_RESULT__" + _json.dumps(_envelope, default=str))
"""


class CodeAgentTools(Toolkit):
    """Single-tool Agno Toolkit that executes LLM-generated Python code.

    The tool ``run_code_agent`` accepts a Python code snippet where all
    Erebus capabilities are available as plain function calls:

    **Shell & Process**
    - ``bash(command, timeout?, cwd?)`` — run a shell command
    - ``python(code, timeout?)`` — run Python in a separate subprocess

    **File System**
    - ``read_file(path, start_line?, end_line?)`` — read file contents
    - ``write_file(path, content)`` — write/create a file
    - ``append_file(path, content)`` — append to a file
    - ``edit_file(path, old, new, count?)`` — find-and-replace in a file
    - ``find_files(pattern, base_dir?, max_results?)`` — glob for files
    - ``search_files(pattern, path?, file_pattern?, ...)`` — grep/ripgrep search
    - ``list_dir(path?)`` — list directory contents

    **Web & HTTP**
    - ``search_web(query, max_results?, engine?)`` — web search (Google/HN/Reddit/GitHub)
    - ``fetch_url(url, max_length?)`` — fetch URL as markdown
    - ``http_get(url, headers?, timeout?)`` — raw HTTP GET
    - ``http_post(url, data?, headers?, timeout?)`` — raw HTTP POST

    **Data Helpers**
    - ``parse_json(text)`` — parse JSON string
    - ``to_json(obj, indent?)`` — serialise to JSON

    **Control Flow**
    - ``final_answer(value)`` — signal the final result
    - ``state`` — persistent dict (survives across calls)

    **Standard Library** (directly available)
    - ``Path``, ``re``, ``json``, ``os``, ``glob``, ``textwrap``, ``shlex``
    """

    def __init__(
        self,
        timeout: int = _DEFAULT_TIMEOUT,
        workspace_path: Optional[str] = None,
        agentic_fetch_url: Optional[str] = None,
    ) -> None:
        self._timeout = timeout
        self._workspace_path = workspace_path
        self._agentic_fetch_url = agentic_fetch_url
        # Persistent state file (one per toolkit instance / session)
        self._state_dir = tempfile.mkdtemp(prefix="erebus_codeagent_")
        self._state_path = os.path.join(self._state_dir, "state.json")
        # Initialise empty state
        with open(self._state_path, "w") as f:
            json.dump({}, f)
        super().__init__(name="code_agent")
        self.register(self.run_code_agent)

    def run_code_agent(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> str:
        """Execute a Python code snippet with all Erebus tools available as functions.

        Write Python code that chains multiple operations together. All helper
        functions are available in the global namespace — no imports needed.

        Use ``state`` (a persistent dict) to pass data between multiple calls.
        Use ``final_answer(value)`` to signal the result explicitly, or just
        let the last ``print()`` output be the result.

        Parameters
        ----------
        code:
            Python source code to execute.  All built-in helper functions
            (``bash``, ``read_file``, ``write_file``, ``search_web``, etc.)
            are available as global functions.  The full Python standard
            library is also available.
        timeout:
            Maximum execution time in seconds (default 120).

        Returns
        -------
        str
            Execution output: either the ``final_answer()`` value, or the
            combined stdout/stderr from the code.

        Examples
        --------
        Chain file search + content reading:

        .. code-block:: python

            # Find all Python files containing "TODO"
            results = search_files("TODO", file_pattern="*.py")
            print(results)

        Multi-step web research:

        .. code-block:: python

            # Search, fetch, and summarise
            results = search_web("Python 3.13 new features")
            print(results)

        Git workflow automation:

        .. code-block:: python

            # Check status, stage, commit in one pass
            status = bash("git status --short")
            if status.strip():
                bash("git add -A")
                bash('git commit -m "auto: update from code agent"')
                print("Changes committed")
            else:
                print("Working tree clean")

        Persistent state across calls:

        .. code-block:: python

            # First call: store data
            state["findings"] = search_files("def.*error", file_pattern="*.py")
            print(f"Found {len(state['findings'])} chars of results")

            # Second call: use stored data
            print(state.get("findings", "No previous findings"))
        """
        import subprocess

        effective_timeout = timeout or self._timeout

        # Indent user code to fit inside the try block
        indented = textwrap.indent(code.strip(), "    ")

        # Find the builtins module directory
        builtins_dir = str(
            Path(__file__).parent.resolve()
        )

        # Build the full script
        script = _BOOTSTRAP_TEMPLATE.format(
            state_path=self._state_path,
            builtins_dir=builtins_dir,
            agentic_fetch_url=self._agentic_fetch_url or "",
            workspace_path=self._workspace_path or os.getcwd(),
            indented_code=indented,
        )

        # Write to temp file to avoid stdin encoding issues
        script_path = os.path.join(self._state_dir, "_run.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        # Run in a subprocess
        cwd = self._workspace_path or os.getcwd()
        try:
            result = subprocess.run(
                [sys.executable, "-u", script_path],
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=cwd,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired:
            return f"Code execution timed out after {effective_timeout}s."
        except Exception as exc:
            return f"Execution error: {exc}"

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # Parse the result envelope
        marker = "__CODE_AGENT_RESULT__"
        output_lines = []
        envelope = None

        for line in stdout.split("\n"):
            if line.startswith(marker):
                try:
                    envelope = json.loads(line[len(marker):])
                except (json.JSONDecodeError, ValueError):
                    # Malformed envelope — treat as regular user output
                    output_lines.append(line)
            else:
                output_lines.append(line)

        user_output = "\n".join(output_lines).strip()

        # Add stderr if present
        if stderr.strip():
            user_output += (
                ("\n" if user_output else "") + f"[stderr]\n{stderr.strip()}"
            )

        # Build final response
        if envelope and envelope.get("is_final"):
            answer = envelope.get("result")
            if answer is not None:
                answer_str = (
                    answer if isinstance(answer, str)
                    else json.dumps(answer, indent=2, default=str)
                )
                if user_output:
                    return f"{user_output}\n\n**Result:** {answer_str}"
                return answer_str

        if len(user_output) > _MAX_OUTPUT:
            user_output = (
                user_output[:_MAX_OUTPUT]
                + f"\n[output truncated at {_MAX_OUTPUT} chars]"
            )

        return user_output or "(no output)"
