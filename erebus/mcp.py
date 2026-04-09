"""MCP (Model Context Protocol) server integration for Erebus.

Loads MCP server configurations from the agent config file and creates
Agno ``MCPTools`` / ``MultiMCPTools`` instances that can be attached
to the agent at startup.

Configuration format (in erebus.toml or erebus.json):

    [mcp]
    [[mcp.servers]]
    name = "filesystem"
    command = "npx"
    args = ["-y", "@modelcontextprotocol/server-filesystem", "/home"]
    env = { SOME_VAR = "value" }

    [[mcp.servers]]
    name = "brave-search"
    url = "https://mcp.brave.com/sse"
    transport = "sse"

    [[mcp.servers]]
    name = "custom-api"
    url = "https://api.example.com/mcp"
    transport = "streamable-http"
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    command: Optional[str] = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None
    transport: str = "stdio"  # "stdio", "sse", or "streamable-http"
    enabled: bool = True
    timeout_seconds: int = 30

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPServerConfig":
        """Create an MCPServerConfig from a dictionary."""
        return cls(
            name=data.get("name", "unnamed"),
            command=data.get("command"),
            args=data.get("args", []),
            env=data.get("env", {}),
            url=data.get("url"),
            transport=data.get("transport", "stdio"),
            enabled=data.get("enabled", True),
            timeout_seconds=data.get("timeout_seconds", 30),
        )


def parse_mcp_configs(mcp_section: dict[str, Any]) -> list[MCPServerConfig]:
    """Parse the [mcp] section of the agent config into MCPServerConfig objects."""
    servers = mcp_section.get("servers", [])
    configs: list[MCPServerConfig] = []
    for srv in servers:
        config = MCPServerConfig.from_dict(srv)
        if config.enabled:
            configs.append(config)
    return configs


async def create_mcp_tools(configs: list[MCPServerConfig]) -> list[Any]:
    """Create and connect MCPTools instances from a list of MCP server configs.

    Returns a list of connected MCPTools instances ready to be passed to
    the agent's ``tools`` parameter.

    This function must be called in an async context.
    """
    from agno.tools.mcp import MCPTools

    tools: list[Any] = []

    for cfg in configs:
        try:
            if cfg.transport == "stdio" and cfg.command:
                # Build the full command string
                cmd_parts = [cfg.command] + cfg.args
                command_str = " ".join(cmd_parts)

                # Merge environment
                env = {**os.environ, **cfg.env} if cfg.env else None

                mcp = MCPTools(
                    command=command_str,
                    env=env,
                    tool_name_prefix=cfg.name.replace("-", "_"),
                )
                await mcp.connect()
                tools.append(mcp)
                logger.info("Connected MCP server (stdio): %s", cfg.name)

            elif cfg.transport in ("sse", "streamable-http") and cfg.url:
                mcp = MCPTools(
                    transport=cfg.transport,
                    url=cfg.url,
                    tool_name_prefix=cfg.name.replace("-", "_"),
                )
                await mcp.connect()
                tools.append(mcp)
                logger.info("Connected MCP server (%s): %s", cfg.transport, cfg.name)

            else:
                logger.warning(
                    "Skipping MCP server %s: invalid config (transport=%s, command=%s, url=%s)",
                    cfg.name,
                    cfg.transport,
                    cfg.command,
                    cfg.url,
                )

        except Exception:
            logger.exception("Failed to connect MCP server: %s", cfg.name)

    return tools


async def close_mcp_tools(tools: list[Any]) -> None:
    """Async cleanup — close all connected MCP tool instances."""
    for tool in tools:
        if hasattr(tool, "close"):
            try:
                await tool.close()
            except Exception:
                logger.debug("Could not close MCP tool: %s", tool)
