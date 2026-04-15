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

# JavaScript preamble injected before user code in run_zx.
# Provides sh/cat/put/rg/rgf/gl/gh helpers and an output accumulator `o`.
_ZX_PREAMBLE = r"""
'use strict';
const {execSync} = require('child_process');
const fs = require('fs');
const path = require('path');

// Output accumulator – assign properties and they are printed as JSON at end.
const o = {};

// sh(cmd, ms?) – run a shell command, return combined stdout/stderr.
function sh(cmd, ms) {
  try {
    return execSync(cmd, {
      encoding: 'utf8',
      shell: '/bin/sh',
      timeout: ms || 30000,
    });
  } catch (e) {
    return (e.stdout || '') + (e.stderr ? '\n[stderr]\n' + e.stderr : '');
  }
}

// cat(filepath, off?, lim?) – read file lines, optional offset and line limit.
function cat(filepath, off, lim) {
  const lines = fs.readFileSync(filepath, 'utf8').split('\n');
  const start = off || 0;
  return (lim != null ? lines.slice(start, start + lim) : lines.slice(start)).join('\n');
}

// put(filepath, content) – write content to a file (creates parent dirs).
function put(filepath, content) {
  fs.mkdirSync(path.dirname(path.resolve(filepath)), {recursive: true});
  fs.writeFileSync(filepath, content, 'utf8');
  return 'written: ' + filepath;
}

// _hasRg – true if the rg binary is available on PATH.
const _hasRg = (() => {
  try { execSync('rg --version', {stdio: 'ignore'}); return true; } catch { return false; }
})();

// _esc(arg) – single-quote-escape a shell argument.
function _esc(arg) { return "'" + String(arg).replace(/'/g, "'\\''") + "'"; }

// rg(pat, searchPath?, opts?) – search for pattern, return matching lines.
// opts: {A, B, C, glob, type, i, head}
function rg(pat, searchPath, opts) {
  if (_hasRg) {
    const args = ['rg', _esc(pat)];
    if (opts) {
      if (opts.A) args.push('-A', String(opts.A));
      if (opts.B) args.push('-B', String(opts.B));
      if (opts.C) args.push('-C', String(opts.C));
      if (opts.glob) args.push('--glob', _esc(opts.glob));
      if (opts.type) args.push('--type', _esc(opts.type));
      if (opts.i) args.push('-i');
      if (opts.head) args.push('--max-count', String(opts.head));
    }
    if (searchPath) args.push(_esc(searchPath));
    return sh(args.join(' '));
  }
  // fallback: grep -rP
  const gArgs = ['grep', '-rP'];
  if (opts && opts.i) gArgs.push('-i');
  gArgs.push(_esc(pat));
  if (searchPath) gArgs.push(_esc(searchPath));
  return sh(gArgs.join(' '));
}

// rgf(pat, searchPath?, glob?) – search for pattern, return file paths only.
function rgf(pat, searchPath, glob_pat) {
  if (_hasRg) {
    const args = ['rg', '-l', _esc(pat)];
    if (glob_pat) args.push('--glob', _esc(glob_pat));
    if (searchPath) args.push(_esc(searchPath));
    return sh(args.join(' '));
  }
  const args = ['grep', '-rlP', _esc(pat)];
  if (searchPath) args.push(_esc(searchPath));
  return sh(args.join(' '));
}

// gl(pat, path?) – glob for file paths.
function gl(pat, searchPath) {
  if (typeof fs.globSync === 'function') {
    const results = fs.globSync(pat, {cwd: searchPath || '.'});
    return results.join('\n');
  }
  // Fallback for older Node: use find + shell glob expansion.
  const base = _esc(searchPath || '.');
  return sh('find ' + base + ' -path ' + _esc(pat) + ' 2>/dev/null');
}

// gh(args) – run the GitHub CLI.
function gh(args) {
  return sh('gh ' + args);
}
""".lstrip()


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
        self.register(self.run_zx)

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

    def run_zx(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> str:
        """Execute JavaScript code with zx-style utility functions pre-loaded.

        Runs the code in a Node.js subprocess after injecting a preamble that
        defines the following helpers (inspired by Claude Code v2.1.108 and
        google/zx):

        **Shell & File**

        * ``sh(cmd, ms?)`` — run a shell command (optional timeout in ms)
        * ``cat(path, off?, lim?)`` — read file content (optional line offset
          and limit)
        * ``put(path, content)`` — write a file

        **Search & Glob**

        * ``rg(pat, path?, opts?)`` — search for pattern (ripgrep / grep
          fallback), returns match text.  ``opts`` may include ``A``, ``B``,
          ``C``, ``glob``, ``type``, ``i``, ``head``.
        * ``rgf(pat, path?, glob?)`` — search for pattern, returns file paths
        * ``gl(pat, path?)`` — glob for file paths

        **GitHub**

        * ``gh(args)`` — run the ``gh`` CLI

        **Output accumulator**

        * ``o`` — plain object; if any keys are assigned, its contents are
          automatically printed as JSON at the end of execution.

        Parameters
        ----------
        code:
            JavaScript source code to execute.
        timeout:
            Maximum execution time in seconds (default 30).

        Returns
        -------
        str
            Combined stdout / stderr from the execution.

        Examples
        --------
        .. code-block:: javascript

            o.cwd = sh("pwd");
            o.mdFiles = rgf("\\\\.md$");
            o.readme = cat("README.md", 0, 20);
            console.log("done");
        """
        epilogue = (
            "\n// Auto-print output accumulator if populated.\n"
            "if (typeof o === 'object' && o !== null && Object.keys(o).length > 0) {\n"
            "  console.log(JSON.stringify(o, null, 2));\n"
            "}\n"
        )
        full_code = _ZX_PREAMBLE + "\n" + code + epilogue
        effective_timeout = timeout or self._timeout
        old_timeout = self._timeout
        self._timeout = effective_timeout
        result = self._execute(["node", "-"], full_code)
        self._timeout = old_timeout
        return result
