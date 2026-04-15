# Token-Efficient Workflows with RTK and REPL Tools

## What This Skill Covers

How to minimise LLM token consumption when running developer commands inside
Erebus, using three complementary techniques borrowed from
[rtk-ai/rtk](https://github.com/rtk-ai/rtk):

1. **`run_rtk`** — route commands through the `rtk` binary (60-90% token savings)
2. **`run_shell(compress=True)`** — built-in RTK-inspired filtering (no install needed)
3. **`usage_report()`** — comprehensive usage analytics via REPL + ccusage

---

## Why Tokens Matter

Every byte of tool output consumes context tokens.  In a 30-minute coding
session, uncompressed output typically uses ~118 000 tokens:

| Operation | Standard | Compressed | Savings |
|-----------|----------|------------|---------|
| `pytest`  | ~8 000   | ~800       | -90%    |
| `git diff`| ~10 000  | ~2 500     | -75%    |
| `git add/commit/push` | ~1 600 | ~120 | -92% |
| `cargo test` | ~25 000 | ~2 500  | -90%    |
| `ruff check` | ~3 000 | ~600     | -80%    |

---

## Technique 1: `run_rtk` (best results, optional install)

`run_rtk` routes commands through the `rtk` Rust binary.  If `rtk` is not
installed it automatically falls back to `run_shell(compress=True)`.

### Install RTK (one-time, optional)

```bash
# macOS
brew install rtk

# Linux / macOS quick install
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
```

### Usage

```python
# Inside an Erebus agent tool call:
output = run_rtk("pytest tests/ -x")          # failures only
output = run_rtk("cargo test")                 # failures only
output = run_rtk("git diff HEAD~1")            # condensed diff
output = run_rtk("git status")                 # compact status
output = run_rtk("npm run build")              # errors/warnings only
output = run_rtk("ruff check erebus/")         # lint errors only
```

When RTK is installed the output is processed by RTK's Rust filter engine.
When it is not installed, Erebus's Python-native compression applies instead
(see Technique 2).

---

## Technique 2: `run_shell(compress=True)` (no install needed)

Erebus implements the following RTK-inspired compression strategies natively:

| Strategy | Description |
|----------|-------------|
| **Deduplication** | Consecutive identical lines collapsed to `line (×N)` |
| **Test filtering** | pytest / cargo test / npm test / go test → failures + summary only |
| **Git compact** | `git add/commit/push/pull` → first meaningful result line |
| **Blank-line normalisation** | Multiple blank lines → single blank line |

```python
# Use compress=True for verbose commands:
output = run_shell("pytest tests/", compress=True)
output = run_shell("cargo build 2>&1", compress=True)
output = run_shell("git log --stat -20", compress=True)
```

**When to use `compress=True` vs `run_rtk`:**
- Use `run_rtk` for git, test runners, linters — RTK has tuned filters for these.
- Use `compress=True` for custom commands or when RTK is not available.

---

## Technique 3: `usage_report()` — Token & Spending Analytics

`usage_report()` generates a formatted report covering:
- Claude Code API spending (via `ccusage` npm package — fetched via `npx` if not installed globally)
- Recent git activity
- Workspace disk usage
- RTK installation status

Inspired by `rtk gain` and `rtk cc-economics`.

```python
# Default: last 30 days
report = usage_report()

# Custom period
report = usage_report(since_days=7)

print(report)
```

### Example output

```
# Erebus Usage Report — 2026-04-15

## Claude Code API Spending (last 30 days)
  2026-03-20  in=12,345  out=4,567  $1.2345
  2026-03-21  in=8,901   out=2,345  $0.8901
  ...
  ────────────────────────────────────────────────────────────
  TOTAL  in=234,567  out=78,901  $23.4567

## Git Activity (last 30 days)
  a1b2c3d feat: add run_rtk tool
  d4e5f6a feat: add usage_report
  ...

## Workspace Disk Usage
  42M

## RTK Status
  Not installed. Install for 60-90% token savings:
  https://github.com/rtk-ai/rtk#installation
```

### ccusage without global install

If `ccusage` is not installed globally, `usage_report()` uses
`npx --yes ccusage` automatically.  To install globally:

```bash
npm i -g ccusage
```

---

## Technique 4: Using ccusage and rtk helpers inside `run_zx`

The `run_zx` preamble now exposes `ccusage(args?)` and `rtk(cmd)` as JS
helpers, making it easy to script usage analytics:

```javascript
// Fetch monthly spending data
const monthly = JSON.parse(ccusage('monthly --json'));
const total = monthly.monthly.reduce((s, m) => s + m.totalCost, 0);
console.log(`Total spend this year: $${total.toFixed(2)}`);

// Run tests through RTK for compressed output
const testResult = rtk('pytest tests/ -x --tb=short');
console.log(testResult);

// Check git log with RTK compression
const log = rtk('git log --stat -10');
console.log(log);
```

---

## Decision Guide

```
Need compressed output?
├── For git / pytest / cargo / npm test → use run_rtk()
├── For other verbose commands → use run_shell(compress=True)
├── For scripted analytics → use run_zx with ccusage() / rtk()
└── For spending report → use usage_report()
```

---

## RTK Official Documentation

- Repository: https://github.com/rtk-ai/rtk
- Commands reference: `rtk --help` or https://github.com/rtk-ai/rtk#commands
- ccusage package: https://www.npmjs.com/package/ccusage
