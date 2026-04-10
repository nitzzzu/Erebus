// Package mcp provides MCP (Model Context Protocol) integration for ErebusLite
// using the eino-ext MCP tool package.
package mcp

import (
	"context"
	"log"

	"github.com/cloudwego/eino/components/tool"
	"github.com/mark3labs/mcp-go/client"
	"github.com/mark3labs/mcp-go/mcp"

	mcptool "github.com/cloudwego/eino-ext/components/tool/mcp"

	"github.com/nitzzzu/Erebus/erebuslite/internal/config"
)

// ServerInfo holds the status info for an MCP server.
type ServerInfo struct {
	Name      string `json:"name"`
	Transport string `json:"transport"`
	Command   string `json:"command,omitempty"`
	URL       string `json:"url,omitempty"`
	Enabled   bool   `json:"enabled"`
}

// ConnectAll connects to all enabled MCP servers and returns their tools.
func ConnectAll(ctx context.Context, servers []config.MCPServerConfig) ([]tool.BaseTool, []func()) {
	var allTools []tool.BaseTool
	var cleanups []func()

	for _, srv := range servers {
		if !srv.IsEnabled() {
			continue
		}

		tools, cleanup, err := connectServer(ctx, srv)
		if err != nil {
			log.Printf("Failed to connect MCP server %q: %v", srv.Name, err)
			continue
		}

		allTools = append(allTools, tools...)
		if cleanup != nil {
			cleanups = append(cleanups, cleanup)
		}
		log.Printf("Connected MCP server (%s): %s (%d tools)", srv.Transport, srv.Name, len(tools))
	}

	return allTools, cleanups
}

func connectServer(ctx context.Context, srv config.MCPServerConfig) ([]tool.BaseTool, func(), error) {
	switch srv.Transport {
	case "sse":
		return connectSSE(ctx, srv)
	case "streamable-http":
		return connectSSE(ctx, srv) // Same client pattern
	case "stdio":
		return connectStdio(ctx, srv)
	default:
		return connectStdio(ctx, srv)
	}
}

func connectSSE(ctx context.Context, srv config.MCPServerConfig) ([]tool.BaseTool, func(), error) {
	if srv.URL == "" {
		return nil, nil, nil
	}

	cli, err := client.NewSSEMCPClient(srv.URL)
	if err != nil {
		return nil, nil, err
	}

	if err := cli.Start(ctx); err != nil {
		return nil, nil, err
	}

	initReq := mcp.InitializeRequest{}
	initReq.Params.ProtocolVersion = mcp.LATEST_PROTOCOL_VERSION
	initReq.Params.ClientInfo = mcp.Implementation{
		Name:    "erebuslite",
		Version: "0.1.0",
	}

	if _, err := cli.Initialize(ctx, initReq); err != nil {
		return nil, nil, err
	}

	tools, err := mcptool.GetTools(ctx, &mcptool.Config{Cli: cli})
	if err != nil {
		return nil, nil, err
	}

	cleanup := func() {
		_ = cli.Close()
	}

	return tools, cleanup, nil
}

func connectStdio(ctx context.Context, srv config.MCPServerConfig) ([]tool.BaseTool, func(), error) {
	if srv.Command == "" {
		return nil, nil, nil
	}

	args := append([]string{}, srv.Args...)
	cli, err := client.NewStdioMCPClient(srv.Command, nil, args...)
	if err != nil {
		return nil, nil, err
	}

	if err := cli.Start(ctx); err != nil {
		return nil, nil, err
	}

	initReq := mcp.InitializeRequest{}
	initReq.Params.ProtocolVersion = mcp.LATEST_PROTOCOL_VERSION
	initReq.Params.ClientInfo = mcp.Implementation{
		Name:    "erebuslite",
		Version: "0.1.0",
	}

	if _, err := cli.Initialize(ctx, initReq); err != nil {
		return nil, nil, err
	}

	tools, err := mcptool.GetTools(ctx, &mcptool.Config{Cli: cli})
	if err != nil {
		return nil, nil, err
	}

	cleanup := func() {
		_ = cli.Close()
	}

	return tools, cleanup, nil
}

// ListServers returns info about configured MCP servers.
func ListServers(servers []config.MCPServerConfig) []ServerInfo {
	var result []ServerInfo
	for _, srv := range servers {
		result = append(result, ServerInfo{
			Name:      srv.Name,
			Transport: srv.Transport,
			Command:   srv.Command,
			URL:       srv.URL,
			Enabled:   srv.IsEnabled(),
		})
	}
	return result
}
