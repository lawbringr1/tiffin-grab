#!/usr/bin/env python3
"""
Push header navbar CSS via `elementor-mcp-add-custom-css`.

**Why two targets:** On the live site, `post-1863.css` (Theme Builder header) is generated but
**not linked** on full-width pages — only `post-591.css` (Elementor Default Kit) is enqueued.
So the navbar rules must live in **Site Settings → Custom CSS** (kit post **591**) to apply
on the front end. We still push navbar-only CSS to the header template (**1863**) so the
library post stays in sync when editing in Elementor.

Requires `.cursor/mcp.json` with `mcpServers.elementor-mcp` url + Authorization.

Examples:
  ./scripts/elementor_mcp_push_header_css.py
  ./scripts/elementor_mcp_push_header_css.py --kit-post-id 591 --header-post-id 1863
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
    rpc_id: int = 2,
) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "tools/call",
        "params": {
            "name": "elementor-mcp-add-custom-css",
            "arguments": {"post_id": post_id, "css": css, "replace": replace},
        },
    }
    _h, raw = mcp_post(base_url, auth, body, session_id=session_id)
    return json.loads(raw)


KIT_NAV_BANNER = """
/*
  --- Header navbar (source: elementor-html/site-header-navbar-2026.css) ---
  Included in the Default Kit so rules load via post-591.css (enqueued sitewide). Theme Builder
  header post 1863 does not enqueue post-1863.css on many front-end pages.
*/
"""


def main() -> None:
    root = repo_root()
    default_nav = root / "elementor-html" / "site-header-navbar-2026.css"
    default_kit = root / "elementor-html" / "elementor-kit-global-custom-css.css"
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Push kit + header navbar CSS via elementor-mcp-add-custom-css.")
    p.add_argument("--nav-css", type=Path, default=default_nav, help="Navbar CSS (default: elementor-html/site-header-navbar-2026.css)")
    p.add_argument("--kit-css", type=Path, default=default_kit, help="Elementor Default Kit custom CSS (default: elementor-html/elementor-kit-global-custom-css.css)")
    p.add_argument(
        "--kit-post-id",
        type=int,
        default=591,
        help="Elementor Default Kit post ID (default: 591).",
    )
    p.add_argument(
        "--header-post-id",
        type=int,
        default=1863,
        help='Theme Builder header template post ID (default: 1863). Use 0 to skip.',
    )
    p.add_argument(
        "--append",
        action="store_true",
        help="Append to existing custom CSS instead of replacing (default: replace).",
    )
    p.add_argument("--mcp-json", type=Path, default=default_mcp, help="Path to Cursor MCP config")
    args = p.parse_args()

    nav_path = args.nav_css.expanduser().resolve()
    kit_path = args.kit_css.expanduser().resolve()
    if not nav_path.is_file():
        sys.exit(f"Navbar CSS not found: {nav_path}")
    if not kit_path.is_file():
        sys.exit(f"Kit CSS not found: {kit_path}")

    mcp_path = args.mcp_json.expanduser().resolve()
    if not mcp_path.is_file():
        sys.exit(f"MCP config not found: {mcp_path}")

    nav_stamped = with_push_build_stamp(nav_path.read_text(encoding="utf-8"))
    kit_text = kit_path.read_text(encoding="utf-8").rstrip() + "\n"
    combined_kit = kit_text + KIT_NAV_BANNER + "\n" + nav_stamped + "\n"

    base_url, auth = load_mcp(mcp_path)
    session_id = mcp_initialize(base_url, auth)
    replace = not args.append
    rpc = 2

    print(f"Pushing {kit_path.relative_to(root)} + {nav_path.relative_to(root)} → kit post_id={args.kit_post_id} (replace={replace}) ...")
    out_kit = mcp_add_custom_css(
        base_url,
        auth,
        session_id,
        post_id=args.kit_post_id,
        css=combined_kit,
        replace=replace,
        rpc_id=rpc,
    )
    print(json.dumps(out_kit, indent=2, ensure_ascii=False))
    if out_kit.get("error"):
        sys.exit(1)
    if (out_kit.get("result") or {}).get("isError"):
        sys.exit(1)

    rpc += 1
    if args.header_post_id:
        print(f"Pushing {nav_path.relative_to(root)} → header template post_id={args.header_post_id} (replace={replace}) ...")
        out_hdr = mcp_add_custom_css(
            base_url,
            auth,
            session_id,
            post_id=args.header_post_id,
            css=nav_stamped,
            replace=replace,
            rpc_id=rpc,
        )
        print(json.dumps(out_hdr, indent=2, ensure_ascii=False))
        if out_hdr.get("error"):
            sys.exit(1)
        if (out_hdr.get("result") or {}).get("isError"):
            sys.exit(1)

    print(
        "\nNavbar CSS is now in the Default Kit (post-591.css is enqueued on the homepage). "
        "Purge caches so HTML/CSS pick up the new post-591 version:\n"
        "  • WP Admin → LiteSpeed Cache → Toolbox → Purge → Purge All\n"
        "  • Hostinger hPanel → Performance / Cache → Purge (if shown)\n"
        "  • Elementor → Tools → Regenerate CSS & Data\n"
        "Verify: fetch post-591.css and search for tg-header-build or Ghar Jaisa.\n"
    )


if __name__ == "__main__":
    main()
