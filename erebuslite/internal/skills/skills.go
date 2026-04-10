// Package skills implements SKILL.md loading with hermes-style nested categories.
package skills

import (
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// Skill represents a loaded SKILL.md skill.
type Skill struct {
	Name        string   `json:"name" yaml:"name"`
	Description string   `json:"description" yaml:"description"`
	Category    string   `json:"category" yaml:"category"`
	Tags        []string `json:"tags" yaml:"tags"`
	Platforms   []string `json:"platforms" yaml:"platforms"`
	License     string   `json:"license" yaml:"license"`
	Content     string   `json:"content" yaml:"-"`
	Path        string   `json:"path" yaml:"-"`
}

// Registry holds all loaded skills.
type Registry struct {
	skills []Skill
}

// NewRegistry creates an empty skill registry.
func NewRegistry() *Registry {
	return &Registry{}
}

// LoadFromDirs loads skills from one or more directories.
func (r *Registry) LoadFromDirs(dirs ...string) {
	for _, dir := range dirs {
		r.loadDir(dir)
	}
}

func (r *Registry) loadDir(dir string) {
	_ = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() || info.Name() != "SKILL.md" {
			return nil
		}
		skill, err := parseSkillFile(path)
		if err != nil {
			return nil
		}
		// Infer category from directory structure
		if skill.Category == "" {
			rel, _ := filepath.Rel(dir, path)
			parts := strings.Split(filepath.Dir(rel), string(filepath.Separator))
			if len(parts) > 0 && parts[0] != "." {
				skill.Category = parts[0]
			}
		}
		r.skills = append(r.skills, skill)
		return nil
	})
}

// List returns all loaded skills.
func (r *Registry) List() []Skill {
	return r.skills
}

// Categories returns a deduplicated list of skill categories.
func (r *Registry) Categories() []string {
	seen := map[string]bool{}
	var cats []string
	for _, s := range r.skills {
		if s.Category != "" && !seen[s.Category] {
			seen[s.Category] = true
			cats = append(cats, s.Category)
		}
	}
	return cats
}

// ByCategory filters skills by category name.
func (r *Registry) ByCategory(category string) []Skill {
	var result []Skill
	for _, s := range r.skills {
		if s.Category == category {
			result = append(result, s)
		}
	}
	return result
}

// Summaries returns short descriptions for the agent's system prompt.
func (r *Registry) Summaries() string {
	if len(r.skills) == 0 {
		return ""
	}
	var sb strings.Builder
	sb.WriteString("\n## Available Skills\n")
	sb.WriteString("You have the following skills available. Ask to use them when relevant:\n\n")
	for _, s := range r.skills {
		sb.WriteString("- **")
		sb.WriteString(s.Name)
		sb.WriteString("**: ")
		sb.WriteString(s.Description)
		sb.WriteString("\n")
	}
	return sb.String()
}

// SaveUserSkill creates a new SKILL.md in the user-skills directory.
func SaveUserSkill(dataDir, name, description, content, category string) (string, error) {
	dir := filepath.Join(dataDir, "user-skills")
	if category != "" {
		dir = filepath.Join(dir, category)
	}
	slug := strings.ToLower(strings.ReplaceAll(name, " ", "-"))
	skillDir := filepath.Join(dir, slug)
	if err := os.MkdirAll(skillDir, 0o755); err != nil {
		return "", err
	}

	// Build SKILL.md with YAML frontmatter
	var sb strings.Builder
	sb.WriteString("---\n")
	sb.WriteString("name: " + name + "\n")
	sb.WriteString("description: " + description + "\n")
	if category != "" {
		sb.WriteString("category: " + category + "\n")
	}
	sb.WriteString("---\n\n")
	sb.WriteString(content)

	path := filepath.Join(skillDir, "SKILL.md")
	return path, os.WriteFile(path, []byte(sb.String()), 0o644)
}

// parseSkillFile reads a SKILL.md file and parses frontmatter + content.
func parseSkillFile(path string) (Skill, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Skill{}, err
	}

	content := string(data)
	skill := Skill{Path: path}

	// Parse YAML frontmatter (between --- markers)
	if strings.HasPrefix(content, "---\n") {
		end := strings.Index(content[4:], "\n---")
		if end >= 0 {
			frontmatter := content[4 : 4+end]
			skill.Content = strings.TrimSpace(content[4+end+4:])
			_ = yaml.Unmarshal([]byte(frontmatter), &skill)
		} else {
			skill.Content = content
		}
	} else {
		skill.Content = content
	}

	// Fallback name from directory
	if skill.Name == "" {
		skill.Name = filepath.Base(filepath.Dir(path))
	}

	return skill, nil
}
