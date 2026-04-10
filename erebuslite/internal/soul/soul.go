// Package soul manages agent personality/instructions loaded from SOUL.md files.
package soul

import (
	"os"
	"path/filepath"
)

// DefaultSoul is the built-in personality when no SOUL.md is found.
const DefaultSoul = `You are **Erebus**, a highly capable AI assistant.

## Core Traits
- Friendly, concise, and insightful.
- Always cite sources when providing factual information.
- Proactively use tools and skills when they can help.
- Remember user preferences across conversations.

## Communication Style
- Use markdown formatting for clarity.
- When presenting lists or data, prefer tables.
- Keep responses focused — quality over quantity.
`

// Load returns the soul instructions from SOUL.md, trying custom path,
// then data_dir/SOUL.md, then falling back to the built-in default.
func Load(soulFile, dataDir string) string {
	if soulFile != "" {
		if content, err := os.ReadFile(soulFile); err == nil {
			return string(content)
		}
	}

	defaultPath := filepath.Join(dataDir, "SOUL.md")
	if content, err := os.ReadFile(defaultPath); err == nil {
		return string(content)
	}

	return DefaultSoul
}

// Save writes the given soul content to disk.
func Save(content, dataDir string) (string, error) {
	target := filepath.Join(dataDir, "SOUL.md")
	if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
		return "", err
	}
	return target, os.WriteFile(target, []byte(content), 0o644)
}
