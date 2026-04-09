---
name: native-mcp
description: Connect to MCP (Model Context Protocol) servers for external tool integration. Configure stdio, SSE, or HTTP transports.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["mcp", "tools", "integration", "protocol"]
---

# Native MCP Client

Use this skill when the user wants to connect to or use MCP (Model Context Protocol) servers.

## When to Use

- User wants to connect to an external MCP server
- User asks about available MCP tools or servers
- User needs to configure MCP server connections
- User wants to use tools provided by MCP servers (filesystem, databases, APIs)

## Transport Types

| Transport | Use Case | Config Key |
|-----------|----------|------------|
| **stdio** | Local servers launched as child processes | `command` + `args` |
| **SSE** | Remote servers with Server-Sent Events | `url` with `transport = "sse"` |
| **streamable-http** | Remote servers with HTTP streaming | `url` with `transport = "streamable-http"` |

## Configuration

MCP servers are configured in `erebus.toml` or `erebus.json`:

```toml
[[mcp.servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/home"]

[[mcp.servers]]
name = "brave-search"
url = "https://mcp.brave.com/sse"
transport = "sse"
env = { BRAVE_API_KEY = "your-key" }
```

## Tool Discovery

When MCP servers are connected, their tools are automatically available to the agent.
Each server's tools are prefixed with the server name to avoid collisions.

## Security

- Only connect to trusted MCP servers
- Environment variables in `env` are passed only to the specific server process
- stdio servers run as child processes with limited permissions
- Review server permissions before connecting

## Process

1. **Check Config**: Read MCP server configuration from erebus.toml
2. **Connect**: Establish connection to configured servers
3. **Discover Tools**: List available tools from connected servers
4. **Execute**: Use MCP tools as needed for the task
5. **Report**: Show results from MCP tool execution
