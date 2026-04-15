"""Agno Toolkit for interactive code execution (REPL).

Provides Python and Node.js execution environments.  Each invocation
runs in a fresh subprocess (stateless) — for stateful sessions use
the ShellTools bash with a persistent process instead.

RTK-inspired output compression is available on ``run_shell`` via the
``compress=True`` parameter, and as a transparent passthrough via
``run_rtk`` when the ``rtk`` binary is on PATH.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from agno.tools.toolkit import Toolkit

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30
_MAX_OUTPUT = 10_000

# ---------------------------------------------------------------------------
# RTK-inspired output compression helpers
# ---------------------------------------------------------------------------

# Regex patterns that identify common "test" commands.
_TEST_CMD_RE = re.compile(
    r"(^|\s)(pytest|py\.test|cargo\s+test|npm\s+(run\s+)?test|npx\s+vitest|"
    r"vitest|go\s+test|gradle\s+test|mvn\s+test|rake\s+test|rspec)\b",
    re.IGNORECASE,
)

# Regex patterns that identify lines containing test failures or errors.
_TEST_FAIL_KEEP_RE = re.compile(
    r"(FAILED|FAIL|ERROR|error\[|Error:|assert|panic|exception|traceback|"
    r"expected|actual|^\s*at\s+|^\s+File\s+\"|test result:|---\s+FAILED|"
    r"ERRORS|failures:|\d+\s+failed|\d+\s+error)",
    re.IGNORECASE,
)

# Commands that should be compressed to a single summary line.
_GIT_COMPACT_RE = re.compile(
    r"(^|\s)git\s+(add|commit|push|pull|fetch|checkout|merge|rebase|stash)\b",
    re.IGNORECASE,
)


def _compress_output(cmd: str, raw: str) -> str:
    """Apply RTK-inspired output compression to *raw* command output.

    Strategies applied (in order):

    1. **Blank-line normalisation** — consecutive blank lines are collapsed
       to a single blank line (applied first so deduplication never folds
       blank lines into ``(×N)`` markers).
    2. **Deduplication** — consecutive identical non-blank lines are collapsed
       to ``line (×N)`` to eliminate repetitive log spam.
    3. **Test filtering** — when *cmd* looks like a test runner, only lines
       that indicate failures/errors, plus the final summary line, are kept.
       Reduces pytest/cargo-test/npm-test output by ~90%.
    4. **Git compact** — for ``git add/commit/push/pull`` the output is
       trimmed to the first non-blank result line (usually all that matters).

    Parameters
    ----------
    cmd:
        The shell command that produced *raw*.
    raw:
        The raw stdout/stderr string from the command.

    Returns
    -------
    str
        Compressed output string.
    """
    lines = raw.splitlines()

    # 1. Blank-line normalisation: collapse consecutive blank lines first so
    #    the deduplication step never folds blank lines into "(×N)" markers.
    blank_normalised: list[str] = []
    prev_blank = False
    for ln in lines:
        is_blank = not ln.strip()
        if is_blank and prev_blank:
            continue
        blank_normalised.append(ln)
        prev_blank = is_blank

    # 2. Deduplication: collapse consecutive identical non-blank lines.
    deduped: list[str] = []
    run_count = 1
    for i, line in enumerate(blank_normalised):
        if i > 0 and line == blank_normalised[i - 1] and line.strip():
            run_count += 1
        else:
            if run_count > 1:
                deduped.append(f"{blank_normalised[i - 1]} (×{run_count})")
            else:
                if i > 0:
                    deduped.append(blank_normalised[i - 1])
            run_count = 1
    # flush last group
    if blank_normalised:
        if run_count > 1:
            deduped.append(f"{blank_normalised[-1]} (×{run_count})")
        else:
            deduped.append(blank_normalised[-1])

    # 3. Test filtering: keep only failure/error lines + summary.
    if _TEST_CMD_RE.search(cmd):
        filtered = [ln for ln in deduped if _TEST_FAIL_KEEP_RE.search(ln)]
        # Always keep the last non-blank line (usually the summary).
        last_non_blank = next(
            (ln for ln in reversed(deduped) if ln.strip()), None
        )
        if last_non_blank and last_non_blank not in filtered:
            filtered.append(last_non_blank)
        deduped = filtered if filtered else deduped

    # 4. Git compact: trim to first meaningful result line.
    if _GIT_COMPACT_RE.search(cmd):
        first = next((ln for ln in deduped if ln.strip()), None)
        if first:
            deduped = [first]

    return "\n".join(deduped)

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

// ccusage(args?) – fetch Claude Code API spending data via the ccusage npm
// package (https://www.npmjs.com/package/ccusage).  Falls back to npx when
// the binary is not installed globally.  Returns raw JSON or an error string.
// Examples: ccusage('daily --json'), ccusage('monthly --json')
function ccusage(args) {
  const base = (() => {
    try { execSync('ccusage --version', {stdio: 'ignore'}); return 'ccusage'; } catch { return null; }
  })();
  const cmd = base
    ? `ccusage ${args || '--json'}`
    : `npx --yes ccusage ${args || '--json'} 2>/dev/null`;
  return sh(cmd);
}

// rtk(cmd) – run a command through the rtk binary for compressed token output.
// If rtk is not installed the command is run directly.
// See https://github.com/rtk-ai/rtk for installation.
const _hasRtk = (() => {
  try { execSync('rtk --version', {stdio: 'ignore'}); return true; } catch { return false; }
})();
function rtk(cmd) {
  return sh(_hasRtk ? 'rtk ' + cmd : cmd);
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
        self.register(self.run_rtk)
        self.register(self.usage_report)

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
        compress: bool = False,
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
        compress:
            When ``True``, apply RTK-inspired output compression before
            returning: deduplication of repeated lines, test-failure-only
            filtering for test runners, git-compact output for commit/push/etc,
            and blank-line normalisation.  Reduces token consumption by
            60-90% for verbose commands.

        Returns
        -------
        str
            Combined stdout / stderr (optionally compressed).
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
            if compress and output.strip():
                output = _compress_output(command, output)
            if len(output) > _MAX_OUTPUT:
                output = output[:_MAX_OUTPUT] + f"\n[output truncated at {_MAX_OUTPUT} chars]"
            return output.strip() or f"(exited with code {result.returncode})"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {effective_timeout}s."
        except Exception as exc:
            return f"Error: {exc}"

    def run_rtk(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
    ) -> str:
        """Run a shell command through the ``rtk`` binary for compressed output.

        RTK (https://github.com/rtk-ai/rtk) is a Rust CLI proxy that reduces
        LLM token consumption 60-90% by filtering and compressing the output of
        common developer tools (``git``, ``pytest``, ``cargo test``,
        ``npm test``, ``ls``, ``grep``, etc.).

        When ``rtk`` is not installed this method transparently falls back to
        ``run_shell`` with ``compress=True`` so the caller always gets some
        form of compressed output.

        Parameters
        ----------
        command:
            Shell command to run.  RTK prepends itself automatically (e.g.
            ``git status`` becomes ``rtk git status``).
        timeout:
            Maximum execution time in seconds (default 30).
        cwd:
            Override working directory (default: workspace root or cwd).

        Returns
        -------
        str
            Token-compressed combined stdout / stderr.

        Examples
        --------
        .. code-block:: python

            # With rtk installed → ~80% fewer tokens
            output = repl.run_rtk("git diff HEAD~1")
            output = repl.run_rtk("pytest tests/ -x")
            output = repl.run_rtk("cargo test")
        """
        if shutil.which("rtk"):
            return self.run_shell(f"rtk {command}", timeout=timeout, cwd=cwd)
        # Graceful fallback: run directly with Python-native compression.
        logger.debug("rtk binary not found; falling back to run_shell(compress=True)")
        return self.run_shell(command, timeout=timeout, cwd=cwd, compress=True)

    def usage_report(
        self,
        since_days: int = 30,
    ) -> str:
        """Generate a comprehensive token-usage report using REPL tools.

        Inspired by ``rtk gain`` and ``rtk cc-economics``, this method uses
        ``run_zx`` with the ``ccusage`` npm package to fetch Claude Code API
        spending data and produce a formatted usage report.

        If ``ccusage`` is not installed it attempts to use it via ``npx``
        automatically.  When the usage data is unavailable the report falls
        back to a lightweight summary of git activity and workspace disk usage.

        Parameters
        ----------
        since_days:
            How many days of history to include (default 30).

        Returns
        -------
        str
            Formatted usage report as plain text.

        Examples
        --------
        .. code-block:: python

            report = repl.usage_report(since_days=7)
            print(report)
        """
        js_code = f"""
// ── Comprehensive usage report ──────────────────────────────────────────────
const sinceDate = (() => {{
  const d = new Date(Date.now() - {since_days} * 24 * 60 * 60 * 1000);
  return d.toISOString().slice(0, 10).replace(/-/g, '');
}})();

// 1. Claude Code spending via ccusage ----------------------------------------
let spendingSection = '';
try {{
  const raw = ccusage('daily --since ' + sinceDate);
  let parsed;
  try {{ parsed = JSON.parse(raw); }} catch {{ parsed = null; }}
  if (parsed && parsed.daily && parsed.daily.length) {{
    const rows = parsed.daily.slice(-{since_days});
    let totalIn = 0, totalOut = 0, totalCost = 0;
    const lines = rows.map(r => {{
      totalIn  += r.inputTokens  || 0;
      totalOut += r.outputTokens || 0;
      totalCost += r.totalCost   || 0;
      return `  ${{r.date}}  in=${{(r.inputTokens||0).toLocaleString()}}  out=${{(r.outputTokens||0).toLocaleString()}}  $$${{(r.totalCost||0).toFixed(4)}}`;
    }});
    spendingSection = [
      '## Claude Code API Spending (last {since_days} days)',
      ...lines,
      '  ' + '-'.repeat(60),
      `  TOTAL  in=${{totalIn.toLocaleString()}}  out=${{totalOut.toLocaleString()}}  $${{totalCost.toFixed(4)}}`,
    ].join('\\n');
  }} else {{
    spendingSection = '## Claude Code API Spending\\n  (no data — run: npm i -g ccusage)';
  }}
}} catch(e) {{
  spendingSection = '## Claude Code API Spending\\n  (ccusage unavailable: ' + e.message + ')';
}}

// 2. Git activity summary -----------------------------------------------------
const gitLog = sh(`git log --oneline --since="{since_days} days ago" 2>/dev/null | head -20`).trim();
const gitSection = gitLog
  ? '## Git Activity (last {since_days} days)\\n' + gitLog.split('\\n').map(l => '  ' + l).join('\\n')
  : '## Git Activity\\n  (no git repository or no recent commits)';

// 3. Workspace disk usage -----------------------------------------------------
const duOut = sh('du -sh . 2>/dev/null || echo "(unavailable)"').trim().split('\\t')[0];
const diskSection = '## Workspace Disk Usage\\n  ' + duOut;

// 4. RTK availability ---------------------------------------------------------
const rtkVer = sh('rtk --version 2>/dev/null').trim();
const rtkSection = rtkVer
  ? '## RTK Status\\n  Installed: ' + rtkVer + '\\n  Token savings active — run commands via run_rtk()'
  : '## RTK Status\\n  Not installed. Install for 60-90% token savings:\\n  https://github.com/rtk-ai/rtk#installation';

const report = [
  '# Erebus Usage Report — ' + new Date().toISOString().slice(0, 10),
  '',
  spendingSection,
  '',
  gitSection,
  '',
  diskSection,
  '',
  rtkSection,
].join('\\n');

console.log(report);
"""
        return self.run_zx(js_code, timeout=max(self._timeout, 60))

    def run_zx(
        self,
        code: str,
        timeout: Optional[int] = None,
    ) -> str:
        """Execute JavaScript code with zx-style utility functions pre-loaded.

        Runs the code in a Node.js subprocess after injecting a preamble that
        defines the following helpers (inspired by Claude Code v2.1.108,
        google/zx, and rtk-ai/rtk):

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

        **GitHub & Analytics**

        * ``gh(args)`` — run the ``gh`` CLI
        * ``ccusage(args?)`` — fetch Claude Code API spending via the
          ``ccusage`` npm package (or ``npx ccusage``).  Returns raw JSON.
          Example: ``ccusage('daily --json')``
        * ``rtk(cmd)`` — run a command through the ``rtk`` binary for
          token-compressed output; falls back to direct execution when ``rtk``
          is not installed.

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
            // usage analytics
            o.spending = JSON.parse(ccusage('monthly --json'));
            // token-compressed git diff
            o.diff = rtk("git diff HEAD~1");
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
