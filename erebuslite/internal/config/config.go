// Package config handles ErebusLite configuration loaded from
// environment variables and TOML config files.
package config

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/BurntSushi/toml"
)

// Config holds all ErebusLite settings.
type Config struct {
	// Data & Storage
	DataDir string

	// Model Configuration
	DefaultModel   string
	ReasoningModel string

	// API Server
	APIHost string
	APIPort int

	// Skills
	SkillsDir string

	// Soul
	SoulFile string

	// API Keys
	OpenAIAPIKey     string
	AnthropicAPIKey  string
	GoogleAPIKey     string
	OpenRouterAPIKey string

	// Agent config (from TOML)
	Agent  AgentConfig
	Skills SkillsConfig
	MCP    MCPConfig
}

// AgentConfig holds the [agent] section from erebus.toml.
type AgentConfig struct {
	Name           string `toml:"name"`
	DefaultModel   string `toml:"default_model"`
	ReasoningModel string `toml:"reasoning_model"`
	Instructions   string `toml:"instructions"`
}

// SkillsConfig holds the [skills] section from erebus.toml.
type SkillsConfig struct {
	ExtraDirs []string       `toml:"extra_dirs"`
	Disabled  []string       `toml:"disabled"`
	GitHub    []GitHubSkills `toml:"github"`
}

// GitHubSkills defines a GitHub repo to load skills from.
type GitHubSkills struct {
	Repo string `toml:"repo"`
	Path string `toml:"path"`
	Ref  string `toml:"ref"`
}

// MCPConfig holds the [mcp] section from erebus.toml.
type MCPConfig struct {
	Servers []MCPServerConfig `toml:"servers"`
}

// MCPServerConfig defines a single MCP server connection.
type MCPServerConfig struct {
	Name           string            `toml:"name"`
	Command        string            `toml:"command"`
	Args           []string          `toml:"args"`
	Env            map[string]string `toml:"env"`
	URL            string            `toml:"url"`
	Transport      string            `toml:"transport"`
	Enabled        *bool             `toml:"enabled"`
	TimeoutSeconds int               `toml:"timeout_seconds"`
}

// IsEnabled returns whether this MCP server is enabled (defaults to true).
func (m MCPServerConfig) IsEnabled() bool {
	if m.Enabled == nil {
		return true
	}
	return *m.Enabled
}

// tomlFile is the structure used to decode the erebus.toml config file.
type tomlFile struct {
	Agent  AgentConfig  `toml:"agent"`
	Skills SkillsConfig `toml:"skills"`
	MCP    MCPConfig    `toml:"mcp"`
}

// Load creates a Config by reading environment variables and the config file.
func Load() *Config {
	homeDir, _ := os.UserHomeDir()
	defaultDataDir := filepath.Join(homeDir, ".erebus")

	cfg := &Config{
		DataDir:      envOr("EREBUS_DATA_DIR", defaultDataDir),
		DefaultModel: envOr("EREBUS_DEFAULT_MODEL", "openai:gpt-4o"),
		APIHost:      envOr("EREBUS_API_HOST", "0.0.0.0"),
		APIPort:      envOrInt("EREBUS_API_PORT", 8741),
		SkillsDir:    os.Getenv("EREBUS_SKILLS_DIR"),
		SoulFile:     os.Getenv("EREBUS_SOUL_FILE"),

		OpenAIAPIKey:     os.Getenv("EREBUS_OPENAI_API_KEY"),
		AnthropicAPIKey:  os.Getenv("EREBUS_ANTHROPIC_API_KEY"),
		GoogleAPIKey:     os.Getenv("EREBUS_GOOGLE_API_KEY"),
		OpenRouterAPIKey: os.Getenv("EREBUS_OPENROUTER_API_KEY"),
	}

	// Also check non-prefixed env vars as fallback for API keys
	if cfg.OpenAIAPIKey == "" {
		cfg.OpenAIAPIKey = os.Getenv("OPENAI_API_KEY")
	}

	// Load TOML config
	tf := loadTOML()
	cfg.Agent = tf.Agent
	cfg.Skills = tf.Skills
	cfg.MCP = tf.MCP

	// Config file overrides
	if tf.Agent.DefaultModel != "" {
		cfg.DefaultModel = tf.Agent.DefaultModel
	}
	if tf.Agent.ReasoningModel != "" {
		cfg.ReasoningModel = tf.Agent.ReasoningModel
	}

	// Ensure data dir exists
	_ = os.MkdirAll(cfg.DataDir, 0o755)

	return cfg
}

// IsAgentConfigured returns true if at least one API key is set.
func (c *Config) IsAgentConfigured() bool {
	return c.OpenAIAPIKey != "" ||
		c.AnthropicAPIKey != "" ||
		c.GoogleAPIKey != "" ||
		c.OpenRouterAPIKey != ""
}

// ModelProvider extracts the provider part from a "provider:model" string.
func (c *Config) ModelProvider() string {
	parts := strings.SplitN(c.DefaultModel, ":", 2)
	if len(parts) == 2 {
		return parts[0]
	}
	return "openai"
}

// ModelID extracts the model ID part from a "provider:model" string.
func (c *Config) ModelID() string {
	parts := strings.SplitN(c.DefaultModel, ":", 2)
	if len(parts) == 2 {
		return parts[1]
	}
	return c.DefaultModel
}

// APIKeyForProvider returns the API key for the given provider name.
func (c *Config) APIKeyForProvider(provider string) string {
	switch strings.ToLower(provider) {
	case "openai":
		return c.OpenAIAPIKey
	case "anthropic":
		return c.AnthropicAPIKey
	case "google":
		return c.GoogleAPIKey
	case "openrouter":
		return c.OpenRouterAPIKey
	default:
		return c.OpenAIAPIKey
	}
}

// BaseURLForProvider returns the base URL override for a provider, if any.
func (c *Config) BaseURLForProvider(provider string) string {
	switch strings.ToLower(provider) {
	case "openrouter":
		return "https://openrouter.ai/api/v1"
	default:
		return ""
	}
}

func loadTOML() tomlFile {
	var tf tomlFile

	// Search order: EREBUS_CONFIG env → ./erebus.toml → ~/.erebus/erebus.toml
	paths := []string{}
	if p := os.Getenv("EREBUS_CONFIG"); p != "" {
		paths = append(paths, p)
	}
	paths = append(paths, "erebus.toml")
	homeDir, _ := os.UserHomeDir()
	if homeDir != "" {
		paths = append(paths, filepath.Join(homeDir, ".erebus", "erebus.toml"))
	}

	for _, p := range paths {
		if _, err := os.Stat(p); err == nil {
			_, _ = toml.DecodeFile(p, &tf)
			break
		}
	}

	return tf
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func envOrInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return fallback
}
