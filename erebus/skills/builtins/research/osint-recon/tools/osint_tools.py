"""OSINT reconnaissance tools for CodeAgent.

Public-API-based intelligence gathering — no API keys required for
basic functionality.  Uses crt.sh, ip-api.com, and DNS lookups.
"""

from __future__ import annotations

import json
import re
import socket
import subprocess
import urllib.error
import urllib.request
from typing import Any

_UA = "Mozilla/5.0 (compatible; Erebus-OSINT/1.0)"


def _get(url: str, timeout: int = 15) -> tuple[int, str]:
    """Simple HTTP GET."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, str(exc)


def osint_whois(domain: str) -> str:
    """WHOIS lookup for domain registration info.

    Parameters
    ----------
    domain:
        Domain name (e.g. ``"example.com"``).

    Returns
    -------
    str
        WHOIS data or error.
    """
    try:
        result = subprocess.run(
            ["whois", domain],
            capture_output=True, text=True, timeout=15,
        )
        return result.stdout.strip() or result.stderr.strip() or "(no output)"
    except FileNotFoundError:
        return "whois command not found — install whois package"
    except subprocess.TimeoutExpired:
        return "WHOIS lookup timed out"
    except Exception as exc:
        return f"WHOIS error: {exc}"


def osint_dns(domain: str, record_type: str = "A") -> str:
    """DNS record lookup.

    Parameters
    ----------
    domain:
        Domain name.
    record_type:
        Record type: A, AAAA, MX, NS, TXT, CNAME, SOA.

    Returns
    -------
    str
        DNS records.
    """
    try:
        result = subprocess.run(
            ["dig", "+short", domain, record_type.upper()],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.strip()
        return output or f"No {record_type} records for {domain}"
    except FileNotFoundError:
        # Fallback to Python socket for A records
        if record_type.upper() == "A":
            try:
                ips = socket.getaddrinfo(domain, None, socket.AF_INET)
                return "\n".join(set(ip[4][0] for ip in ips))
            except socket.gaierror:
                return f"Could not resolve {domain}"
        return "dig command not found — install dnsutils"
    except Exception as exc:
        return f"DNS error: {exc}"


def osint_headers(url: str) -> dict[str, str]:
    """HTTP headers analysis for technology fingerprinting.

    Parameters
    ----------
    url:
        Target URL.

    Returns
    -------
    dict
        Response headers.
    """
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return dict(resp.headers)
    except Exception as exc:
        return {"error": str(exc)}


def osint_email_validate(email: str) -> dict[str, Any]:
    """Basic email format + MX record validation.

    Parameters
    ----------
    email:
        Email address to validate.

    Returns
    -------
    dict
        Validation results.
    """
    result: dict[str, Any] = {"email": email, "valid_format": False, "has_mx": False}
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        result["valid_format"] = True
        domain = email.split("@")[1]
        mx = osint_dns(domain, "MX")
        result["has_mx"] = bool(mx) and "No MX" not in mx
        result["mx_records"] = mx
    return result


def osint_subdomain_enum(domain: str) -> list[str]:
    """Subdomain enumeration via crt.sh (Certificate Transparency).

    Parameters
    ----------
    domain:
        Target domain.

    Returns
    -------
    list[str]
        Discovered subdomains.
    """
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    status, body = _get(url, timeout=20)
    if status == 200:
        try:
            entries = json.loads(body)
            names = set()
            for entry in entries:
                name = entry.get("name_value", "")
                for n in name.split("\n"):
                    n = n.strip().lower()
                    if n and n.endswith(domain):
                        names.add(n)
            return sorted(names)
        except json.JSONDecodeError:
            return [f"Parse error: {body[:200]}"]
    return [f"crt.sh error ({status}): {body[:200]}"]


def osint_ip_info(ip: str) -> dict[str, Any]:
    """IP geolocation and ASN info via ip-api.com.

    Parameters
    ----------
    ip:
        IPv4 or IPv6 address.

    Returns
    -------
    dict
        Location and network info.
    """
    status, body = _get(f"http://ip-api.com/json/{ip}")
    if status == 200:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"error": body[:500]}
    return {"error": f"ip-api ({status}): {body[:500]}"}


def osint_social_check(username: str) -> dict[str, str]:
    """Check username availability across platforms.

    Uses HTTP status codes to guess if a profile exists.

    Parameters
    ----------
    username:
        Username to check.

    Returns
    -------
    dict
        Platform → status mapping.
    """
    platforms = {
        "GitHub": f"https://github.com/{username}",
        "Twitter/X": f"https://x.com/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "Instagram": f"https://www.instagram.com/{username}/",
        "LinkedIn": f"https://www.linkedin.com/in/{username}/",
    }
    results = {}
    for name, url in platforms.items():
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": _UA})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                results[name] = "exists" if resp.status == 200 else f"status:{resp.status}"
        except urllib.error.HTTPError as exc:
            results[name] = "not found" if exc.code == 404 else f"error:{exc.code}"
        except Exception:
            results[name] = "error"
    return results


def osint_dorking(query: str, site: str | None = None) -> str:
    """Build a Google dork query string.

    Parameters
    ----------
    query:
        Search terms.
    site:
        Optional site restriction.

    Returns
    -------
    str
        Google dork URL ready to open.
    """
    import urllib.parse
    dork = query
    if site:
        dork = f"site:{site} {query}"
    encoded = urllib.parse.quote(dork)
    return f"https://www.google.com/search?q={encoded}"


# -- TOOLS dict: required export for CodeAgent skill tool loading --
TOOLS: dict[str, Any] = {
    "osint_whois": osint_whois,
    "osint_dns": osint_dns,
    "osint_headers": osint_headers,
    "osint_email_validate": osint_email_validate,
    "osint_subdomain_enum": osint_subdomain_enum,
    "osint_ip_info": osint_ip_info,
    "osint_social_check": osint_social_check,
    "osint_dorking": osint_dorking,
}
