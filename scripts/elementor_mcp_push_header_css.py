#!/usr/bin/env python3
"""
Push `elementor-html/site-header-navbar-2026.css` to an Elementor header template via
`elementor-mcp-add-custom-css` (page-level custom CSS; requires Elementor Pro on the site).

Requires `.cursor/mcp.json` with `mcpServers.elementor-mcp` url + Authorization.

Examples:
  ./scripts/elementor_mcp_push_header_css.py
  ./scripts/elementor_mcp_push_header_css.py --post-id 721
  ./scripts/elementor_mcp_push_header_css.py --css path/to/other.css
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Prepended only when pushing (not saved to disk). Changes the stored CSS so Elementor cache busts;
# full-page HTML may still be edge-cached until you purge LiteSpeed / Hostinger CDN.
_BUILD_STAMP_RE = re.compile(r"^\s*/\* tg-header-build:[^\n]+?\*/\s*\n?")


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


def mcp_post(url: str, auth: str, body: dict, session_id: str | None, timeout: int = 120) -> tuple[dict[str, str], str]:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", auth)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        raw = resp.read().decode("utf-8")
    return headers, raw


def mcp_initialize(base_url: str, auth: str) -> str:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "tiffin-grab-header-css", "version": "1"},
        },
    }
    headers, _ = mcp_post(base_url, auth, body, session_id=None, timeout=30)
    sid = headers.get("mcp-session-id")
    if not sid:
        sys.exit("MCP initialize did not return Mcp-Session-Id header.")
    return sid.strip()


def with_push_build_stamp(css: str) -> str:
    """Strip any previous stamp and prepend UTC ISO time (in-memory only)."""
    stripped = _BUILD_STAMP_RE.sub("", css, count=1)
    stamp = f"/* tg-header-build: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} */\n"
    return stamp + stripped.lstrip("\n")


def mcp_add_custom_css(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    post_id: int,
    css: str,
    replace: bool,
) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "elementor-mcp-add-custom-css",
            "arguments": {"post_id": post_id, "css": css, "replace": replace},
        },
    }
    _h, raw = mcp_post(base_url, auth, body, session_id=session_id)
    return json.loads(raw)


def main() -> None:
    root = repo_root()
    default_css = root / "elementor-html" / "site-header-navbar-2026.css"
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Push header navbar CSS via elementor-mcp-add-custom-css.")
    p.add_argument(
        "--post-id",
        type=int,
        default=1863,
        help='Elementor Theme Builder header template post ID (default: 1863 “New Header”, shortcode [elementor-template id="1863"]).',
    )
    p.add_argument("--css", type=Path, default=default_css, help="CSS file path (default: elementor-html/site-header-navbar-2026.css)")
    p.add_argument(
        "--append",
        action="store_true",
        help="Append to existing page custom CSS instead of replacing (default: replace).",
    )
    p.add_argument("--mcp-json", type=Path, default=default_mcp, help="Path to Cursor MCP config")
    args = p.parse_args()

    css_path = args.css.expanduser().resolve()
    if not css_path.is_file():
        sys.exit(f"CSS file not found: {css_path}")

    mcp_path = args.mcp_json.expanduser().resolve()
    if not mcp_path.is_file():
        sys.exit(f"MCP config not found: {mcp_path}")

    css = with_push_build_stamp(css_path.read_text(encoding="utf-8"))
    base_url, auth = load_mcp(mcp_path)
    session_id = mcp_initialize(base_url, auth)

    print(f"Pushing {css_path.relative_to(root)} → post_id={args.post_id} (replace={not args.append}) ...")
    out = mcp_add_custom_css(
        base_url,
        auth,
        session_id,
        post_id=args.post_id,
        css=css,
        replace=not args.append,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))

    if out.get("error"):
        sys.exit(1)
    result = out.get("result") or {}
    if result.get("isError"):
        sys.exit(1)

    print(
        "\nIf the navbar still looks old in a new browser, the HTML is likely served from "
        "Hostinger/LiteSpeed full-page cache (incognito does not bypass the CDN).\n"
        "Purge after each header deploy:\n"
        "  • WP Admin → LiteSpeed Cache → Toolbox → Purge → Purge All\n"
        "  • Hostinger hPanel → your site → Performance / Cache → Purge (if shown)\n"
        "  • Elementor → Tools → Regenerate CSS & Data\n"
        "Verify: View Source or Network → search for tg-header-build (UTC stamp on each push).\n"
    )


if __name__ == "__main__":
    main()
