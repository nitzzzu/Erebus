// Package notifications provides a simple webhook-based notification system.
package notifications

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// Channel represents a notification destination.
type Channel struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	URL       string `json:"url"`
	Enabled   bool   `json:"enabled"`
	IsDefault bool   `json:"is_default"`
}

// Manager handles CRUD for notification channels and sending.
type Manager struct {
	path     string
	channels []Channel
	mu       sync.RWMutex
}

// NewManager creates a notification manager backed by notifications.json.
func NewManager(dataDir string) *Manager {
	path := filepath.Join(dataDir, "notifications.json")
	m := &Manager{path: path}
	m.channels = m.load()
	return m
}

func (m *Manager) load() []Channel {
	data, err := os.ReadFile(m.path)
	if err != nil {
		return nil
	}
	var channels []Channel
	if err := json.Unmarshal(data, &channels); err != nil {
		return nil
	}
	return channels
}

func (m *Manager) save() error {
	data, err := json.MarshalIndent(m.channels, "", "  ")
	if err != nil {
		return err
	}
	_ = os.MkdirAll(filepath.Dir(m.path), 0o755)
	return os.WriteFile(m.path, data, 0o644)
}

// List returns all notification channels.
func (m *Manager) List() []Channel {
	m.mu.RLock()
	defer m.mu.RUnlock()
	result := make([]Channel, len(m.channels))
	copy(result, m.channels)
	return result
}

// Create adds a new notification channel.
func (m *Manager) Create(name, url string, enabled, isDefault bool) (*Channel, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	ch := Channel{
		ID:        fmt.Sprintf("%x", time.Now().UnixNano())[:12],
		Name:      name,
		URL:       url,
		Enabled:   enabled,
		IsDefault: isDefault,
	}
	m.channels = append(m.channels, ch)
	if err := m.save(); err != nil {
		return nil, err
	}
	return &ch, nil
}

// Update modifies a notification channel.
func (m *Manager) Update(id string, updates map[string]any) (*Channel, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	for i, ch := range m.channels {
		if ch.ID == id {
			if v, ok := updates["name"].(string); ok {
				m.channels[i].Name = v
			}
			if v, ok := updates["url"].(string); ok {
				m.channels[i].URL = v
			}
			if v, ok := updates["enabled"].(bool); ok {
				m.channels[i].Enabled = v
			}
			if v, ok := updates["is_default"].(bool); ok {
				m.channels[i].IsDefault = v
			}
			if err := m.save(); err != nil {
				return nil, err
			}
			return &m.channels[i], nil
		}
	}
	return nil, nil
}

// Delete removes a notification channel.
func (m *Manager) Delete(id string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	for i, ch := range m.channels {
		if ch.ID == id {
			m.channels = append(m.channels[:i], m.channels[i+1:]...)
			_ = m.save()
			return true
		}
	}
	return false
}

// Send sends a notification to a specific channel or the default channel.
func (m *Manager) Send(message, title string, channelID *string) map[string]any {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var targets []Channel
	if channelID != nil {
		for _, ch := range m.channels {
			if ch.ID == *channelID && ch.Enabled {
				targets = append(targets, ch)
			}
		}
	} else {
		for _, ch := range m.channels {
			if ch.IsDefault && ch.Enabled {
				targets = append(targets, ch)
			}
		}
	}

	if len(targets) == 0 {
		return map[string]any{"sent": false, "error": "no channels available", "channels": []string{}}
	}

	var sentTo []string
	for _, ch := range targets {
		if err := sendWebhook(ch.URL, title, message); err == nil {
			sentTo = append(sentTo, ch.Name)
		}
	}

	return map[string]any{"sent": len(sentTo) > 0, "channels": sentTo}
}

func sendWebhook(url, title, message string) error {
	payload := map[string]string{
		"title":   title,
		"message": message,
	}
	data, _ := json.Marshal(payload)
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Post(url, "application/json", bytes.NewReader(data))
	if err != nil {
		return err
	}
	resp.Body.Close()
	return nil
}
