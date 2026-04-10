"""Agno Toolkit for interactive code execution (REPL).

Provides Python and Node.js execution environments.  Each invocation
runs in a fresh subprocess (stateless) — for stateful sessions use
the ShellTools bash with a persistent process instead.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30
_MAX_OUTPUT = 10_000


class REPLTools(Toolkit):
    """Agent tools for executing Python and Node.js code snippets."""

    def __init__(
        self,
        timeout: int = _DEFAULT_TIMEOUT,
        workspace_path: Optional[str] = None,
    ) -> None:
        self._timeout = timeout
        self._workspace_path = workspace_path
        super().__init__(name="repl")
        self.register(self.run_python)
        self.register(self.run_node)
        self.register(self.run_shell)

    def _cwd(self) -> Optional[str]:
        if self._workspace_path and Path(self._workspace_path).exists():
            return self._workspace_path
        return None

    def _execute(
        self,
        cmd: list[str],
        code: str,
        env: Optional[dict] = None,
    ) -> str:
        """Run ``cmd`` with ``code`` on stdin, return combined output."""
        cwd = self._cwd()
        run_env = {**os.environ}
        if env:
            run_env.update(env)
        try:
            result = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=cwd,
                env=run_env,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            output = stdout
            if stderr.strip():
                output = output + ("\n" if output else "") + f"[stderr]\n{stderr}"
            if len(output) > _MAX_OUTPUT:
                output = output[:_MAX_OUTPUT] + f"\n[output truncated at {_MAX_OUTPUT} chars]"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return f"Execution timed out after {self._timeout}s."
        except FileNotFoundError as exc:
            return f"Interpreter not found: {exc}"
        except Exception as exc:
            return f"Execution error: {exc}"

    def run_python(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> str:
        """Execute a Python code snippet and return its output.

        The snippet runs in a fresh Python subprocess with the workspace
        directory as the working directory (if set).

        Parameters
        ----------
        code:
            Python source code to execute.
        timeout:
            Maximum execution time in seconds (default 30).

        Returns
        -------
        str
            Combined stdout / stderr from the execution.
        """
        effective_timeout = timeout or self._timeout
        old_timeout = self._timeout
        self._timeout = effective_timeout
        result = self._execute([sys.executable, "-"], code)
        self._timeout = old_timeout
        return result

    def run_node(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> str:
        """Execute a Node.js code snippet and return its output.

        Requires ``node`` to be on PATH.

        Parameters
        ----------
        code:
            JavaScript / Node.js source code to execute.
        timeout:
            Maximum execution time in seconds (default 30).

        Returns
        -------
        str
            Combined stdout / stderr from the execution.
        """
        effective_timeout = timeout or self._timeout
        old_timeout = self._timeout
        self._timeout = effective_timeout
        result = self._execute(["node", "-"], code)
        self._timeout = old_timeout
        return result

    def run_shell(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
    ) -> str:
        """Execute a shell command and return its output.

        This is a lightweight alternative to the full ShellTools for quick
        one-off commands.  The working directory defaults to the active
        workspace root.

        Parameters
        ----------
        command:
            Shell command to execute (passed to ``/bin/sh -c``).
        timeout:
            Maximum execution time in seconds (default 30).
        cwd:
            Override working directory (default: workspace root or cwd).

        Returns
        -------
        str
            Combined stdout / stderr.
        """
        effective_timeout = timeout or self._timeout
        run_cwd = cwd or self._cwd() or os.getcwd()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=run_cwd,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            output = stdout
            if stderr.strip():
                output = output + ("\n" if output else "") + f"[stderr]\n{stderr}"
            if len(output) > _MAX_OUTPUT:
                output = output[:_MAX_OUTPUT] + f"\n[output truncated at {_MAX_OUTPUT} chars]"
            return output.strip() or f"(exited with code {result.returncode})"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {effective_timeout}s."
        except Exception as exc:
            return f"Error: {exc}"
