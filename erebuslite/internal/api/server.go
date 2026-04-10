// Package api implements the REST API server for ErebusLite, matching
// the Python Erebus API endpoints for compatibility with the web UI.
package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/nitzzzu/Erebus/erebuslite/internal/agent"
	"github.com/nitzzzu/Erebus/erebuslite/internal/config"
	"github.com/nitzzzu/Erebus/erebuslite/internal/notifications"
	"github.com/nitzzzu/Erebus/erebuslite/internal/scheduler"
	"github.com/nitzzzu/Erebus/erebuslite/internal/sessions"
	"github.com/nitzzzu/Erebus/erebuslite/internal/skills"
	"github.com/nitzzzu/Erebus/erebuslite/internal/soul"
)

// Server holds the HTTP API handler and all dependencies.
type Server struct {
	cfg       *config.Config
	mux       *http.ServeMux
	sessions  *sessions.Store
	skills    *skills.Registry
	scheduler *scheduler.Scheduler
	notifs    *notifications.Manager
	agent     *agent.Agent

	// Active SSE streams
	streams       map[string]chan agent.StreamEvent
	streamSessions map[string]string // streamID → sessionID
	streamsMu     sync.RWMutex
}

// New creates a new API server with all routes registered.
func New(cfg *config.Config, sessStore *sessions.Store, registry *skills.Registry, ag *agent.Agent) *Server {
	s := &Server{
		cfg:            cfg,
		sessions:       sessStore,
		skills:         registry,
		scheduler:      scheduler.New(cfg.DataDir),
		notifs:         notifications.NewManager(cfg.DataDir),
		agent:          ag,
		streams:        make(map[string]chan agent.StreamEvent),
		streamSessions: make(map[string]string),
	}

	mux := http.NewServeMux()
	s.mux = mux

	// CORS middleware is applied in ServeHTTP

	// Chat
	mux.HandleFunc("POST /api/chat", s.handleChat)
	mux.HandleFunc("POST /api/chat/start", s.handleChatStart)
	mux.HandleFunc("GET /api/chat/stream", s.handleChatStream)

	// Sessions
	mux.HandleFunc("GET /api/sessions", s.handleListSessions)
	mux.HandleFunc("POST /api/sessions", s.handleCreateSession)
	mux.HandleFunc("GET /api/sessions/{session_id}", s.handleGetSession)
	mux.HandleFunc("PUT /api/sessions/{session_id}/rename", s.handleRenameSession)
	mux.HandleFunc("DELETE /api/sessions/{session_id}", s.handleDeleteSession)

	// Memory (stub — ErebusLite doesn't have built-in memory yet)
	mux.HandleFunc("GET /api/memory/{user_id}", s.handleListMemories)
	mux.HandleFunc("DELETE /api/memory/{memory_id}", s.handleDeleteMemory)

	// Skills
	mux.HandleFunc("GET /api/skills", s.handleListSkills)
	mux.HandleFunc("GET /api/skills/categories", s.handleSkillCategories)
	mux.HandleFunc("GET /api/skills/category/{category}", s.handleSkillsByCategory)
	mux.HandleFunc("POST /api/skills", s.handleCreateSkill)

	// MCP Servers
	mux.HandleFunc("GET /api/mcp/servers", s.handleListMCPServers)

	// Config
	mux.HandleFunc("GET /api/config", s.handleGetConfig)

	// Schedules
	mux.HandleFunc("GET /api/schedules", s.handleListSchedules)
	mux.HandleFunc("POST /api/schedules", s.handleCreateSchedule)
	mux.HandleFunc("PUT /api/schedules/{schedule_id}", s.handleUpdateSchedule)
	mux.HandleFunc("DELETE /api/schedules/{schedule_id}", s.handleDeleteSchedule)

	// Soul
	mux.HandleFunc("GET /api/soul", s.handleGetSoul)
	mux.HandleFunc("PUT /api/soul", s.handleUpdateSoul)

	// Context
	mux.HandleFunc("GET /api/context", s.handleGetContext)

	// Channels
	mux.HandleFunc("GET /api/channels", s.handleListChannels)

	// Settings
	mux.HandleFunc("GET /api/settings", s.handleGetSettings)
	mux.HandleFunc("PUT /api/settings", s.handleUpdateSettings)

	// Notifications
	mux.HandleFunc("GET /api/notifications/channels", s.handleListNotificationChannels)
	mux.HandleFunc("POST /api/notifications/channels", s.handleCreateNotificationChannel)
	mux.HandleFunc("PUT /api/notifications/channels/{channel_id}", s.handleUpdateNotificationChannel)
	mux.HandleFunc("DELETE /api/notifications/channels/{channel_id}", s.handleDeleteNotificationChannel)
	mux.HandleFunc("POST /api/notifications/test", s.handleTestNotification)

	// Health
	mux.HandleFunc("GET /api/health", s.handleHealth)

	return s
}

// Handler returns the underlying HTTP handler for mounting in a gateway.
func (s *Server) Handler() http.Handler {
	return s
}

// Scheduler returns the server's scheduler instance for external lifecycle management.
func (s *Server) Scheduler() *scheduler.Scheduler {
	return s.scheduler
}

// ServeHTTP implements http.Handler with CORS support.
func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// CORS headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	s.mux.ServeHTTP(w, r)
}

// ── Helpers ─────────────────────────────────────────────────────────────────

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func readJSON(r *http.Request, v any) error {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return err
	}
	return json.Unmarshal(body, v)
}

func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"detail": msg})
}

func generateTitle(msg string) string {
	title := strings.ReplaceAll(strings.TrimSpace(msg), "\n", " ")
	if len(title) > 60 {
		title = title[:57] + "..."
	}
	return title
}

// ── Chat Handlers ───────────────────────────────────────────────────────────

func (s *Server) handleChat(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Message   string  `json:"message"`
		SessionID string  `json:"session_id"`
		UserID    string  `json:"user_id"`
		Model     *string `json:"model"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	if req.SessionID == "" {
		req.SessionID = "web-session"
	}
	if req.UserID == "" {
		req.UserID = "web-user"
	}

	model := s.cfg.DefaultModel
	if req.Model != nil && *req.Model != "" {
		model = *req.Model
	}

	// Load session history for context
	var history []map[string]string
	if session, err := s.sessions.Load(req.SessionID); err == nil {
		history = sessionMessagesToHistory(session.Messages)
	}

	ctx := r.Context()
	content, err := s.agent.Run(ctx, req.Message, history)
	if err != nil {
		writeError(w, 500, err.Error())
		return
	}

	writeJSON(w, 200, map[string]string{
		"content":    content,
		"session_id": req.SessionID,
		"model":      model,
	})
}

func (s *Server) handleChatStart(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Message   string  `json:"message"`
		SessionID *string `json:"session_id"`
		UserID    string  `json:"user_id"`
		Model     *string `json:"model"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	if req.UserID == "" {
		req.UserID = "web-user"
	}

	model := s.cfg.DefaultModel
	if req.Model != nil && *req.Model != "" {
		model = *req.Model
	}

	// Resolve or create session
	var session *sessions.Session
	if req.SessionID != nil && *req.SessionID != "" {
		var err error
		session, err = s.sessions.Load(*req.SessionID)
		if err != nil {
			session, _ = s.sessions.New(model, "New Chat")
		}
	} else {
		session, _ = s.sessions.New(model, generateTitle(req.Message))
	}

	// Build history before appending the new user message
	history := sessionMessagesToHistory(session.Messages)

	// Append user message
	session.Messages = append(session.Messages, sessions.Message{
		Role:    "user",
		Content: req.Message,
	})
	_ = s.sessions.Save(session)

	// Create stream and track session association
	streamID := fmt.Sprintf("%x", time.Now().UnixNano())[:16]
	eventCh := make(chan agent.StreamEvent, 100)

	s.streamsMu.Lock()
	s.streams[streamID] = eventCh
	s.streamSessions[streamID] = session.SessionID
	s.streamsMu.Unlock()

	// Run agent in background
	go func() {
		ctx := context.Background()
		s.agent.RunStream(ctx, req.Message, history, eventCh)
	}()

	writeJSON(w, 200, map[string]string{
		"stream_id":  streamID,
		"session_id": session.SessionID,
	})
}

func (s *Server) handleChatStream(w http.ResponseWriter, r *http.Request) {
	streamID := r.URL.Query().Get("stream_id")
	if streamID == "" {
		writeError(w, 400, "stream_id required")
		return
	}

	s.streamsMu.RLock()
	eventCh, ok := s.streams[streamID]
	s.streamsMu.RUnlock()
	if !ok {
		writeError(w, 404, "Stream not found")
		return
	}

	// SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	flusher, ok := w.(http.Flusher)
	if !ok {
		writeError(w, 500, "streaming not supported")
		return
	}

	ctx := r.Context()

	defer func() {
		s.streamsMu.Lock()
		delete(s.streams, streamID)
		sessionID := s.streamSessions[streamID]
		delete(s.streamSessions, streamID)
		s.streamsMu.Unlock()
		_ = sessionID // sessionID used in saveAssistantMessage via closure
	}()

	for {
		select {
		case <-ctx.Done():
			return
		case event, open := <-eventCh:
			if !open {
				return
			}
			data, _ := json.Marshal(event.Data)
			fmt.Fprintf(w, "event: %s\ndata: %s\n\n", event.Type, string(data))
			flusher.Flush()

			if event.Type == "done" || event.Type == "error" {
				// Save session with assistant response
				if event.Type == "done" {
					if content, ok := event.Data["content"].(string); ok {
						s.streamsMu.RLock()
						sid := s.streamSessions[streamID]
						s.streamsMu.RUnlock()
						s.saveAssistantMessage(sid, content)
					}
				}
				return
			}
		case <-time.After(30 * time.Second):
			// Heartbeat
			fmt.Fprintf(w, "event: heartbeat\ndata: \n\n")
			flusher.Flush()
		}
	}
}

func (s *Server) saveAssistantMessage(sessionID string, content string) {
	if sessionID == "" || content == "" {
		return
	}
	session, err := s.sessions.Load(sessionID)
	if err != nil {
		return
	}
	session.Messages = append(session.Messages, sessions.Message{
		Role:    "assistant",
		Content: content,
	})
	_ = s.sessions.Save(session)
}

// ── Session Handlers ────────────────────────────────────────────────────────

func (s *Server) handleListSessions(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"sessions": s.sessions.All()})
}

func (s *Server) handleCreateSession(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Title string  `json:"title"`
		Model *string `json:"model"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	if req.Title == "" {
		req.Title = "New Chat"
	}
	model := s.cfg.DefaultModel
	if req.Model != nil && *req.Model != "" {
		model = *req.Model
	}
	session, err := s.sessions.New(model, req.Title)
	if err != nil {
		writeError(w, 500, err.Error())
		return
	}
	writeJSON(w, 200, session.Compact())
}

func (s *Server) handleGetSession(w http.ResponseWriter, r *http.Request) {
	sid := r.PathValue("session_id")
	session, err := s.sessions.Load(sid)
	if err != nil {
		writeError(w, 404, "Session not found")
		return
	}
	writeJSON(w, 200, map[string]any{"session": session})
}

func (s *Server) handleRenameSession(w http.ResponseWriter, r *http.Request) {
	sid := r.PathValue("session_id")
	var req struct {
		Title string `json:"title"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	session, err := s.sessions.Rename(sid, req.Title)
	if err != nil {
		writeError(w, 404, "Session not found")
		return
	}
	writeJSON(w, 200, session.Compact())
}

func (s *Server) handleDeleteSession(w http.ResponseWriter, r *http.Request) {
	sid := r.PathValue("session_id")
	if !s.sessions.Delete(sid) {
		writeError(w, 404, "Session not found")
		return
	}
	writeJSON(w, 200, map[string]bool{"deleted": true})
}

// ── Memory Handlers (stubs) ─────────────────────────────────────────────────

func (s *Server) handleListMemories(w http.ResponseWriter, r *http.Request) {
	// Memory not yet implemented in ErebusLite — return empty list
	writeJSON(w, 200, map[string]any{"memories": []any{}})
}

func (s *Server) handleDeleteMemory(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]bool{"deleted": true})
}

// ── Skills Handlers ─────────────────────────────────────────────────────────

func (s *Server) handleListSkills(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"skills": s.skills.List()})
}

func (s *Server) handleSkillCategories(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"categories": s.skills.Categories()})
}

func (s *Server) handleSkillsByCategory(w http.ResponseWriter, r *http.Request) {
	category := r.PathValue("category")
	writeJSON(w, 200, map[string]any{
		"category": category,
		"skills":   s.skills.ByCategory(category),
	})
}

func (s *Server) handleCreateSkill(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name        string `json:"name"`
		Description string `json:"description"`
		Content     string `json:"content"`
		Category    string `json:"category"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	path, err := skills.SaveUserSkill(s.cfg.DataDir, req.Name, req.Description, req.Content, req.Category)
	if err != nil {
		writeError(w, 500, err.Error())
		return
	}
	writeJSON(w, 200, map[string]any{"saved": true, "path": path})
}

// ── MCP Handlers ────────────────────────────────────────────────────────────

func (s *Server) handleListMCPServers(w http.ResponseWriter, r *http.Request) {
	var servers []map[string]any
	for _, srv := range s.cfg.MCP.Servers {
		servers = append(servers, map[string]any{
			"name":      srv.Name,
			"transport": srv.Transport,
			"command":   srv.Command,
			"url":       srv.URL,
			"enabled":   srv.IsEnabled(),
		})
	}
	if servers == nil {
		servers = []map[string]any{}
	}
	writeJSON(w, 200, map[string]any{"servers": servers})
}

// ── Config Handler ──────────────────────────────────────────────────────────

func (s *Server) handleGetConfig(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{
		"config": map[string]any{
			"agent": map[string]any{
				"name":            s.cfg.Agent.Name,
				"default_model":   s.cfg.DefaultModel,
				"reasoning_model": s.cfg.ReasoningModel,
			},
		},
	})
}

// ── Schedule Handlers ───────────────────────────────────────────────────────

func (s *Server) handleListSchedules(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"schedules": s.scheduler.List()})
}

func (s *Server) handleCreateSchedule(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name                string         `json:"name"`
		Cron                string         `json:"cron"`
		Description         string         `json:"description"`
		Payload             map[string]any `json:"payload"`
		Timezone            string         `json:"timezone"`
		NotificationChannel *string        `json:"notification_channel"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	if req.Timezone == "" {
		req.Timezone = "UTC"
	}
	if req.Payload == nil {
		req.Payload = map[string]any{}
	}
	entry, err := s.scheduler.Create(req.Name, req.Cron, req.Description, req.Payload, req.Timezone, req.NotificationChannel)
	if err != nil {
		writeError(w, 400, err.Error())
		return
	}
	writeJSON(w, 200, entry)
}

func (s *Server) handleUpdateSchedule(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("schedule_id")
	var updates map[string]any
	if err := readJSON(r, &updates); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	entry, err := s.scheduler.Update(id, updates)
	if err != nil {
		writeError(w, 400, err.Error())
		return
	}
	if entry == nil {
		writeError(w, 404, "Schedule not found")
		return
	}
	writeJSON(w, 200, entry)
}

func (s *Server) handleDeleteSchedule(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("schedule_id")
	if !s.scheduler.Delete(id) {
		writeError(w, 404, "Schedule not found")
		return
	}
	writeJSON(w, 200, map[string]bool{"deleted": true})
}

// ── Soul Handlers ───────────────────────────────────────────────────────────

func (s *Server) handleGetSoul(w http.ResponseWriter, r *http.Request) {
	content := soul.Load(s.cfg.SoulFile, s.cfg.DataDir)
	writeJSON(w, 200, map[string]string{"content": content})
}

func (s *Server) handleUpdateSoul(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Content string `json:"content"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	path, err := soul.Save(req.Content, s.cfg.DataDir)
	if err != nil {
		writeError(w, 500, err.Error())
		return
	}
	writeJSON(w, 200, map[string]any{"saved": true, "path": path})
}

// ── Context Handler ─────────────────────────────────────────────────────────

func (s *Server) handleGetContext(w http.ResponseWriter, r *http.Request) {
	// Load AGENTS.md / CLAUDE.md from data dir and CWD
	content := loadContextFiles(s.cfg.DataDir)
	writeJSON(w, 200, map[string]string{"content": content})
}

// loadContextFiles loads AGENTS.md or CLAUDE.md from the data dir and CWD.
func loadContextFiles(dataDir string) string {
	var parts []string

	for _, name := range []string{"AGENTS.md", "CLAUDE.md"} {
		path := dataDir + "/" + name
		if data, err := os.ReadFile(path); err == nil {
			parts = append(parts, string(data))
			break
		}
	}

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

// ── Channels Handler ────────────────────────────────────────────────────────

func (s *Server) handleListChannels(w http.ResponseWriter, r *http.Request) {
	channels := []map[string]any{
		{"name": "Web UI", "configured": true, "status": "active"},
	}
	writeJSON(w, 200, map[string]any{"channels": channels})
}

// ── Settings Handlers ───────────────────────────────────────────────────────

func (s *Server) handleGetSettings(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{
		"default_model":    s.cfg.DefaultModel,
		"reasoning_model":  nilIfEmpty(s.cfg.ReasoningModel),
		"skills_dir":       nilIfEmpty(s.cfg.SkillsDir),
		"api_host":         s.cfg.APIHost,
		"api_port":         s.cfg.APIPort,
	})
}

func (s *Server) handleUpdateSettings(w http.ResponseWriter, r *http.Request) {
	var req struct {
		DefaultModel   *string `json:"default_model"`
		ReasoningModel *string `json:"reasoning_model"`
		SkillsDir      *string `json:"skills_dir"`
	}
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	if req.DefaultModel != nil {
		s.cfg.DefaultModel = *req.DefaultModel
	}
	if req.ReasoningModel != nil {
		s.cfg.ReasoningModel = *req.ReasoningModel
	}
	if req.SkillsDir != nil {
		s.cfg.SkillsDir = *req.SkillsDir
	}
	writeJSON(w, 200, map[string]bool{"updated": true})
}

// ── Notification Handlers ───────────────────────────────────────────────────

func (s *Server) handleListNotificationChannels(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"channels": s.notifs.List()})
}

func (s *Server) handleCreateNotificationChannel(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name      string `json:"name"`
		URL       string `json:"url"`
		Enabled   bool   `json:"enabled"`
		IsDefault bool   `json:"is_default"`
	}
	req.Enabled = true
	if err := readJSON(r, &req); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	ch, err := s.notifs.Create(req.Name, req.URL, req.Enabled, req.IsDefault)
	if err != nil {
		writeError(w, 500, err.Error())
		return
	}
	writeJSON(w, 200, ch)
}

func (s *Server) handleUpdateNotificationChannel(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("channel_id")
	var updates map[string]any
	if err := readJSON(r, &updates); err != nil {
		writeError(w, 400, "invalid request body")
		return
	}
	ch, err := s.notifs.Update(id, updates)
	if err != nil {
		writeError(w, 500, err.Error())
		return
	}
	if ch == nil {
		writeError(w, 404, "Channel not found")
		return
	}
	writeJSON(w, 200, ch)
}

func (s *Server) handleDeleteNotificationChannel(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("channel_id")
	if !s.notifs.Delete(id) {
		writeError(w, 404, "Channel not found")
		return
	}
	writeJSON(w, 200, map[string]bool{"deleted": true})
}

func (s *Server) handleTestNotification(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Message   string  `json:"message"`
		Title     string  `json:"title"`
		ChannelID *string `json:"channel_id"`
	}
	req.Message = "Test notification from ErebusLite"
	req.Title = "ErebusLite Test"
	if err := readJSON(r, &req); err != nil {
		log.Printf("notification test read error: %v", err)
	}
	result := s.notifs.Send(req.Message, req.Title, req.ChannelID)
	sent, _ := result["sent"].(bool)
	if !sent {
		writeError(w, 400, "Send failed")
		return
	}
	writeJSON(w, 200, result)
}

// ── Health Handler ──────────────────────────────────────────────────────────

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{
		"status":           "ok",
		"version":          "0.1.0",
		"runtime":          "go/eino",
		"gateway":          true,
		"agent_configured": s.cfg.IsAgentConfigured(),
	})
}

func nilIfEmpty(s string) any {
	if s == "" {
		return nil
	}
	return s
}

// sessionMessagesToHistory converts a session's messages to the history format
// expected by the agent (slice of role/content maps).
func sessionMessagesToHistory(msgs []sessions.Message) []map[string]string {
	if len(msgs) == 0 {
		return nil
	}
	history := make([]map[string]string, 0, len(msgs))
	for _, m := range msgs {
		history = append(history, map[string]string{
			"role":    m.Role,
			"content": m.Content,
		})
	}
	return history
}
