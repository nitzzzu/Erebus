"""Erebus authentication middleware.

Supports two auth providers:
- ``github``   — OAuth 2.0 login via GitHub (session cookie after redirect)
- ``authelia`` — Forward-auth proxy: trusts ``Remote-User`` / ``Remote-Name`` headers
                 set by Authelia after it has authenticated the request upstream.

Set these environment variables to enable authentication:

    EREBUS_AUTH_ENABLED=true
    EREBUS_AUTH_PROVIDER=github          # or "authelia"

    # GitHub only
    EREBUS_GITHUB_CLIENT_ID=<your-app-client-id>
    EREBUS_GITHUB_CLIENT_SECRET=<your-app-client-secret>
    EREBUS_GITHUB_ALLOWED_LOGINS=user1,user2   # optional allowlist (comma-separated)

    # Session signing (required when auth is enabled)
    EREBUS_SECRET_KEY=<random-32-byte-hex>      # generate: openssl rand -hex 32

    # Authelia only
    EREBUS_AUTHELIA_HEADER_USER=Remote-User     # header carrying the username (default)
    EREBUS_AUTHELIA_HEADER_NAME=Remote-Name     # header carrying display name (default)

Unauthenticated requests to protected paths are redirected to /auth/login (GitHub)
or rejected with 401 (Authelia — let the proxy handle the redirect).

Paths that never require auth: /api/health, /auth/*, all static assets.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import logging
import os
import time
from typing import Awaitable, Callable
from urllib.parse import urlencode

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

_ALWAYS_PUBLIC = frozenset({"/api/health", "/auth/login", "/auth/callback", "/auth/logout"})
_PUBLIC_PREFIXES = ("/auth/",)

_COOKIE_NAME = "erebus_session"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _is_public_path(path: str) -> bool:
    """Return True for paths that do not require authentication."""
    if path in _ALWAYS_PUBLIC:
        return True
    for prefix in _PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    # Static assets (Next.js build artefacts, favicons, etc.)
    for ext in (".js", ".css", ".png", ".ico", ".svg", ".woff", ".woff2", ".txt", ".json"):
        if path.endswith(ext):
            return True
    return False


def _sign(secret: bytes, payload: str) -> str:
    """Return HMAC-SHA256 hex signature for *payload*."""
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def _make_session_cookie(secret: bytes, user: dict) -> str:
    """Encode a signed session value containing the user dict."""
    data = json.dumps(user, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(data.encode()).decode()
    sig = _sign(secret, encoded)
    return f"{encoded}.{sig}"


def _decode_session_cookie(secret: bytes, value: str) -> dict | None:
    """Decode and verify a session cookie.  Returns None on failure."""
    try:
        encoded, sig = value.rsplit(".", 1)
        expected = _sign(secret, encoded)
        if not hmac.compare_digest(sig, expected):
            return None
        data = base64.urlsafe_b64decode(encoded.encode()).decode()
        return json.loads(data)
    except Exception:
        return None


# ── GitHub OAuth helpers ─────────────────────────────────────────────────────

_GH_AUTH_URL = "https://github.com/login/oauth/authorize"
_GH_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GH_USER_URL = "https://api.github.com/user"


async def _github_exchange_code(client_id: str, client_secret: str, code: str) -> str | None:
    """Exchange an OAuth *code* for a GitHub access token."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            _GH_TOKEN_URL,
            data={"client_id": client_id, "client_secret": client_secret, "code": code},
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json().get("access_token")


async def _github_get_user(token: str) -> dict | None:
    """Fetch the GitHub user object for *token*."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            _GH_USER_URL,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()


# ── Middleware ───────────────────────────────────────────────────────────────


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for Erebus.

    Checks every incoming request and either passes it through (public path
    or already authenticated) or redirects / rejects.
    """

    def __init__(
        self,
        app,
        *,
        provider: str,
        secret_key: bytes,
        github_client_id: str = "",
        github_client_secret: str = "",
        github_allowed_logins: list[str] | None = None,
        authelia_header_user: str = "Remote-User",
        authelia_header_name: str = "Remote-Name",
    ) -> None:
        super().__init__(app)
        self.provider = provider.lower()
        self.secret_key = secret_key
        self.github_client_id = github_client_id
        self.github_client_secret = github_client_secret
        self.github_allowed_logins: set[str] = set(github_allowed_logins or [])
        self.authelia_header_user = authelia_header_user.lower()
        self.authelia_header_name = authelia_header_name.lower()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # ── Always-public paths ──────────────────────────────────────────────
        if _is_public_path(path):
            return await call_next(request)

        # ── Provider-specific auth ───────────────────────────────────────────
        if self.provider == "authelia":
            return await self._handle_authelia(request, call_next)
        else:
            return await self._handle_github(request, call_next)

    # ── Authelia ─────────────────────────────────────────────────────────────

    async def _handle_authelia(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Trust headers set by the Authelia forward-auth proxy."""
        username = request.headers.get(self.authelia_header_user, "").strip()
        if not username:
            return JSONResponse(
                {"error": "Unauthorized — Authelia authentication required"},
                status_code=401,
            )
        # Inject user info into request state for downstream handlers
        request.state.user = {
            "login": username,
            "name": request.headers.get(self.authelia_header_name, username).strip(),
            "provider": "authelia",
        }
        return await call_next(request)

    # ── GitHub OAuth ─────────────────────────────────────────────────────────

    async def _handle_github(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Validate GitHub session cookie or trigger OAuth flow."""
        cookie_value = request.cookies.get(_COOKIE_NAME, "")
        user = _decode_session_cookie(self.secret_key, cookie_value) if cookie_value else None

        if user:
            # Validate allowlist (if configured)
            if self.github_allowed_logins and user.get("login") not in self.github_allowed_logins:
                return HTMLResponse(
                    "<h1>403 Forbidden</h1><p>Your account is not allowed.</p>", 403
                )
            request.state.user = user
            return await call_next(request)

        # Not authenticated — redirect to GitHub login
        redirect_uri = str(request.base_url).rstrip("/") + "/auth/callback"
        params = urlencode({
            "client_id": self.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user",
        })
        return RedirectResponse(f"{_GH_AUTH_URL}?{params}", status_code=302)


# ── OAuth callback & logout routes ───────────────────────────────────────────

def create_auth_router(
    *,
    provider: str,
    secret_key: bytes,
    github_client_id: str = "",
    github_client_secret: str = "",
    github_allowed_logins: list[str] | None = None,
    authelia_header_user: str = "Remote-User",
    authelia_header_name: str = "Remote-Name",
):
    """Return a FastAPI router with /auth/login, /auth/callback, /auth/logout."""
    from fastapi import APIRouter
    from fastapi.responses import HTMLResponse, RedirectResponse

    router = APIRouter(prefix="/auth", tags=["auth"])
    allowed: set[str] = set(github_allowed_logins or [])

    @router.get("/login")
    async def login(request: Request):
        if provider != "github":
            return HTMLResponse("<p>Authentication is handled upstream.</p>")
        redirect_uri = str(request.base_url).rstrip("/") + "/auth/callback"
        params = urlencode({
            "client_id": github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user",
        })
        return RedirectResponse(f"{_GH_AUTH_URL}?{params}", status_code=302)

    @router.get("/callback")
    async def callback(request: Request, code: str | None = None, error: str | None = None):
        if provider != "github":
            return HTMLResponse("<p>Authentication is handled upstream.</p>")

        if error or not code:
            return HTMLResponse(
                f"<h1>Authentication error</h1><pre>{html.escape(error or 'No code')}</pre>",
                400,
            )

        token = await _github_exchange_code(github_client_id, github_client_secret, code)
        if not token:
            return HTMLResponse(
                "<h1>Authentication failed</h1><p>Could not get access token.</p>", 401
            )

        gh_user = await _github_get_user(token)
        if not gh_user:
            return HTMLResponse("<h1>Authentication failed</h1><p>Could not fetch user.</p>", 401)

        login = gh_user.get("login", "")
        if allowed and login not in allowed:
            return HTMLResponse(
                f"<h1>403 Forbidden</h1><p>GitHub account <b>{login}</b> is not allowed.</p>",
                403,
            )

        user = {
            "login": login,
            "name": gh_user.get("name") or login,
            "avatar_url": gh_user.get("avatar_url", ""),
            "provider": "github",
            "at": int(time.time()),
        }
        cookie_value = _make_session_cookie(secret_key, user)

        response = RedirectResponse("/", status_code=302)
        response.set_cookie(
            _COOKIE_NAME,
            cookie_value,
            max_age=_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
        return response

    @router.get("/logout")
    async def logout():
        response = RedirectResponse("/", status_code=302)
        response.delete_cookie(_COOKIE_NAME)
        return response

    @router.get("/me")
    async def me(request: Request):
        if provider == "authelia":
            # Header names are lowercased by Starlette
            username = request.headers.get(authelia_header_user.lower(), "").strip()
            if not username:
                return JSONResponse({"authenticated": False}, status_code=401)
            return JSONResponse({
                "authenticated": True,
                "user": {
                    "login": username,
                    "name": request.headers.get(authelia_header_name.lower(), username).strip(),
                    "provider": "authelia",
                },
            })
        # GitHub — decode cookie
        cookie_value = request.cookies.get(_COOKIE_NAME, "")
        user = _decode_session_cookie(secret_key, cookie_value) if cookie_value else None
        if not user:
            return JSONResponse({"authenticated": False}, status_code=401)
        return JSONResponse({"authenticated": True, "user": user})

    return router


# ── Factory ───────────────────────────────────────────────────────────────────


def build_auth_components(settings) -> tuple[dict | None, object | None]:
    """Return ``(middleware_kwargs, auth_router)`` if auth is enabled, else ``(None, None)``.

    The caller should add the middleware via::

        app.add_middleware(AuthMiddleware, **middleware_kwargs)
    """
    auth_enabled = os.environ.get("EREBUS_AUTH_ENABLED", "").lower() in ("1", "true", "yes")
    if not getattr(settings, "auth_enabled", auth_enabled):
        return None, None

    provider = getattr(settings, "auth_provider", os.environ.get("EREBUS_AUTH_PROVIDER", "github"))

    raw_secret = getattr(settings, "secret_key", os.environ.get("EREBUS_SECRET_KEY", ""))
    if not raw_secret:
        import secrets as _secrets
        raw_secret = _secrets.token_hex(32)
        logger.warning(
            "EREBUS_SECRET_KEY not set — generated ephemeral key "
            "(sessions won't survive restarts; set EREBUS_SECRET_KEY for production)"
        )
    secret_key = raw_secret.encode() if isinstance(raw_secret, str) else raw_secret

    gh_client_id = getattr(
        settings, "github_client_id", os.environ.get("EREBUS_GITHUB_CLIENT_ID", "")
    )
    gh_client_secret = getattr(
        settings, "github_client_secret", os.environ.get("EREBUS_GITHUB_CLIENT_SECRET", "")
    )
    raw_allowed = getattr(
        settings, "github_allowed_logins", os.environ.get("EREBUS_GITHUB_ALLOWED_LOGINS", "")
    )
    gh_allowed = [u.strip() for u in raw_allowed.split(",") if u.strip()] if raw_allowed else []

    authelia_header_user = getattr(
        settings,
        "authelia_header_user",
        os.environ.get("EREBUS_AUTHELIA_HEADER_USER", "Remote-User"),
    )
    authelia_header_name = getattr(
        settings,
        "authelia_header_name",
        os.environ.get("EREBUS_AUTHELIA_HEADER_NAME", "Remote-Name"),
    )

    middleware_kwargs = {
        "provider": provider,
        "secret_key": secret_key,
        "github_client_id": gh_client_id,
        "github_client_secret": gh_client_secret,
        "github_allowed_logins": gh_allowed,
        "authelia_header_user": authelia_header_user,
        "authelia_header_name": authelia_header_name,
    }

    router = create_auth_router(
        provider=provider,
        secret_key=secret_key,
        github_client_id=gh_client_id,
        github_client_secret=gh_client_secret,
        github_allowed_logins=gh_allowed,
        authelia_header_user=authelia_header_user,
        authelia_header_name=authelia_header_name,
    )

    return middleware_kwargs, router
