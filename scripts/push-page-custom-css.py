#!/usr/bin/env python3
"""Push a CSS file into an Elementor page's page-level Custom CSS via MCP.

Why: on this site LiteSpeed UCSS strips inline <style> from HTML widgets, but Elementor's
page Custom CSS (output as a managed stylesheet) survives — same path the navbar CSS uses.

Usage:
  SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/push-page-custom-css.py --post-id 13039 \
    --css-file elementor-html/healthy-meals-page-2026.css
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_mcp(mcp_path: Path) -> tuple[str, str]:
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    ec = data.get("mcpServers", {}).get("elementor-mcp")
    if not ec:
        sys.exit(f"No mcpServers.elementor-mcp in {mcp_path}")
    auth = (ec.get("headers") or {}).get("Authorization")
    url = ec.get("url")
    if not auth or not url:
        sys.exit("elementor-mcp missing url or headers.Authorization")
    return str(url).rstrip("/"), auth


def mcp_post(url: str, auth: str, body: dict, session_id: str | None, timeout: int = 120):
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", auth)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        raw = json.loads(resp.read().decode("utf-8"))
    return headers, raw


def mcp_initialize(base_url: str, auth: str) -> str:
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "tg-page-css", "version": "1"}},
    }
    headers, _ = mcp_post(base_url, auth, body, session_id=None, timeout=30)
    sid = headers.get("mcp-session-id")
    if not sid:
        sys.exit("MCP initialize did not return Mcp-Session-Id header.")
    return sid.strip()


def main() -> None:
    root = repo_root()
    p = argparse.ArgumentParser()
    p.add_argument("--post-id", type=int, required=True)
    p.add_argument("--css-file", type=Path, required=True)
    p.add_argument("--mcp-json", type=Path, default=root / ".cursor" / "mcp.json")
    p.add_argument("--append", action="store_true")
    args = p.parse_args()

    css_path = args.css_file.expanduser().resolve()
    if not css_path.is_file():
        sys.exit(f"CSS not found: {css_path}")
    css = css_path.read_text(encoding="utf-8")

    base_url, auth = load_mcp(args.mcp_json.expanduser().resolve())
    sid = mcp_initialize(base_url, auth)
    body = {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "elementor-mcp-add-custom-css",
                   "arguments": {"post_id": args.post_id, "css": css, "replace": not args.append}},
    }
    _h, raw = mcp_post(base_url, auth, body, session_id=sid)
    if raw.get("error"):
        sys.exit(f"MCP error: {raw['error']}")
    res = raw.get("result") or {}
    if res.get("isError"):
        sys.exit(f"Tool error: {res.get('content')}")
    print(f"Pushed {len(css)} bytes of custom CSS → post {args.post_id}: {res.get('structuredContent') or 'ok'}")


if __name__ == "__main__":
    main()
