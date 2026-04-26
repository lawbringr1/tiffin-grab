#!/usr/bin/env python3
"""
Create (once) or update the TiffinGrab Referral Program Elementor page.

First run (no map file):
  - elementor-mcp-create-page → new published page
  - Full-width container + HTML widget with referral-program-2026.html
  - Writes elementor-html/.referral-program-page-element-id.json

Later runs (map file exists):
  - Only updates the HTML widget content (same post_id / html_widget)

Requires: .cursor/mcp.json with elementor-mcp url + Authorization.

Usage:
  python3 scripts/setup_referral_program_page_2026.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = ROOT / ".cursor" / "mcp.json"
HTML_FILE = ROOT / "elementor-html" / "referral-program-2026.html"
OUT_MAP = ROOT / "elementor-html" / ".referral-program-page-element-id.json"
PAGE_TITLE = "Referral Program"


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
            "clientInfo": {"name": "setup-referral-program", "version": "1"},
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


def delete_content(url: str, auth: str, sid: str, post_id: int) -> None:
    call_tool(url, auth, sid, "elementor-mcp-delete-page-content", {"post_id": post_id})


def add_container(url: str, auth: str, sid: str, post_id: int, parent_id: str | None, settings: dict) -> str:
    args: dict = {"post_id": post_id, "settings": settings}
    if parent_id:
        args["parent_id"] = parent_id
    sc = structured(call_tool(url, auth, sid, "elementor-mcp-add-container", args))
    eid = sc.get("element_id")
    if not eid:
        sys.exit(f"add_container missing element_id: {sc}")
    return str(eid)


def add_html_widget(url: str, auth: str, sid: str, post_id: int, parent_id: str, html: str) -> str:
    sc = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-add-widget",
            {
                "post_id": post_id,
                "parent_id": parent_id,
                "widget_type": "html",
                "settings": {"html": html},
            },
        )
    )
    eid = sc.get("element_id")
    if not eid:
        sys.exit(f"add_widget missing element_id: {sc}")
    return str(eid)


def update_widget_html(url: str, auth: str, sid: str, post_id: int, element_id: str, html: str) -> None:
    sc = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-update-widget",
            {"post_id": post_id, "element_id": element_id, "settings": {"html": html}},
        )
    )
    if sc.get("success") is False:
        sys.exit(f"update_widget failed: {sc}")


def publish(url: str, auth: str, sid: str, post_id: int) -> None:
    structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-update-page-settings",
            {
                "post_id": post_id,
                "settings": {"post_status": "publish", "hide_title": "yes", "hide_page_title": "yes"},
            },
        )
    )


def build_page_html_shell(url: str, auth: str, sid: str, post_id: int, html: str) -> str:
    delete_content(url, auth, sid, post_id)
    row = add_container(
        url,
        auth,
        sid,
        post_id,
        None,
        {
            "content_width": "full",
            "flex_direction": "row",
            "flex_gap": {"unit": "px", "column": "0", "row": "0", "isLinked": True},
        },
    )
    inner = add_container(
        url,
        auth,
        sid,
        post_id,
        row,
        {
            "content_width": "full",
            "flex_direction": "column",
            "width": {"unit": "%", "size": 100, "sizes": []},
        },
    )
    wid = add_html_widget(url, auth, sid, post_id, inner, "<p>Loading…</p>")
    update_widget_html(url, auth, sid, post_id, wid, html)
    publish(url, auth, sid, post_id)
    return wid


def main() -> None:
    url, auth = load_mcp()
    sid = mcp_init(url, auth)
    html = HTML_FILE.read_text(encoding="utf-8")

    if OUT_MAP.is_file():
        data = json.loads(OUT_MAP.read_text(encoding="utf-8"))
        post_id = int(data["post_id"])
        wid = str(data["html_widget"])
        update_widget_html(url, auth, sid, post_id, wid, html)
        publish(url, auth, sid, post_id)
        print(f"Updated HTML widget on existing page post_id={post_id} element_id={wid}")
        print("Map:", OUT_MAP.relative_to(ROOT))
        return

    created = structured(
        call_tool(
            url,
            auth,
            sid,
            "elementor-mcp-create-page",
            {"title": PAGE_TITLE, "status": "publish", "post_type": "page"},
        )
    )
    post_id = int(created.get("post_id") or created.get("id") or 0)
    if post_id <= 0:
        sys.exit(f"create-page missing post_id: {created}")

    wid = build_page_html_shell(url, auth, sid, post_id, html)
    OUT_MAP.write_text(json.dumps({"post_id": post_id, "html_widget": wid}, indent=2), encoding="utf-8")
    print("Created Referral Program page post_id:", post_id, "html_widget:", wid)
    print("Wrote", OUT_MAP.relative_to(ROOT))
    print("Add to header menu: python3 scripts/wp_add_referral_nav_menu_item.py")


if __name__ == "__main__":
    main()
