# Code Agent — smolagents-inspired Code Execution

## Overview

The **Code Agent** (`run_code_agent`) is a single tool that executes LLM-generated
Python code with all Erebus capabilities available as plain function calls. Instead
of making 5-10 separate tool calls with LLM round-trips between each, write one
Python code block that chains everything together.

Inspired by HuggingFace's [smolagents CodeAgent](https://github.com/huggingface/smolagents)
pattern — the LLM generates code that naturally composes operations using loops,
conditionals, variables, and functions.

## When to Use

Use `run_code_agent` when the task requires **chaining multiple operations**:

- Search files → read matches → process content → write results
- Run shell commands → parse output → make decisions → act on them
- Web search → fetch pages → extract data → save locally
- Read config → validate → transform → write updated config
- Git operations → file changes → commit → report

**Do NOT use** for simple single operations — use the individual tools instead.

## Available Functions

### Shell & Process
- `bash(command, timeout=60, cwd=None)` — run a shell command
- `python(code, timeout=60)` — run Python in a separate subprocess

### File System
- `read_file(path, start_line=None, end_line=None)` — read file contents
- `write_file(path, content)` — write/create a file
- `append_file(path, content)` — append to a file
- `edit_file(path, old, new, count=1)` — find-and-replace in a file
- `find_files(pattern, base_dir=None, max_results=500)` — glob for files
- `search_files(pattern, path=None, file_pattern=None, ...)` — grep/ripgrep search
- `list_dir(path=".")` — list directory contents

### Web & HTTP
- `search_web(query, max_results=5, engine="google")` — web search
- `fetch_url(url, max_length=8000)` — fetch URL as markdown
- `http_get(url, headers=None, timeout=30)` — raw HTTP GET
- `http_post(url, data=None, headers=None, timeout=30)` — raw HTTP POST

### Data Helpers
- `parse_json(text)` — parse JSON string
- `to_json(obj, indent=2)` — serialise to JSON

### Control Flow
- `final_answer(value)` — signal the final result
- `state` — persistent dict (survives across `run_code_agent` calls)

### Standard Library (directly available)
- `Path`, `re`, `json`, `os`, `glob`, `textwrap`, `shlex`
- Full Python stdlib via normal `import` statements

### Skill-Provided Tools (dynamically loaded)

Skills can extend the CodeAgent by shipping a `tools/` directory with Python
modules.  These tools are **automatically discovered** and injected into the
CodeAgent namespace — no configuration needed.

**Currently available skill tools:**

- **Obsidian** — `obsidian_search`, `obsidian_read`, `obsidian_write`, `obsidian_append`, `obsidian_list`, `obsidian_delete`
- **DuckDB** — `duckdb_query`, `duckdb_sql`, `duckdb_load_csv`, `duckdb_load_parquet`, `duckdb_load_json`, `duckdb_tables`, `duckdb_describe`, `duckdb_export_csv`
- **OSINT** — `osint_whois`, `osint_dns`, `osint_headers`, `osint_email_validate`, `osint_subdomain_enum`, `osint_ip_info`, `osint_social_check`, `osint_dorking`
- **Frida** — `frida_devices`, `frida_apps`, `frida_spawn`, `frida_attach`, `frida_unpin_ssl`, `frida_trace`, `frida_run_script`
- **Pentest** — `pentest_portscan`, `pentest_service_enum`, `pentest_web_headers`, `pentest_ssl_check`, `pentest_dir_brute`, `pentest_whatweb`, `pentest_vuln_scan`
- **Supabase** — `supa_query`, `supa_insert`, `supa_update`, `supa_delete`, `supa_rpc`, `supa_sql`, `supa_storage_list`, `supa_storage_upload`, `supa_storage_download`

To add your own skill tools, create a `tools/` directory in your skill folder
with a Python file that exports a `TOOLS` dict.  See `SKILL_TOOLS_100_IDEAS.md`
for 100 real-world ideas.

## Patterns

### Chain Search → Read → Process
```python
results = search_files("TODO|FIXME", file_pattern="*.py")
for line in results.split("\n"):
    if ":" in line:
        filepath = line.split(":")[0]
        content = read_file(filepath, 1, 10)
        print(f"--- {filepath} ---")
        print(content)
```

### Multi-Step Git Workflow
```python
status = bash("git status --short")
if status.strip():
    bash("git add -A")
    bash('git commit -m "chore: automated update"')
    print("Changes committed")
else:
    print("Working tree clean")
```

### Web Research Pipeline
```python
results = search_web("Python async patterns", max_results=3)
import re
urls = re.findall(r'https?://[^\s]+', results)
for url in urls[:2]:
    page = fetch_url(url, max_length=2000)
    print(f"\n--- {url} ---")
    print(page[:500])
```

### Persistent State Workflow
```python
# Call 1: Gather data
state["todos"] = search_files("TODO", file_pattern="*.py")
print(f"Stored {len(state['todos'])} chars of TODOs")

# Call 2: Process stored data
todos = state.get("todos", "")
print(f"Processing {len(todos)} chars of stored TODOs")
```

### Skill Tools — Obsidian + DuckDB Chain
```python
# Search Obsidian notes, load into DuckDB, analyse
notes = obsidian_list("Projects/")
for note_path in notes[:5]:
    content = obsidian_read(note_path)
    print(f"{note_path}: {len(content)} chars")

# Load a CSV and run SQL analytics
duckdb_load_csv("data/sales.csv", "sales")
result = duckdb_sql("""
    SELECT region, SUM(amount) total
    FROM sales GROUP BY region ORDER BY total DESC
""")
print(result)
```

### Skill Tools — OSINT Recon Chain
```python
# Full domain recon
domain = "target.com"
print("=== DNS ===")
print(osint_dns(domain, "A"))
print(osint_dns(domain, "MX"))
print("=== Subdomains ===")
subs = osint_subdomain_enum(domain)
print(f"Found {len(subs)} subdomains")
for s in subs[:10]:
    print(f"  {s}")
print("=== Security Headers ===")
headers = pentest_web_headers(f"https://{domain}")
for h, v in headers.items():
    print(f"  {h}: {v}")
```

## Guidelines

1. **Think before coding** — plan the sequence of operations before writing code.
2. **Print progress** — use `print()` for intermediate results so the agent can
   see what's happening.
3. **Handle errors** — wrap risky operations in try/except.
4. **Use state sparingly** — only store data that's needed across multiple calls.
5. **Keep it focused** — one code block should accomplish one coherent task.
6. **Prefer built-in functions** — use `read_file()` over `bash("cat file")` for
   better error handling and path resolution.

## Anti-Patterns

- ❌ Using `run_code_agent` for a single `bash("ls")` call — use `run_shell` instead
- ❌ Writing extremely long code blocks (>100 lines) — break into multiple calls
- ❌ Ignoring return values from functions — always check and handle results
- ❌ Storing large data in `state` — use files instead for large datasets
