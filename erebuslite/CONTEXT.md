# ErebusLite — Eino Documentation Context

## Eino Framework (v0.8.8)

### ChatModelAgent
- Uses `adk.NewChatModelAgent(ctx, &adk.ChatModelAgentConfig{...})` to create agents
- Implements ReAct pattern: Reason → Action → Act → Observation loop
- Tools configured via `adk.ToolsConfig { ToolsNodeConfig: compose.ToolsNodeConfig { Tools: []tool.BaseTool{...} } }`
- When no tools configured, degrades to a single ChatModel call

### Runner
- `adk.NewRunner(ctx, adk.RunnerConfig{Agent: agent})` creates a runner
- `runner.Query(ctx, "message")` returns `*AsyncIterator[*AgentEvent]`
- Events have `Output.MessageOutput.Message.Content` for text content

### AgentEvent Structure
```go
type AgentEvent struct {
    AgentName string
    Output    *AgentOutput  // Contains MessageOutput
    Action    *AgentAction  // Transfer, exit, etc.
    Err       error
}

type AgentOutput struct {
    MessageOutput *MessageVariant
}

type MessageVariant struct {
    IsStreaming   bool
    Message       *schema.Message  // Has .Content string
    MessageStream MessageStream
    Role          schema.RoleType
}
```

### Tool Creation (InferTool)
```go
tool, err := utils.InferTool("name", "description", func(ctx, *Input) (string, error) { ... })
```

### OpenAI ChatModel
```go
chatModel, err := openai.NewChatModel(ctx, &openai.ChatModelConfig{
    Model:   "gpt-4o",
    APIKey:  apiKey,
    BaseURL: baseURL, // for OpenRouter etc.
})
```

## Eino-Ext MCP Integration (v0.0.8)

### MCP Tool Loading
```go
import mcptool "github.com/cloudwego/eino-ext/components/tool/mcp"

tools, err := mcptool.GetTools(ctx, &mcptool.Config{Cli: cli})
```

### MCP Client (mcp-go v0.47.1)
- SSE: `client.NewSSEMCPClient(url)`
- Stdio: `client.NewStdioMCPClient(command, env, args...)`
- Initialize: `cli.Initialize(ctx, initRequest)`

## Dependencies
- `github.com/cloudwego/eino` v0.8.8
- `github.com/cloudwego/eino-ext/components/model/openai` v0.1.12
- `github.com/cloudwego/eino-ext/components/tool/mcp` v0.0.8
- `github.com/mark3labs/mcp-go` v0.47.1
- `github.com/BurntSushi/toml` v1.6.0
- `github.com/robfig/cron/v3` v3.0.1
- `gopkg.in/yaml.v3` v3.0.1
