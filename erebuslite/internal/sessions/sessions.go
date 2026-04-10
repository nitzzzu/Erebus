// Package sessions provides persistent chat session storage using JSON files.
package sessions

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"
)

// Session represents a single chat session.
type Session struct {
	SessionID string           `json:"session_id"`
	Title     string           `json:"title"`
	Model     string           `json:"model"`
	Messages  []Message        `json:"messages"`
	CreatedAt float64          `json:"created_at"`
	UpdatedAt float64          `json:"updated_at"`
	Pinned    bool             `json:"pinned"`
	Archived  bool             `json:"archived"`
	ToolCalls []map[string]any `json:"tool_calls"`
}

// Message represents a single message in a session.
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// Compact returns metadata-only dict (no messages) for list views.
type SessionCompact struct {
	SessionID    string  `json:"session_id"`
	Title        string  `json:"title"`
	Model        string  `json:"model"`
	MessageCount int     `json:"message_count"`
	CreatedAt    float64 `json:"created_at"`
	UpdatedAt    float64 `json:"updated_at"`
	Pinned       bool    `json:"pinned"`
	Archived     bool    `json:"archived"`
}

// Compact returns a compact representation of the session without messages.
func (s *Session) Compact() SessionCompact {
	return SessionCompact{
		SessionID:    s.SessionID,
		Title:        s.Title,
		Model:        s.Model,
		MessageCount: len(s.Messages),
		CreatedAt:    s.CreatedAt,
		UpdatedAt:    s.UpdatedAt,
		Pinned:       s.Pinned,
		Archived:     s.Archived,
	}
}

// Store manages session persistence and caching.
type Store struct {
	dataDir string
	mu      sync.RWMutex
	cache   map[string]*Session
}

// NewStore creates a new session store.
func NewStore(dataDir string) *Store {
	dir := filepath.Join(dataDir, "sessions")
	_ = os.MkdirAll(dir, 0o755)
	return &Store{
		dataDir: dataDir,
		cache:   make(map[string]*Session),
	}
}

func (s *Store) sessionsDir() string {
	return filepath.Join(s.dataDir, "sessions")
}

func (s *Store) sessionPath(sid string) string {
	return filepath.Join(s.sessionsDir(), sid+".json")
}

// Save persists a session to disk and updates the cache.
func (s *Store) Save(session *Session) error {
	session.UpdatedAt = float64(time.Now().Unix())
	data, err := json.Marshal(session)
	if err != nil {
		return err
	}
	if err := os.WriteFile(s.sessionPath(session.SessionID), data, 0o644); err != nil {
		return err
	}
	s.mu.Lock()
	s.cache[session.SessionID] = session
	s.mu.Unlock()
	return nil
}

// Load retrieves a session from cache or disk.
func (s *Store) Load(sid string) (*Session, error) {
	s.mu.RLock()
	if sess, ok := s.cache[sid]; ok {
		s.mu.RUnlock()
		return sess, nil
	}
	s.mu.RUnlock()

	data, err := os.ReadFile(s.sessionPath(sid))
	if err != nil {
		return nil, err
	}
	var session Session
	if err := json.Unmarshal(data, &session); err != nil {
		return nil, err
	}
	s.mu.Lock()
	s.cache[sid] = &session
	s.mu.Unlock()
	return &session, nil
}

// New creates and persists a new session.
func (s *Store) New(model, title string) (*Session, error) {
	now := float64(time.Now().Unix())
	sid := fmt.Sprintf("%x", time.Now().UnixNano())[:12]
	session := &Session{
		SessionID: sid,
		Title:     title,
		Model:     model,
		Messages:  []Message{},
		CreatedAt: now,
		UpdatedAt: now,
		ToolCalls: []map[string]any{},
	}
	if err := s.Save(session); err != nil {
		return nil, err
	}
	return session, nil
}

// Delete removes a session from disk and cache.
func (s *Store) Delete(sid string) bool {
	s.mu.Lock()
	delete(s.cache, sid)
	s.mu.Unlock()
	path := s.sessionPath(sid)
	if err := os.Remove(path); err != nil {
		return false
	}
	return true
}

// Rename changes the title of a session.
func (s *Store) Rename(sid, title string) (*Session, error) {
	session, err := s.Load(sid)
	if err != nil {
		return nil, err
	}
	session.Title = title
	if err := s.Save(session); err != nil {
		return nil, err
	}
	return session, nil
}

// All returns compact metadata for all sessions, sorted by updated_at desc.
func (s *Store) All() []SessionCompact {
	dir := s.sessionsDir()
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	var result []SessionCompact
	for _, entry := range entries {
		if filepath.Ext(entry.Name()) != ".json" {
			continue
		}
		sid := entry.Name()[:len(entry.Name())-5] // strip .json
		session, err := s.Load(sid)
		if err != nil {
			continue
		}
		result = append(result, session.Compact())
	}
	sort.Slice(result, func(i, j int) bool {
		return result[i].UpdatedAt > result[j].UpdatedAt
	})
	return result
}
