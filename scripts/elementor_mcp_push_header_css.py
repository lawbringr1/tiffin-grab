#!/usr/bin/env python3
"""
Push TiffinGrab navbar CSS for the Theme Builder **header** template (default post **1863**).

1. **Custom CSS on the header library post** — `elementor-mcp-add-custom-css` so Elementor stores
   rules on the header template (what you edit in Theme Builder).

2. **Inline `<style>` in an HTML widget (recommended)** — rules are output **inside the header
   markup**, so they apply on every page that uses this header (including new home pages), even
   when LiteSpeed combines CSS or omits `post-1863.css` from the `<head>`.

Optional: merge the same navbar CSS into the **Default Kit** (post 591) with `--kit-post-id 591`
if you also want kit-level copies (not required when the inline widget is used).

Requires `.cursor/mcp.json` with `mcpServers.elementor-mcp` url + Authorization.

Examples:
  python3 scripts/elementor_mcp_push_header_css.py
  python3 scripts/elementor_mcp_push_header_css.py --create-inline-widget
  python3 scripts/elementor_mcp_push_header_css.py --kit-post-id 591
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

_BUILD_STAMP_RE = re.compile(r"^\s*/\* tg-header-build:[^\n]+?\*/\s*\n?")

KIT_NAV_BANNER = """
/*
  --- Header navbar (source: elementor-html/site-header-navbar-2026.css) ---
  Merged into Default Kit when --kit-post-id is set.
*/
"""


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


def mcp_post(url: str, auth: str, body: dict, session_id: str | None, timeout: int = 120) -> tuple[dict[str, str], dict]:
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
    stripped = _BUILD_STAMP_RE.sub("", css, count=1)
    stamp = f"/* tg-header-build: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} */\n"
    return stamp + stripped.lstrip("\n")


def wrap_inline_style(css: str) -> str:
    script = """
<script id="tg-header-referral-banner-script">
(function () {
  var header = document.querySelector('header.elementor.elementor-1863.elementor-location-header, .elementor-location-header.elementor-1863');
  if (!header) return;
  var existing = header.querySelector('.tg-referral-banner-link');
  if (existing) return;
  var link = document.createElement('a');
  link.className = 'tg-referral-banner-link';
  link.href = 'https://tiffingrab.ca/referral-program/';
  link.textContent = 'Refer & Earn Free Tiffins - You: +1, Friend: +2. Tap to join now.';
  link.setAttribute('aria-label', 'Open Referral Program page');
  header.appendChild(link);

  function ensureMobileDock() {
    var isMobile = window.matchMedia('(max-width: 767px)').matches;
    var existing = document.querySelector('.tg-mobile-dock');
    if (!isMobile) {
      if (existing) existing.remove();
      document.body.style.paddingBottom = '';
      return;
    }

    if (!existing) {
      var nav = document.createElement('nav');
      nav.className = 'tg-mobile-dock';
      nav.setAttribute('aria-label', 'Mobile quick navigation');
      nav.innerHTML =
        '<a href="https://tiffingrab.ca/">Home</a>' +
        '<a href="https://tiffingrab.ca/referral-program/">Referral</a>' +
        '<a href="https://tiffingrab.ca/tiffin-plans/">Plans</a>' +
        '<a href="https://tiffingrab.ca/menu/">Menu</a>' +
        '<a href="https://tiffingrab.ca/contact-us/">Contact</a>';
      document.body.appendChild(nav);
    }

    var path = (window.location.pathname || '/').replace(/\/+$/, '') || '/';
    document.querySelectorAll('.tg-mobile-dock a').forEach(function (a) {
      var hrefPath = new URL(a.href, window.location.origin).pathname.replace(/\/+$/, '') || '/';
      if (hrefPath === path) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });

    document.body.style.paddingBottom = 'calc(4.9rem + env(safe-area-inset-bottom))';
  }

  ensureMobileDock();
  window.addEventListener('resize', ensureMobileDock, { passive: true });
})();
</script>
""".strip()
    return f'<style id="tg-header-navbar-rules">\n{css.rstrip()}\n</style>\n{script}\n'


def structured_from_result(raw: dict) -> dict:
    res = raw.get("result") or {}
    if res.get("isError"):
        txt = res.get("content", [{}])[0].get("text", str(res))
        sys.exit(f"MCP tool error: {txt[:2000]}")
    return res.get("structuredContent") or {}


def mcp_add_custom_css(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    post_id: int,
    css: str,
    replace: bool,
    rpc_id: int,
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
    if raw.get("error"):
        sys.exit(f"MCP error: {raw['error']}")
    structured_from_result(raw)
    return raw


def mcp_call_tool(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    name: str,
    arguments: dict,
    rpc_id: int,
) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    _h, raw = mcp_post(base_url, auth, body, session_id=session_id)
    if raw.get("error"):
        sys.exit(f"MCP error: {raw['error']}")
    sc = structured_from_result(raw)
    return sc


def main() -> None:
    root = repo_root()
    default_nav = root / "elementor-html" / "site-header-navbar-2026.css"
    default_kit = root / "elementor-html" / "elementor-kit-global-custom-css.css"
    default_inline_id = root / "elementor-html" / "header-navbar-inline-element.id"
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Push Theme Builder header navbar CSS via Elementor MCP.")
    p.add_argument("--nav-css", type=Path, default=default_nav, help="Navbar CSS file path")
    p.add_argument("--kit-css", type=Path, default=default_kit, help="Kit CSS file (only if --kit-post-id set)")
    p.add_argument("--kit-post-id", type=int, default=0, help="Default Kit post ID (591). 0 = skip kit merge.")
    p.add_argument("--header-post-id", type=int, default=1863, help="Theme Builder header template post ID.")
    p.add_argument(
        "--inline-element-id-file",
        type=Path,
        default=default_inline_id,
        help="File containing one line: HTML widget element id for inline <style> (optional).",
    )
    p.add_argument(
        "--create-inline-widget",
        action="store_true",
        help="Add an HTML widget to the header (parent column 6b4ffdd) and save its id to --inline-element-id-file.",
    )
    p.add_argument(
        "--inline-parent-id",
        default="6b4ffdd",
        help="Elementor container data-id to attach new HTML widget (default: logo column on desktop row).",
    )
    p.add_argument(
        "--append",
        action="store_true",
        help="Append custom CSS instead of replace (default: replace).",
    )
    p.add_argument("--mcp-json", type=Path, default=default_mcp, help="Path to Cursor MCP config")
    args = p.parse_args()

    nav_path = args.nav_css.expanduser().resolve()
    kit_path = args.kit_css.expanduser().resolve()
    if not nav_path.is_file():
        sys.exit(f"Navbar CSS not found: {nav_path}")
    if args.kit_post_id and not kit_path.is_file():
        sys.exit(f"Kit CSS not found: {kit_path}")

    mcp_path = args.mcp_json.expanduser().resolve()
    if not mcp_path.is_file():
        sys.exit(f"MCP config not found: {mcp_path}")

    nav_stamped = with_push_build_stamp(nav_path.read_text(encoding="utf-8"))
    base_url, auth = load_mcp(mcp_path)
    session_id = mcp_initialize(base_url, auth)
    replace = not args.append
    rpc = 2

    if args.kit_post_id:
        kit_text = kit_path.read_text(encoding="utf-8").rstrip() + "\n"
        combined_kit = kit_text + KIT_NAV_BANNER + "\n" + nav_stamped + "\n"
        print(f"Pushing kit + navbar → kit post_id={args.kit_post_id} ...")
        mcp_add_custom_css(
            base_url,
            auth,
            session_id,
            post_id=args.kit_post_id,
            css=combined_kit,
            replace=replace,
            rpc_id=rpc,
        )
        rpc += 1

    print(f"Pushing navbar CSS → header template post_id={args.header_post_id} ...")
    mcp_add_custom_css(
        base_url,
        auth,
        session_id,
        post_id=args.header_post_id,
        css=nav_stamped,
        replace=replace,
        rpc_id=rpc,
    )
    rpc += 1

    id_file = args.inline_element_id_file.expanduser().resolve()
    if args.create_inline_widget:
        if id_file.is_file() and id_file.read_text(encoding="utf-8").strip():
            sys.exit(f"Refusing to create widget: {id_file.name} already has an id. Delete it or remove --create-inline-widget.")
        print(
            f"Creating HTML widget under parent {args.inline_parent_id!r} on post {args.header_post_id} ..."
        )
        sc = mcp_call_tool(
            base_url,
            auth,
            session_id,
            name="elementor-mcp-add-widget",
            arguments={
                "post_id": args.header_post_id,
                "parent_id": args.inline_parent_id,
                "widget_type": "html",
                "settings": {"html": "<!-- TiffinGrab navbar styles (updated by MCP) -->\n"},
            },
            rpc_id=rpc,
        )
        rpc += 1
        new_id = sc.get("element_id")
        if not new_id:
            sys.exit(f"add_widget did not return element_id: {sc}")
        id_file.parent.mkdir(parents=True, exist_ok=True)
        id_file.write_text(str(new_id).strip() + "\n", encoding="utf-8")
        print(f"Wrote element id to {id_file.relative_to(root)}: {new_id}")

    if id_file.is_file():
        element_id = id_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if element_id:
            print(f"Pushing inline <style> → HTML widget {element_id} on post {args.header_post_id} ...")
            mcp_call_tool(
                base_url,
                auth,
                session_id,
                name="elementor-mcp-update-widget",
                arguments={
                    "post_id": args.header_post_id,
                    "element_id": element_id,
                    "settings": {"html": wrap_inline_style(nav_stamped)},
                },
                rpc_id=rpc,
            )

    print(
        "\nDone. Header template holds the navbar; inline HTML widget (if configured) outputs "
        "styles with the header on every page using this theme location.\n"
        "After changes: Elementor → Tools → Regenerate CSS & Data, then purge LiteSpeed / Hostinger cache.\n"
    )


if __name__ == "__main__":
    main()
