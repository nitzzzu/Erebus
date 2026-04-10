// Package agent provides the core AI agent built on the Eino framework.
package agent

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"github.com/cloudwego/eino-ext/components/model/openai"
	"github.com/cloudwego/eino/adk"
	"github.com/cloudwego/eino/components/tool"
	"github.com/cloudwego/eino/components/tool/utils"
	"github.com/cloudwego/eino/compose"
	"github.com/cloudwego/eino/schema"

	"github.com/nitzzzu/Erebus/erebuslite/internal/config"
	"github.com/nitzzzu/Erebus/erebuslite/internal/skills"
	"github.com/nitzzzu/Erebus/erebuslite/internal/soul"
)

// Agent wraps an Eino ADK agent with session-awareness and tool integration.
type Agent struct {
	cfg      *config.Config
	registry *skills.Registry
	mcpTools []tool.BaseTool
	mu       sync.Mutex
}

// New creates a new Agent instance.
func New(cfg *config.Config, registry *skills.Registry) *Agent {
	return &Agent{
		cfg:      cfg,
		registry: registry,
	}
}

// SetMCPTools sets additional MCP tools for the agent.
func (a *Agent) SetMCPTools(tools []tool.BaseTool) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.mcpTools = tools
}

// StreamEvent represents a single event emitted during streaming.
type StreamEvent struct {
	Type string // "run_started", "token", "tool_start", "tool_end", "done", "error"
	Data map[string]any
}

// Run executes the agent with the given message and returns the full response.
func (a *Agent) Run(ctx context.Context, message string, history []map[string]string) (string, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	runner, err := a.createRunner(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to create agent runner: %w", err)
	}

	messages := buildMessages(message, history)
	iter := runner.Run(ctx, messages)
	var sb strings.Builder
	for {
		event, ok := iter.Next()
		if !ok {
			break
		}
		if event.Err != nil {
			return sb.String(), event.Err
		}
		if event.Output != nil && event.Output.MessageOutput != nil {
			mv := event.Output.MessageOutput
			if mv.Message != nil {
				sb.WriteString(mv.Message.Content)
			}
		}
	}
	return sb.String(), nil
}

// RunStream executes the agent with streaming, sending events to the provided channel.
func (a *Agent) RunStream(ctx context.Context, message string, history []map[string]string, events chan<- StreamEvent) {
	defer close(events)

	a.mu.Lock()
	runner, err := a.createRunner(ctx)
	a.mu.Unlock()

	if err != nil {
		events <- StreamEvent{Type: "error", Data: map[string]any{"message": err.Error()}}
		return
	}

	events <- StreamEvent{Type: "run_started", Data: map[string]any{}}

	messages := buildMessages(message, history)
	iter := runner.Run(ctx, messages)
	var fullContent strings.Builder

	for {
		event, ok := iter.Next()
		if !ok {
			break
		}
		if event.Err != nil {
			events <- StreamEvent{Type: "error", Data: map[string]any{"message": event.Err.Error()}}
			return
		}
		if event.Output != nil && event.Output.MessageOutput != nil {
			mv := event.Output.MessageOutput
			if mv.Message != nil && mv.Message.Content != "" {
				fullContent.WriteString(mv.Message.Content)
				events <- StreamEvent{
					Type: "token",
					Data: map[string]any{"text": mv.Message.Content},
				}
			}
		}
	}

	events <- StreamEvent{
		Type: "done",
		Data: map[string]any{
			"content": fullContent.String(),
		},
	}
}

func (a *Agent) createRunner(ctx context.Context) (*adk.Runner, error) {
	chatModel, err := a.createChatModel(ctx)
	if err != nil {
		return nil, err
	}

	// Build tools
	agentTools := a.buildTools()

	// Build instructions
	instructions := a.buildInstructions()

	agentCfg := &adk.ChatModelAgentConfig{
		Name:        a.cfg.Agent.Name,
		Description: "ErebusLite — lightweight AI assistant powered by Eino",
		Instruction: instructions,
		Model:       chatModel,
	}

	if len(agentTools) > 0 {
		agentCfg.ToolsConfig = adk.ToolsConfig{
			ToolsNodeConfig: compose.ToolsNodeConfig{
				Tools: agentTools,
			},
		}
	}

	if agentCfg.Name == "" {
		agentCfg.Name = "Erebus"
	}

	agent, err := adk.NewChatModelAgent(ctx, agentCfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create ChatModelAgent: %w", err)
	}

	runner := adk.NewRunner(ctx, adk.RunnerConfig{Agent: agent})
	return runner, nil
}

func (a *Agent) createChatModel(ctx context.Context) (*openai.ChatModel, error) {
	provider := a.cfg.ModelProvider()
	modelID := a.cfg.ModelID()
	apiKey := a.cfg.APIKeyForProvider(provider)

	if apiKey == "" {
		return nil, fmt.Errorf("no API key configured for provider %q — set EREBUS_OPENAI_API_KEY or equivalent", provider)
	}

	modelCfg := &openai.ChatModelConfig{
		Model:  modelID,
		APIKey: apiKey,
	}

	// Handle non-OpenAI providers via OpenAI-compatible endpoint
	if baseURL := a.cfg.BaseURLForProvider(provider); baseURL != "" {
		modelCfg.BaseURL = baseURL
	}

	return openai.NewChatModel(ctx, modelCfg)
}

func (a *Agent) buildTools() []tool.BaseTool {
	var tools []tool.BaseTool

	// Add MCP tools if configured
	tools = append(tools, a.mcpTools...)

	// Shell execution tool
	shellTool, err := utils.InferTool(
		"execute_shell",
		"Execute a shell command and return its output. Use for system tasks, file operations, and running programs.",
		func(ctx context.Context, input *ShellInput) (string, error) {
			cmd := exec.CommandContext(ctx, "sh", "-c", input.Command)
			out, err := cmd.CombinedOutput()
			if err != nil {
				return fmt.Sprintf("Error: %v\nOutput: %s", err, string(out)), nil
			}
			return string(out), nil
		},
	)
	if err == nil {
		tools = append(tools, shellTool)
	}

	// File read tool
	readTool, err := utils.InferTool(
		"read_file",
		"Read the contents of a file at the given path.",
		func(ctx context.Context, input *FileReadInput) (string, error) {
			data, err := os.ReadFile(input.Path)
			if err != nil {
				return "", fmt.Errorf("failed to read file: %w", err)
			}
			return string(data), nil
		},
	)
	if err == nil {
		tools = append(tools, readTool)
	}

	// File write tool
	writeTool, err := utils.InferTool(
		"write_file",
		"Write content to a file at the given path, creating directories as needed.",
		func(ctx context.Context, input *FileWriteInput) (string, error) {
			dir := filepath.Dir(input.Path)
			if dir != "" && dir != "." {
				_ = os.MkdirAll(dir, 0o755)
			}
			if err := os.WriteFile(input.Path, []byte(input.Content), 0o644); err != nil {
				return "", fmt.Errorf("failed to write file: %w", err)
			}
			return fmt.Sprintf("Written %d bytes to %s", len(input.Content), input.Path), nil
		},
	)
	if err == nil {
		tools = append(tools, writeTool)
	}

	// Web search tool (DuckDuckGo via shell)
	searchTool, err := utils.InferTool(
		"web_search",
		"Search the web using DuckDuckGo. Returns text results for the given query.",
		func(ctx context.Context, input *SearchInput) (string, error) {
			cmd := exec.CommandContext(ctx, "sh", "-c",
				fmt.Sprintf(`curl -sL "https://html.duckduckgo.com/html/?q=%s" | sed 's/<[^>]*>//g' | head -100`, input.Query))
			out, err := cmd.CombinedOutput()
			if err != nil {
				return fmt.Sprintf("Search failed: %v", err), nil
			}
			result := string(out)
			if len(result) > 2000 {
				result = result[:2000] + "..."
			}
			return result, nil
		},
	)
	if err == nil {
		tools = append(tools, searchTool)
	}

	return tools
}

func (a *Agent) buildInstructions() string {
	soulContent := soul.Load(a.cfg.SoulFile, a.cfg.DataDir)
	var sb strings.Builder
	sb.WriteString(soulContent)

	// Add config instructions
	if a.cfg.Agent.Instructions != "" {
		sb.WriteString("\n\n")
		sb.WriteString(a.cfg.Agent.Instructions)
	}

	// Add skill summaries
	if a.registry != nil {
		summaries := a.registry.Summaries()
		if summaries != "" {
			sb.WriteString("\n")
			sb.WriteString(summaries)
		}
	}

	// Add context files (AGENTS.md)
	contextContent := loadContextFiles(a.cfg.DataDir)
	if contextContent != "" {
		sb.WriteString("\n\n## Project Context\n\n")
		sb.WriteString(contextContent)
	}

	return sb.String()
}

func loadContextFiles(dataDir string) string {
	var parts []string

	// Global context file
	for _, name := range []string{"AGENTS.md", "CLAUDE.md"} {
		path := dataDir + "/" + name
		if data, err := os.ReadFile(path); err == nil {
			parts = append(parts, string(data))
			break
		}
	}

	// CWD context file
	cwd, _ := os.Getwd()
	for _, name := range []string{"AGENTS.md", "CLAUDE.md"} {
		path := cwd + "/" + name
		if data, err := os.ReadFile(path); err == nil {
			parts = append(parts, string(data))
			break
		}
	}

	return strings.Join(parts, "\n\n")
}

// Tool input types

// ShellInput is the input for the shell execution tool.
type ShellInput struct {
	Command string `json:"command" jsonschema:"description=The shell command to execute"`
}

// FileReadInput is the input for the file read tool.
type FileReadInput struct {
	Path string `json:"path" jsonschema:"description=Absolute path to the file to read"`
}

// FileWriteInput is the input for the file write tool.
type FileWriteInput struct {
	Path    string `json:"path" jsonschema:"description=Absolute path to the file to write"`
	Content string `json:"content" jsonschema:"description=The content to write to the file"`
}

// SearchInput is the input for the web search tool.
type SearchInput struct {
	Query string `json:"query" jsonschema:"description=The search query"`
}

// buildMessages converts a session history and new user message into a slice of
// schema.Message for the Eino runner.Run API. The runner prepends the system
// instruction automatically, so we only include user/assistant turns here.
func buildMessages(message string, history []map[string]string) []*schema.Message {
	msgs := make([]*schema.Message, 0, len(history)+1)
	for _, h := range history {
		role := h["role"]
		content := h["content"]
		switch role {
		case "user":
			msgs = append(msgs, schema.UserMessage(content))
		case "assistant":
			msgs = append(msgs, schema.AssistantMessage(content, nil))
		}
	}
	msgs = append(msgs, schema.UserMessage(message))
	return msgs
}

func init() {
	// Suppress noisy logs from dependencies
	log.SetFlags(log.LstdFlags | log.Lshortfile)
}
