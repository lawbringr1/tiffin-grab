#!/usr/bin/env python3
"""
Push Elementor widget settings via the site’s elementor-mcp server (HTML widget content or container custom_css).

Cross-platform Elementor MCP HTML/CSS pusher (replaces legacy PowerShell one-offs).

Requires: Python 3.8+, .cursor/mcp.json with mcpServers.elementor-mcp url + Authorization.

Examples:
  ./scripts/elementor_mcp_push_html_widget.py \\
    --post-id 10297 --element-id 24caf9c \\
    --html elementor-html/tiffin-plans-listing-editorial-2026.html

  ./scripts/elementor_mcp_push_html_widget.py \\
    --post-id 9825 --element-id a2cdc57 \\
    --custom-css elementor-html/home-2026-hero-button-row.css
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


def mcp_call_tool(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    tool_name: str,
    arguments: dict,
) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 41,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    _headers, raw = mcp_post(base_url, auth, body, session_id=session_id)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(f"Non-JSON MCP response: {raw[:2000]}")


def mcp_update_widget_settings(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    post_id: int,
    element_id: str,
    settings: dict,
) -> dict:
    return mcp_call_tool(
        base_url,
        auth,
        session_id,
        tool_name="elementor-mcp-update-widget",
        arguments={"post_id": post_id, "element_id": element_id, "settings": settings},
    )


def mcp_update_container_settings(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    post_id: int,
    element_id: str,
    settings: dict,
) -> dict:
    return mcp_call_tool(
        base_url,
        auth,
        session_id,
        tool_name="elementor-mcp-update-container",
        arguments={"post_id": post_id, "element_id": element_id, "settings": settings},
    )


def main() -> None:
    root = repo_root_from_script()
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Push Elementor widget settings via elementor-mcp.")
    p.add_argument("--post-id", type=int, required=True)
    p.add_argument("--element-id", required=True)
    p.add_argument(
        "--html",
        help="Path to HTML file (relative to repo root or absolute).",
    )
    p.add_argument(
        "--custom-css",
        metavar="PATH",
        help="Path to CSS file sent as Elementor custom_css (container button row, etc.).",
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

    if bool(args.html) == bool(args.custom_css):
        sys.exit("Provide exactly one of: --html PATH or --custom-css PATH")

    if args.html:
        file_path = Path(args.html).expanduser()
        label = "html"
        settings = {"html": None}
    else:
        file_path = Path(args.custom_css).expanduser()
        label = "custom_css"
        settings = {"custom_css": None}

    if not file_path.is_absolute():
        file_path = (root / file_path).resolve()
    if not file_path.is_file():
        sys.exit(f"File not found: {file_path}")

    base_url, auth = load_elementor_mcp_config(mcp_path)
    text = file_path.read_text(encoding="utf-8")
    if "html" in settings:
        settings["html"] = text
    else:
        settings["custom_css"] = text

    print(
        f"POSTing {file_path.relative_to(root)} ({label}) -> post {args.post_id} element {args.element_id} ..."
    )
    session_id = mcp_initialize(base_url, auth)
    if label == "custom_css":
        out = mcp_update_container_settings(
            base_url,
            auth,
            session_id,
            post_id=args.post_id,
            element_id=args.element_id,
            settings=settings,
        )
    else:
        out = mcp_update_widget_settings(
            base_url,
            auth,
            session_id,
            post_id=args.post_id,
            element_id=args.element_id,
            settings=settings,
        )
    print(json.dumps(out, indent=2, ensure_ascii=False))

    err = out.get("error")
    if err:
        sys.exit(1)
    result = out.get("result") or {}
    if result.get("isError"):
        sys.exit(1)
    structured = result.get("structuredContent") or {}
    if structured.get("success") is False:
        sys.exit(1)


if __name__ == "__main__":
    main()
