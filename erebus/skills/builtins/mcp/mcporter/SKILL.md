---
name: mcporter
description: CLI bridge for discovering, calling, and managing MCP servers directly from the terminal using mcporter.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["mcp", "cli", "bridge", "tools"]
---

# MCPorter — CLI MCP Bridge

Use this skill for ad-hoc MCP server interaction from the terminal.

## When to Use

- User wants to test or explore an MCP server interactively
- User needs to call a specific MCP tool once without full integration
- User wants to list tools available on an MCP server
- User needs to debug MCP server connectivity

## Installation

```bash
pip install mcporter
```

## Usage

### List available tools on an MCP server
```bash
mcporter list-tools --command "npx -y @modelcontextprotocol/server-filesystem /tmp"
```

### Call a specific tool
```bash
mcporter call --command "npx -y @modelcontextprotocol/server-filesystem /tmp" \
  --tool read_file --args '{"path": "/tmp/test.txt"}'
```

### Discover servers from an MCP registry
```bash
mcporter discover
```

## Process

1. **Identify Server**: Determine which MCP server to interact with
2. **List Tools**: Use `mcporter list-tools` to see available capabilities
3. **Call Tools**: Execute specific tools with required arguments
4. **Parse Results**: Process and present the tool output
