#!/usr/bin/env python3
"""
One-time Elementor MCP setup for /menu/ (post 1098):

1. Export current Elementor JSON from the public menu page.
2. Create a published clone page "Weekly Menu — Data" and import that JSON (REST reads this post).
3. Replace the public menu page with a single full-width HTML widget (weekly-menu-page-2026.html).
4. Patch mu-plugins/tiffingrab-weekly-menu-rest.php TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID to the clone ID.
5. Write elementor-html/.weekly-menu-page-element-id.json for scripts/push-weekly-menu-2026-to-elementor.sh

Requires: .cursor/mcp.json with elementor-mcp url + Authorization.

Usage:
  python3 scripts/setup_weekly_menu_page_2026.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = ROOT / ".cursor" / "mcp.json"
PUBLIC_POST_ID = 1098
HTML_FILE = ROOT / "elementor-html" / "weekly-menu-page-2026.html"
MU_PLUGIN = ROOT / "wordpress" / "wp-content" / "mu-plugins" / "tiffingrab-weekly-menu-rest.php"
OUT_MAP = ROOT / "elementor-html" / ".weekly-menu-page-element-id.json"
DATA_PAGE_TITLE = "Weekly Menu — Data"


def load_mcp() -> tuple[str, str]:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    ec = data.get("mcpServers", {}).get("elementor-mcp")
    if not ec:
        sys.exit("No elementor-mcp in mcp.json")
    auth = (ec.get("headers") or {}).get("Authorization")
    url = str(ec.get("url", "")).rstrip("/")
    if not auth or not url:
        sys.exit("elementor-mcp missing url or Authorization")
    return url, auth


def mcp_post(url: str, auth: str, body: dict, session_id: str | None) -> tuple[dict[str, str], dict]:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", auth)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    with urllib.request.urlopen(req, timeout=180) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return headers, json.loads(resp.read().decode())


def mcp_init(url: str, auth: str) -> str:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "setup-weekly-menu", "version": "1"},
        },
    }
    headers, _ = mcp_post(url, auth, body, None)
    sid = headers.get("mcp-session-id")
    if not sid:
        sys.exit("No Mcp-Session-Id from initialize")
    return sid


def call_tool(url: str, auth: str, sid: str, name: str, arguments: dict) -> dict:
    body = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    _, raw = mcp_post(url, auth, body, sid)
    if raw.get("error"):
        sys.exit(f"MCP error: {raw['error']}")
    res = raw.get("result") or {}
    if res.get("isError"):
        txt = res.get("content", [{}])[0].get("text", str(res))
        sys.exit(f"Tool error ({name}): {txt[:4000]}")
    return res


def structured(res: dict) -> dict:
    return res.get("structuredContent") or {}


def patch_mu_source_id(new_id: int) -> None:
    text = MU_PLUGIN.read_text(encoding="utf-8")
    out, n = re.subn(
        r"(const\s+TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID\s*=\s*)\d+(\s*;)",
        rf"\g<1>{new_id}\2",
        text,
        count=1,
    )
    if n != 1:
        sys.exit(f"Could not patch SOURCE_POST_ID in {MU_PLUGIN} (matches={n})")
    MU_PLUGIN.write_text(out, encoding="utf-8")


def main() -> None:
    url, auth = load_mcp()
    sid = mcp_init(url, auth)
    html = HTML_FILE.read_text(encoding="utf-8")

    ex = structured(call_tool(url, auth, sid, "elementor-mcp-export-page", {"post_id": PUBLIC_POST_ID}))
    template_json = ex.get("json")
    if not isinstance(template_json, list) or not template_json:
        sys.exit(f"export-page returned no json: keys={list(ex.keys())}")

    created = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-create-page",
            {"title": DATA_PAGE_TITLE, "status": "publish", "post_type": "page"},
        )
    )
    source_post_id = int(created.get("post_id") or created.get("id") or 0)
    if source_post_id <= 0:
        sys.exit(f"create-page missing post_id: {created}")

    imp = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-import-template",
            {"post_id": source_post_id, "template_json": template_json, "position": -1},
        )
    )
    if imp.get("success") is False:
        sys.exit(f"import-template failed: {imp}")

    call_tool(url, auth, sid, "elementor-mcp-delete-page-content", {"post_id": PUBLIC_POST_ID})
    row = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-add-container",
            {
                "post_id": PUBLIC_POST_ID,
                "settings": {
                    "content_width": "full",
                    "flex_direction": "row",
                    "flex_gap": {"unit": "px", "column": "0", "row": "0", "isLinked": True},
                },
            },
        )
    )["element_id"]
    inner = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-add-container",
            {
                "post_id": PUBLIC_POST_ID,
                "parent_id": row,
                "settings": {
                    "content_width": "full",
                    "flex_direction": "column",
                    "width": {"unit": "%", "size": 100, "sizes": []},
                },
            },
        )
    )["element_id"]
    wid = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-add-widget",
            {
                "post_id": PUBLIC_POST_ID,
                "parent_id": inner,
                "widget_type": "html",
                "settings": {"html": "<p>Loading…</p>"},
            },
        )
    )["element_id"]
    call_tool(
        url,
        auth,
        sid,
        "elementor-mcp-update-widget",
        {"post_id": PUBLIC_POST_ID, "element_id": wid, "settings": {"html": html}},
    )
    structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-update-page-settings",
            {"post_id": PUBLIC_POST_ID, "settings": {"post_status": "publish"}},
        )
    )

    patch_mu_source_id(source_post_id)
    OUT_MAP.write_text(
        json.dumps({"post_id": PUBLIC_POST_ID, "html_widget": wid, "source_post_id": source_post_id}, indent=2),
        encoding="utf-8",
    )

    print("Weekly menu public page:", PUBLIC_POST_ID, "html_widget:", wid)
    print("Elementor data clone (REST source):", source_post_id, DATA_PAGE_TITLE)
    print("Patched", MU_PLUGIN.name, "TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID ->", source_post_id)
    print("Wrote", OUT_MAP.relative_to(ROOT))
    print("\nNext: deploy the updated MU plugin to production wp-content/mu-plugins/ if needed.")


if __name__ == "__main__":
    main()
