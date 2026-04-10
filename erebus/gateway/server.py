"""Unified Erebus Gateway — API + channels + web UI in a single process.

The gateway is the single entry point for Erebus:
- REST API endpoints under ``/api/``
- Telegram webhook under ``/telegram/`` (if configured)
- Teams messages under ``/api/messages`` (if configured)
- Web UI served as static files at ``/`` (if built)
- Onboarding page if the agent is not set up yet

This replaces running separate processes for the API, Telegram, and Teams.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from erebus.config import ErebusSettings, get_settings
from erebus.gateway.channels.manager import ChannelManager

logger = logging.getLogger(__name__)

# Import version from package
try:
    from erebus import __version__ as _VERSION
except ImportError:
    _VERSION = "0.1.0"

# Path to the Next.js static export (built into web/out/)
_WEB_STATIC_DIR = Path(__file__).parent.parent.parent / "web" / "out"

# Minimal onboarding HTML template shown when the agent is not configured.
# Use .format(version=_VERSION) before returning.
_ONBOARDING_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Erebus — Setup</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0a0a0a; color: #e5e5e5;
      display: flex; align-items: center; justify-content: center;
      min-height: 100vh; padding: 2rem;
    }}
    .card {{
      background: #171717; border: 1px solid #262626; border-radius: 12px;
      padding: 2.5rem; max-width: 540px; width: 100%;
    }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
    .subtitle {{ color: #a3a3a3; margin-bottom: 1.5rem; }}
    .step {{ margin-bottom: 1rem; padding: 1rem; background: #1a1a2e;
            border-radius: 8px; border-left: 3px solid #6366f1; }}
    .step h3 {{ font-size: 0.95rem; color: #818cf8; margin-bottom: 0.25rem; }}
    .step p {{ font-size: 0.875rem; color: #a3a3a3; }}
    code {{ background: #262626; padding: 0.15rem 0.4rem; border-radius: 4px;
           font-size: 0.85rem; color: #c4b5fd; }}
    .footer {{ margin-top: 1.5rem; text-align: center; color: #525252;
              font-size: 0.8rem; }}
    a {{ color: #818cf8; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>🌑 Welcome to Erebus</h1>
    <p class="subtitle">Your AI agent is almost ready. Complete the setup below.</p>

    <div class="step">
      <h3>1. Set your API key</h3>
      <p>Export an LLM provider key, e.g.<br>
        <code>export EREBUS_OPENAI_API_KEY=sk-...</code>
      </p>
    </div>

    <div class="step">
      <h3>2. (Optional) Configure channels</h3>
      <p>Telegram: <code>export EREBUS_TELEGRAM_TOKEN=...</code><br>
         Teams: <code>export EREBUS_TEAMS_APP_ID=...</code></p>
    </div>

    <div class="step">
      <h3>3. (Optional) Customise your agent</h3>
      <p>Edit <code>~/.erebus/SOUL.md</code> for personality,<br>
         or add skills to <code>~/.erebus/skills/</code>.</p>
    </div>

    <div class="step">
      <h3>4. Restart the gateway</h3>
      <p>Run <code>erebus gateway</code> or restart the Docker container.</p>
    </div>

    <div class="footer">
      <p>Erebus v{version} · <a href="https://github.com/nitzzzu/Erebus">GitHub</a></p>
    </div>
  </div>
</body>
</html>
"""

# Pre-render the onboarding HTML with the current version
_ONBOARDING_HTML = _ONBOARDING_HTML_TEMPLATE.format(version=_VERSION)


def _is_agent_configured(settings: ErebusSettings) -> bool:
    """Check if the agent has at least a model provider key configured."""
    return any([
        settings.openai_api_key,
        settings.anthropic_api_key,
        settings.google_api_key,
        settings.openrouter_api_key,
    ])


def create_gateway_app(settings: Optional[ErebusSettings] = None) -> FastAPI:
    """Create the unified Erebus gateway FastAPI application.

    This single app serves:
    - The REST API (``/api/``)
    - Messaging channels (Telegram, Teams) if configured
    - The web UI as static files (if built)
    - An onboarding page if the agent is not yet configured
    """
    if settings is None:
        settings = get_settings()

    # Build the core API app (it already defines all /api/* routes)
    from erebus.api.server import create_api_app

    app = create_api_app(settings)

    # ── 1. Mount configured messaging channels ──────────────────────────────
    channel_manager = ChannelManager(settings)
    channel_manager.mount_all(app)

    # ── 2. Override select API endpoints with gateway-aware versions ────────
    # Remove original /api/channels and /api/health routes, then add
    # replacements that include channel-manager awareness.
    _override_paths = {"/api/channels", "/api/health"}
    app.routes[:] = [r for r in app.routes if getattr(r, "path", None) not in _override_paths]

    @app.get("/api/channels")
    async def list_channels_gateway():
        return {"channels": channel_manager.status_all()}

    @app.get("/api/health")
    async def gateway_health():
        return {
            "status": "ok",
            "version": _VERSION,
            "gateway": True,
            "agent_configured": _is_agent_configured(settings),
            "channels": channel_manager.status_all(),
        }

    # ── 3. Serve web UI or onboarding page ──────────────────────────────────
    has_web_ui = _WEB_STATIC_DIR.is_dir() and (_WEB_STATIC_DIR / "index.html").is_file()

    if has_web_ui:
        static_root = _WEB_STATIC_DIR.resolve()

        def _safe_resolve(subpath: str) -> Path | None:
            """Resolve a subpath within the static dir, returning None if it escapes."""
            # Reject obvious traversal attempts
            if ".." in subpath.split("/"):
                return None
            candidate = (static_root / subpath).resolve()
            if not str(candidate).startswith(str(static_root)):
                return None
            return candidate

        # Serve the Next.js static export with SPA fallback
        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            """Serve the Next.js static export with SPA fallback."""
            safe = _safe_resolve(full_path)
            if safe is None:
                return JSONResponse({"error": "forbidden"}, status_code=403)

            # Try exact file
            if safe.is_file():
                return None  # Let StaticFiles handle it

            # Try path.html (Next.js static export pattern)
            html_safe = _safe_resolve(f"{full_path.rstrip('/')}.html")
            if html_safe is not None and html_safe.is_file():
                return HTMLResponse(html_safe.read_text(encoding="utf-8"))

            # Try path/index.html
            index_safe = _safe_resolve(f"{full_path.rstrip('/')}/index.html")
            if index_safe is not None and index_safe.is_file():
                return HTMLResponse(index_safe.read_text(encoding="utf-8"))

            # SPA fallback: serve root index.html
            root_index = static_root / "index.html"
            if root_index.is_file():
                return HTMLResponse(root_index.read_text(encoding="utf-8"))
            return JSONResponse({"error": "not found"}, status_code=404)

        # Mount static files for assets (_next/*, images, etc.)
        app.mount("/", StaticFiles(directory=str(_WEB_STATIC_DIR), html=True), name="web-ui")
    else:
        # No web UI build available
        @app.get("/")
        async def root():
            if not _is_agent_configured(settings):
                return HTMLResponse(_ONBOARDING_HTML)
            return HTMLResponse(
                "<html><body style='background:#0a0a0a;color:#e5e5e5;font-family:sans-serif;"
                "display:flex;align-items:center;justify-content:center;min-height:100vh'>"
                "<div style='text-align:center'>"
                "<h1>🌑 Erebus</h1>"
                "<p>Web UI not built. Run <code>cd web && npm run build</code> "
                "or use the API at <a href='/api/health' style='color:#818cf8'>/api/health</a>"
                "</p></div></body></html>"
            )

    return app
