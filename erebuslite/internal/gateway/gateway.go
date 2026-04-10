// Package gateway provides the unified ErebusLite server that combines the
// REST API with static file serving for the web UI.
package gateway

import (
	"context"
	"fmt"
	"log"
	"mime"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/nitzzzu/Erebus/erebuslite/internal/agent"
	"github.com/nitzzzu/Erebus/erebuslite/internal/api"
	"github.com/nitzzzu/Erebus/erebuslite/internal/config"
	mcpkg "github.com/nitzzzu/Erebus/erebuslite/internal/mcp"
	"github.com/nitzzzu/Erebus/erebuslite/internal/sessions"
	"github.com/nitzzzu/Erebus/erebuslite/internal/skills"
)

const version = "0.1.0"

// Gateway is the unified HTTP server for ErebusLite.
type Gateway struct {
	cfg         *config.Config
	apiSrv      *api.Server
	webRoot     string
	mcpCleanups []func()
}

// New creates a new Gateway.
func New(cfg *config.Config) (*Gateway, error) {
	// Initialize session store
	sessStore := sessions.NewStore(cfg.DataDir)

	// Initialize skills registry
	registry := skills.NewRegistry()
	skillDirs := collectSkillDirs(cfg)
	registry.LoadFromDirs(skillDirs...)
	log.Printf("Skills loaded: %d from %d directories", len(registry.List()), len(skillDirs))

	// Initialize agent
	ag := agent.New(cfg, registry)

	// Connect MCP servers
	var mcpCleanups []func()
	if len(cfg.MCP.Servers) > 0 {
		ctx := context.Background()
		mcpTools, cleanups := mcpkg.ConnectAll(ctx, cfg.MCP.Servers)
		if len(mcpTools) > 0 {
			ag.SetMCPTools(mcpTools)
			log.Printf("MCP tools loaded: %d", len(mcpTools))
		}
		mcpCleanups = cleanups
	}

	// Create API server
	apiSrv := api.New(cfg, sessStore, registry, ag)

	// Determine web UI root (relative to binary, or standard paths)
	webRoot := findWebRoot()

	return &Gateway{
		cfg:         cfg,
		apiSrv:      apiSrv,
		webRoot:     webRoot,
		mcpCleanups: mcpCleanups,
	}, nil
}

// Run starts the HTTP server and blocks until ctx is cancelled.
func (g *Gateway) Run(ctx context.Context, addr string) error {
	// Cleanup MCP connections when done
	defer func() {
		for _, cleanup := range g.mcpCleanups {
			cleanup()
		}
	}()

	mux := http.NewServeMux()

	// Mount all API routes under /api/
	mux.Handle("/api/", g.apiSrv.Handler())

	// Serve web UI or onboarding
	if g.webRoot != "" {
		mux.HandleFunc("/", g.serveWebUI)
	} else {
		mux.HandleFunc("/", g.serveOnboarding)
	}

	srv := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 30 * time.Second,
	}

	// Graceful shutdown
	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = srv.Shutdown(shutdownCtx)
	}()

	if g.webRoot != "" {
		log.Printf("Serving web UI from: %s", g.webRoot)
	}
	return srv.ListenAndServe()
}

func (g *Gateway) serveWebUI(w http.ResponseWriter, r *http.Request) {
	// CORS for web UI requests
	w.Header().Set("Access-Control-Allow-Origin", "*")

	path := r.URL.Path
	if path == "/" {
		path = "/index.html"
	}

	// Security: prevent directory traversal
	cleanPath := filepath.Clean(path)
	if strings.Contains(cleanPath, "..") {
		http.Error(w, "forbidden", http.StatusForbidden)
		return
	}

	fullPath := filepath.Join(g.webRoot, cleanPath)

	// Try exact file
	if info, err := os.Stat(fullPath); err == nil && !info.IsDir() {
		serveFile(w, r, fullPath)
		return
	}

	// Try path.html (Next.js static export pattern)
	htmlPath := strings.TrimSuffix(fullPath, "/") + ".html"
	if info, err := os.Stat(htmlPath); err == nil && !info.IsDir() {
		serveFile(w, r, htmlPath)
		return
	}

	// Try path/index.html
	indexPath := filepath.Join(strings.TrimSuffix(fullPath, "/"), "index.html")
	if info, err := os.Stat(indexPath); err == nil && !info.IsDir() {
		serveFile(w, r, indexPath)
		return
	}

	// SPA fallback: serve root index.html
	rootIndex := filepath.Join(g.webRoot, "index.html")
	if _, err := os.Stat(rootIndex); err == nil {
		serveFile(w, r, rootIndex)
		return
	}

	http.NotFound(w, r)
}

func (g *Gateway) serveOnboarding(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	if !g.cfg.IsAgentConfigured() {
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprintf(w, onboardingHTML, version)
		return
	}

	w.Header().Set("Content-Type", "text/html")
	fmt.Fprint(w, `<html><body style="background:#0a0a0a;color:#e5e5e5;font-family:sans-serif;
display:flex;align-items:center;justify-content:center;min-height:100vh">
<div style="text-align:center">
<h1>🌑 ErebusLite</h1>
<p>Web UI not built. Run <code>cd web && npm run build</code>
or use the API at <a href="/api/health" style="color:#818cf8">/api/health</a>
</p></div></body></html>`)
}

func serveFile(w http.ResponseWriter, r *http.Request, path string) {
	ext := filepath.Ext(path)
	if ct := mime.TypeByExtension(ext); ct != "" {
		w.Header().Set("Content-Type", ct)
	}
	http.ServeFile(w, r, path)
}

func findWebRoot() string {
	// Check standard locations for the pre-built web UI
	candidates := []string{
		"../web/out",                         // relative to erebuslite binary
		"web/out",                            // from project root
		"/app/web/out",                       // Docker
		filepath.Join("..", "web", "out"),     // dev
	}

	// Also check relative to executable
	if exe, err := os.Executable(); err == nil {
		dir := filepath.Dir(exe)
		candidates = append(candidates,
			filepath.Join(dir, "..", "web", "out"),
			filepath.Join(dir, "web", "out"),
		)
	}

	for _, c := range candidates {
		abs, err := filepath.Abs(c)
		if err != nil {
			continue
		}
		indexPath := filepath.Join(abs, "index.html")
		if _, err := os.Stat(indexPath); err == nil {
			log.Printf("Web UI found at: %s", abs)
			return abs
		}
	}

	log.Printf("Web UI not found — will show onboarding page")
	return ""
}

func collectSkillDirs(cfg *config.Config) []string {
	var dirs []string

	// Built-in skills (from the parent Erebus project)
	builtinDir := filepath.Join("..", "erebus", "skills", "builtins")
	if abs, err := filepath.Abs(builtinDir); err == nil {
		if _, err := os.Stat(abs); err == nil {
			dirs = append(dirs, abs)
		}
	}

	// Also check relative to executable
	if exe, err := os.Executable(); err == nil {
		exeBuiltin := filepath.Join(filepath.Dir(exe), "..", "erebus", "skills", "builtins")
		if abs, err := filepath.Abs(exeBuiltin); err == nil {
			if _, err := os.Stat(abs); err == nil {
				dirs = append(dirs, abs)
			}
		}
	}

	// User-configured directory
	if cfg.SkillsDir != "" {
		if _, err := os.Stat(cfg.SkillsDir); err == nil {
			dirs = append(dirs, cfg.SkillsDir)
		}
	}

	// ~/.erebus/skills/
	userSkills := filepath.Join(cfg.DataDir, "skills")
	if _, err := os.Stat(userSkills); err == nil {
		dirs = append(dirs, userSkills)
	}

	// ~/.erebus/user-skills/
	agentSkills := filepath.Join(cfg.DataDir, "user-skills")
	if _, err := os.Stat(agentSkills); err == nil {
		dirs = append(dirs, agentSkills)
	}

	// Extra dirs from config
	for _, d := range cfg.Skills.ExtraDirs {
		expanded := os.ExpandEnv(d)
		if strings.HasPrefix(expanded, "~") {
			home, _ := os.UserHomeDir()
			expanded = filepath.Join(home, expanded[1:])
		}
		if _, err := os.Stat(expanded); err == nil {
			dirs = append(dirs, expanded)
		}
	}

	return dirs
}

const onboardingHTML = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ErebusLite — Setup</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0a0a0a; color: #e5e5e5;
      display: flex; align-items: center; justify-content: center;
      min-height: 100vh; padding: 2rem;
    }
    .card {
      background: #171717; border: 1px solid #262626; border-radius: 12px;
      padding: 2.5rem; max-width: 540px; width: 100%%;
    }
    h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
    .subtitle { color: #a3a3a3; margin-bottom: 1.5rem; }
    .step { margin-bottom: 1rem; padding: 1rem; background: #1a1a2e;
            border-radius: 8px; border-left: 3px solid #6366f1; }
    .step h3 { font-size: 0.95rem; color: #818cf8; margin-bottom: 0.25rem; }
    .step p { font-size: 0.875rem; color: #a3a3a3; }
    code { background: #262626; padding: 0.15rem 0.4rem; border-radius: 4px;
           font-size: 0.85rem; color: #c4b5fd; }
    .footer { margin-top: 1.5rem; text-align: center; color: #525252;
              font-size: 0.8rem; }
    a { color: #818cf8; text-decoration: none; }
    .badge { display: inline-block; padding: 0.2rem 0.6rem; background: #1e293b;
             border-radius: 4px; font-size: 0.75rem; color: #38bdf8; margin-left: 0.5rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🌑 Welcome to ErebusLite <span class="badge">Go / Eino</span></h1>
    <p class="subtitle">Lightweight AI agent — almost ready. Complete the setup below.</p>

    <div class="step">
      <h3>1. Set your API key</h3>
      <p>Export an LLM provider key, e.g.<br>
        <code>export EREBUS_OPENAI_API_KEY=sk-...</code>
      </p>
    </div>

    <div class="step">
      <h3>2. (Optional) Configure MCP servers</h3>
      <p>Add to <code>erebus.toml</code>:<br>
        <code>[[mcp.servers]]</code></p>
    </div>

    <div class="step">
      <h3>3. (Optional) Customise your agent</h3>
      <p>Edit <code>~/.erebus/SOUL.md</code> for personality,<br>
         or add skills to <code>~/.erebus/skills/</code>.</p>
    </div>

    <div class="step">
      <h3>4. Restart ErebusLite</h3>
      <p>Run the binary again or restart the container.</p>
    </div>

    <div class="footer">
      <p>ErebusLite v%s · <a href="https://github.com/nitzzzu/Erebus">GitHub</a></p>
    </div>
  </div>
</body>
</html>`
