---
name: osint-recon
description: OSINT reconnaissance tools for the CodeAgent — domain, IP, email, and social media intelligence
---

# OSINT Recon — CodeAgent Tools

## Overview

This skill extends the CodeAgent with Open Source Intelligence (OSINT) functions.
Uses public APIs and the Agentic Fetch service for web-based lookups.
No API keys required for basic functionality.

Inspired by [awesome-osint](https://github.com/jivoi/awesome-osint).

## CodeAgent Functions

- `osint_whois(domain)` — WHOIS lookup for domain registration info
- `osint_dns(domain, record_type="A")` — DNS record lookup
- `osint_headers(url)` — HTTP headers analysis for technology fingerprinting
- `osint_email_validate(email)` — basic email format + MX validation
- `osint_subdomain_enum(domain)` — subdomain enumeration via crt.sh
- `osint_ip_info(ip)` — IP geolocation and ASN info
- `osint_social_check(username)` — check username across platforms
- `osint_dorking(query, site=None)` — Google dorking helper

## Example

```python
# Full recon on a domain
domain = "example.com"
print("=== WHOIS ===")
print(osint_whois(domain))
print("=== DNS ===")
print(osint_dns(domain, "A"))
print(osint_dns(domain, "MX"))
print("=== Subdomains ===")
print(osint_subdomain_enum(domain))
```
