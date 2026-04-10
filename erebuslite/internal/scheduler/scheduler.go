// Package scheduler provides cron-based task scheduling with JSON persistence.
package scheduler

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/robfig/cron/v3"
)

// ExecFunc is called when a schedule fires. It receives the schedule entry and
// returns an optional response string (e.g. from the agent).
type ExecFunc func(entry Entry) string

// Entry represents a single scheduled task.
type Entry struct {
	ID                  string         `json:"id"`
	Name                string         `json:"name"`
	Cron                string         `json:"cron"`
	Description         string         `json:"description"`
	Enabled             bool           `json:"enabled"`
	Payload             map[string]any `json:"payload"`
	Timezone            string         `json:"timezone"`
	NotificationChannel *string        `json:"notification_channel"`
	CreatedAt           string         `json:"created_at"`
	LastRun             *string        `json:"last_run"`
}

// Scheduler manages cron schedules persisted as JSON.
type Scheduler struct {
	path    string
	entries []Entry
	mu      sync.RWMutex

	cronRunner *cron.Cron
	cronIDs    map[string]cron.EntryID // schedule ID → cron entry ID
	execFn     ExecFunc
}

// New creates a scheduler backed by schedules.json in the given data directory.
func New(dataDir string) *Scheduler {
	path := filepath.Join(dataDir, "schedules.json")
	s := &Scheduler{
		path:    path,
		cronIDs: make(map[string]cron.EntryID),
	}
	s.entries = s.load()
	return s
}

// Start begins the cron runner. Each enabled entry will fire execFn when triggered.
// This must be called once after New().
func (s *Scheduler) Start(execFn ExecFunc) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.execFn = execFn
	s.cronRunner = cron.New(cron.WithSeconds())

	for _, entry := range s.entries {
		if !entry.Enabled {
			continue
		}
		s.registerCronEntry(entry, execFn)
	}

	s.cronRunner.Start()
	log.Printf("Scheduler started with %d active entries", len(s.cronIDs))
}

// Stop halts the cron runner.
func (s *Scheduler) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.cronRunner != nil {
		s.cronRunner.Stop()
	}
}

// registerCronEntry adds an entry to the cron runner. Must be called with s.mu held.
func (s *Scheduler) registerCronEntry(entry Entry, execFn ExecFunc) {
	if s.cronRunner == nil {
		return
	}
	cronSpec := strings.TrimSpace(entry.Cron)
	// cron/v3 with WithSeconds() uses 6-field format; 5-field standard cron needs a seconds prefix
	if len(strings.Fields(cronSpec)) == 5 {
		cronSpec = "0 " + cronSpec
	}
	eid, err := s.cronRunner.AddFunc(cronSpec, func() {
		log.Printf("Scheduler: firing entry %q (%s)", entry.Name, entry.ID)
		now := time.Now().UTC().Format(time.RFC3339)

		// Update last_run on the stored entry
		s.mu.Lock()
		for i, e := range s.entries {
			if e.ID == entry.ID {
				s.entries[i].LastRun = &now
				_ = s.save()
				break
			}
		}
		s.mu.Unlock()

		if execFn != nil {
			execFn(entry)
		}
	})
	if err != nil {
		log.Printf("Scheduler: failed to register cron entry %q: %v", entry.Name, err)
		return
	}
	s.cronIDs[entry.ID] = eid
}

func (s *Scheduler) load() []Entry {
	data, err := os.ReadFile(s.path)
	if err != nil {
		return nil
	}
	var entries []Entry
	if err := json.Unmarshal(data, &entries); err != nil {
		return nil
	}
	return entries
}

func (s *Scheduler) save() error {
	data, err := json.MarshalIndent(s.entries, "", "  ")
	if err != nil {
		return err
	}
	_ = os.MkdirAll(filepath.Dir(s.path), 0o755)
	return os.WriteFile(s.path, data, 0o644)
}

// List returns all schedule entries.
func (s *Scheduler) List() []Entry {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]Entry, len(s.entries))
	copy(result, s.entries)
	return result
}

// Create adds a new schedule entry.
func (s *Scheduler) Create(name, cronExpr, description string, payload map[string]any, tz string, notifChannel *string) (*Entry, error) {
	// Validate cron expression
	parser := cron.NewParser(cron.Minute | cron.Hour | cron.Dom | cron.Month | cron.Dow)
	if _, err := parser.Parse(cronExpr); err != nil {
		return nil, fmt.Errorf("invalid cron expression: %s", cronExpr)
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	entry := Entry{
		ID:                  fmt.Sprintf("%x", time.Now().UnixNano())[:12],
		Name:                name,
		Cron:                cronExpr,
		Description:         description,
		Enabled:             true,
		Payload:             payload,
		Timezone:            tz,
		NotificationChannel: notifChannel,
		CreatedAt:           time.Now().UTC().Format(time.RFC3339),
	}
	s.entries = append(s.entries, entry)
	if err := s.save(); err != nil {
		return nil, err
	}

	// Register with live cron runner if started
	if s.cronRunner != nil && s.execFn != nil {
		s.registerCronEntry(entry, s.execFn)
	}

	return &entry, nil
}

// Update modifies an existing schedule entry.
func (s *Scheduler) Update(id string, updates map[string]any) (*Entry, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	for i, e := range s.entries {
		if e.ID == id {
			if v, ok := updates["name"].(string); ok {
				s.entries[i].Name = v
			}
			if v, ok := updates["cron"].(string); ok {
				parser := cron.NewParser(cron.Minute | cron.Hour | cron.Dom | cron.Month | cron.Dow)
				if _, err := parser.Parse(v); err != nil {
					return nil, fmt.Errorf("invalid cron expression: %s", v)
				}
				s.entries[i].Cron = v
			}
			if v, ok := updates["description"].(string); ok {
				s.entries[i].Description = v
			}
			if v, ok := updates["enabled"].(bool); ok {
				s.entries[i].Enabled = v
			}
			if v, ok := updates["timezone"].(string); ok {
				s.entries[i].Timezone = v
			}
			if err := s.save(); err != nil {
				return nil, err
			}

			// Sync live cron runner: remove old entry and re-add if enabled
			if s.cronRunner != nil && s.execFn != nil {
				if cronID, ok := s.cronIDs[id]; ok {
					s.cronRunner.Remove(cronID)
					delete(s.cronIDs, id)
				}
				if s.entries[i].Enabled {
					s.registerCronEntry(s.entries[i], s.execFn)
				}
			}

			return &s.entries[i], nil
		}
	}
	return nil, nil
}

// Delete removes a schedule entry by ID.
func (s *Scheduler) Delete(id string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	for i, e := range s.entries {
		if e.ID == id {
			s.entries = append(s.entries[:i], s.entries[i+1:]...)
			_ = s.save()
			// Remove from live cron runner
			if s.cronRunner != nil {
				if cronID, ok := s.cronIDs[id]; ok {
					s.cronRunner.Remove(cronID)
					delete(s.cronIDs, id)
				}
			}
			return true
		}
	}
	return false
}
