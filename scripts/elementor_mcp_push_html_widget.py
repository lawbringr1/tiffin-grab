#!/usr/bin/env python3
"""
Push raw HTML into an Elementor HTML widget via the site’s elementor-mcp server.

Equivalent to tmp-mcp-push-html-widget.ps1 — use this on macOS/Linux (no PowerShell).

Requires: Python 3.8+, .cursor/mcp.json with mcpServers.elementor-mcp url + Authorization.

Example:
  ./scripts/elementor_mcp_push_html_widget.py \\
    --post-id 10297 --element-id 24caf9c \\
    --html elementor-html/tiffin-plans-listing-editorial-2026.html
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def load_elementor_mcp_config(mcp_path: Path) -> tuple[str, str]:
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    ec = data.get("mcpServers", {}).get("elementor-mcp")
    if not ec:
        sys.exit(f"No mcpServers.elementor-mcp in {mcp_path}")
    auth = (ec.get("headers") or {}).get("Authorization")
    url = ec.get("url")
    if not auth or not url:
        sys.exit(f"elementor-mcp missing url or headers.Authorization in {mcp_path}")
    return str(url).rstrip("/"), auth


def mcp_post(
    url: str,
    auth: str,
    body: dict,
    *,
    session_id: str | None = None,
    timeout: int = 120,
) -> tuple[dict[str, str], str]:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", auth)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"MCP HTTP {e.code}: {err_body[:2000]}")
    except urllib.error.URLError as e:
        sys.exit(f"MCP request failed: {e}")
    return headers, raw


def session_id_from_headers(headers: dict[str, str]) -> str | None:
    for key, val in headers.items():
        if key.lower() == "mcp-session-id":
            return val.strip()
    return None


def mcp_initialize(base_url: str, auth: str) -> str:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "tiffin-grab-cli", "version": "1"},
        },
    }
    headers, _ = mcp_post(base_url, auth, body, session_id=None, timeout=30)
    sid = session_id_from_headers(headers)
    if not sid:
        sys.exit("MCP initialize did not return Mcp-Session-Id header.")
    return sid


def mcp_update_widget_html(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    post_id: int,
    element_id: str,
    html: str,
) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 41,
        "method": "tools/call",
        "params": {
            "name": "elementor-mcp-update-widget",
            "arguments": {
                "post_id": post_id,
                "element_id": element_id,
                "settings": {"html": html},
            },
        },
    }
    _headers, raw = mcp_post(base_url, auth, body, session_id=session_id)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(f"Non-JSON MCP response: {raw[:2000]}")


def main() -> None:
    root = repo_root_from_script()
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Push HTML to Elementor widget via elementor-mcp.")
    p.add_argument("--post-id", type=int, required=True)
    p.add_argument("--element-id", required=True)
    p.add_argument(
        "--html",
        required=True,
        help="Path to HTML file (relative to repo root or absolute).",
    )
    p.add_argument(
        "--mcp-json",
        type=Path,
        default=default_mcp,
        help=f"Path to Cursor MCP config (default: {default_mcp})",
    )
    args = p.parse_args()

    mcp_path = args.mcp_json.expanduser().resolve()
    if not mcp_path.is_file():
        sys.exit(f"MCP config not found: {mcp_path}")

    html_path = Path(args.html).expanduser()
    if not html_path.is_absolute():
        html_path = (root / html_path).resolve()
    if not html_path.is_file():
        sys.exit(f"HTML file not found: {html_path}")

    base_url, auth = load_elementor_mcp_config(mcp_path)
    html = html_path.read_text(encoding="utf-8")

    print(f"POSTing {html_path.relative_to(root)} -> post {args.post_id} element {args.element_id} ...")
    session_id = mcp_initialize(base_url, auth)
    out = mcp_update_widget_html(
        base_url,
        auth,
        session_id,
        post_id=args.post_id,
        element_id=args.element_id,
        html=html,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))

    err = out.get("error")
    if err:
        sys.exit(1)
    # tools/call wraps result; treat missing success as failure if structuredContent says otherwise
    result = out.get("result") or {}
    structured = result.get("structuredContent") or {}
    if structured.get("success") is False:
        sys.exit(1)


if __name__ == "__main__":
    main()
