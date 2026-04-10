// Package heartbeat provides a periodic task runner that reads from HEARTBEAT.md.
// Inspired by picoclaw's heartbeat system: on each tick it loads the file,
// parses quick-task sections and runs them through the agent.
package heartbeat

import (
	"context"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	defaultInterval   = 30 * time.Minute
	heartbeatFilename = "HEARTBEAT.md"
	defaultTemplate   = `# Heartbeat Tasks

## Quick Tasks (respond directly)

- Report current time and date
- Check system status

## Long Tasks (future: use spawn for async)

<!-- Add long-running tasks here -->
`
)

// ExecFunc is called for each task found in HEARTBEAT.md.
// It receives the task text and returns the agent's response.
type ExecFunc func(ctx context.Context, task string) string

// Runner periodically reads HEARTBEAT.md and runs quick tasks.
type Runner struct {
	dataDir  string
	interval time.Duration
	execFn   ExecFunc
}

// New creates a heartbeat Runner.
// interval is how often to check (use 0 for the default 30-minute interval).
func New(dataDir string, interval time.Duration, execFn ExecFunc) *Runner {
	if interval <= 0 {
		interval = defaultInterval
	}
	return &Runner{
		dataDir:  dataDir,
		interval: interval,
		execFn:   execFn,
	}
}

// Start runs the heartbeat loop until ctx is cancelled.
func (r *Runner) Start(ctx context.Context) {
	r.ensureTemplate()

	log.Printf("Heartbeat started (interval: %s)", r.interval)

	ticker := time.NewTicker(r.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			r.tick(ctx)
		}
	}
}

func (r *Runner) tick(ctx context.Context) {
	tasks := r.loadQuickTasks()
	if len(tasks) == 0 {
		return
	}

	log.Printf("Heartbeat: running %d quick task(s)", len(tasks))
	for _, task := range tasks {
		if ctx.Err() != nil {
			return
		}
		log.Printf("Heartbeat: executing task %q", task)
		result := r.execFn(ctx, task)
		if result != "" {
			log.Printf("Heartbeat task result (%q): %s", task, truncate(result, 200))
		}
	}
}

// loadQuickTasks parses the "## Quick Tasks" section from HEARTBEAT.md.
// Lines starting with "- " are task items.
func (r *Runner) loadQuickTasks() []string {
	path := filepath.Join(r.dataDir, heartbeatFilename)
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}

	var tasks []string
	inQuickSection := false

	for _, line := range strings.Split(string(data), "\n") {
		trimmed := strings.TrimSpace(line)

		// Detect section headers
		if strings.HasPrefix(trimmed, "## ") {
			inQuickSection = strings.Contains(strings.ToLower(trimmed), "quick")
			continue
		}

		if inQuickSection && strings.HasPrefix(trimmed, "- ") {
			task := strings.TrimPrefix(trimmed, "- ")
			task = strings.TrimSpace(task)
			if task != "" && !strings.HasPrefix(task, "<!--") {
				tasks = append(tasks, task)
			}
		}
	}

	return tasks
}

// ensureTemplate creates a default HEARTBEAT.md if it doesn't exist.
func (r *Runner) ensureTemplate() {
	path := filepath.Join(r.dataDir, heartbeatFilename)
	if _, err := os.Stat(path); os.IsNotExist(err) {
		if err := os.WriteFile(path, []byte(defaultTemplate), 0o644); err != nil {
			log.Printf("Heartbeat: failed to create template: %v", err)
			return
		}
		log.Printf("Heartbeat: created default template at %s", path)
	}
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}
