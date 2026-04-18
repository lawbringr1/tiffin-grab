#!/usr/bin/env python3
"""Rebuild Contact Us page (post 562) as a single full-width HTML widget and push contact-us-page-2026.html."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = ROOT / ".cursor" / "mcp.json"
POST_ID = 562
HTML_FILE = ROOT / "elementor-html" / "contact-us-page-2026.html"
OUT_JSON = ROOT / "elementor-html" / ".contact-page-element-id.json"


def load_mcp() -> tuple[str, str]:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    ec = data.get("mcpServers", {}).get("elementor-mcp")
    if not ec:
        sys.exit("No elementor-mcp")
    return str(ec["url"]).rstrip("/"), (ec.get("headers") or {}).get("Authorization", "")


def mcp_post(url: str, auth: str, body: dict, sid: str | None) -> tuple[dict, dict]:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", auth)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if sid:
        req.add_header("Mcp-Session-Id", sid)
    with urllib.request.urlopen(req, timeout=120) as r:
        h = {k.lower(): v for k, v in r.headers.items()}
        return h, json.loads(r.read().decode())


def init(url: str, auth: str) -> str:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "contact-setup", "version": "1"}},
    }
    h, _ = mcp_post(url, auth, body, None)
    sid = h.get("mcp-session-id")
    if not sid:
        sys.exit("No session")
    return sid


def call(url: str, auth: str, sid: str, name: str, args: dict) -> dict:
    body = {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": args}}
    _, raw = mcp_post(url, auth, body, sid)
    if raw.get("error"):
        sys.exit(str(raw["error"]))
    res = raw.get("result") or {}
    if res.get("isError"):
        sys.exit(res.get("content", [{}])[0].get("text", str(res)))
    return (res.get("structuredContent") or {})


def main() -> None:
    url, auth = load_mcp()
    sid = init(url, auth)
    html = HTML_FILE.read_text(encoding="utf-8")

    call(url, auth, sid, "elementor-mcp-delete-page-content", {"post_id": POST_ID})
    row = call(
        url,
        auth,
        sid,
        "elementor-mcp-add-container",
        {
            "post_id": POST_ID,
            "settings": {
                "content_width": "full",
                "flex_direction": "row",
                "flex_gap": {"unit": "px", "column": "0", "row": "0", "isLinked": True},
            },
        },
    )["element_id"]
    inner = call(
        url,
        auth,
        sid,
        "elementor-mcp-add-container",
        {
            "post_id": POST_ID,
            "parent_id": row,
            "settings": {"content_width": "full", "flex_direction": "column", "width": {"unit": "%", "size": 100, "sizes": []}},
        },
    )["element_id"]
    wid = call(
        url,
        auth,
        sid,
        "elementor-mcp-add-widget",
        {"post_id": POST_ID, "parent_id": inner, "widget_type": "html", "settings": {"html": "<p>Loading…</p>"}},
    )["element_id"]
    call(
        url,
        auth,
        sid,
        "elementor-mcp-update-widget",
        {"post_id": POST_ID, "element_id": wid, "settings": {"html": html}},
    )
    call(url, auth, sid, "elementor-mcp-update-page-settings", {"post_id": POST_ID, "settings": {"post_status": "publish"}})

    OUT_JSON.write_text(json.dumps({"post_id": POST_ID, "html_widget": wid}, indent=2), encoding="utf-8")
    print("post_id", POST_ID, "html_widget", wid)
    print("Wrote", OUT_JSON.relative_to(ROOT))


if __name__ == "__main__":
    main()
