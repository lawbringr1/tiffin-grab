#!/usr/bin/env python3
"""
One-time (or repeatable) Elementor MCP setup for Legal hub + four policy pages.

- Clears each page, builds containers + HTML widgets, pushes repo HTML.
- Writes elementor-html/.legal-element-ids.json for scripts/push-legal-2026-to-elementor.sh

Requires: .cursor/mcp.json with elementor-mcp url + Authorization.

Usage:
  python3 scripts/setup_legal_elementor_2026.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = ROOT / ".cursor" / "mcp.json"
OUT_IDS = ROOT / "elementor-html" / ".legal-element-ids.json"

POST_LEGAL_HUB = 11032
POST_TERMS = 552
POST_PRIVACY = 511
POST_REFUND = 11034
POST_DELIVERY = 11036


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
            "clientInfo": {"name": "setup-legal", "version": "1"},
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
        sys.exit(f"Tool error: {txt[:2000]}")
    return res


def structured(res: dict) -> dict:
    return res.get("structuredContent") or {}


def delete_content(url: str, auth: str, sid: str, post_id: int) -> None:
    call_tool(url, auth, sid, "elementor-mcp-delete-page-content", {"post_id": post_id})


def add_container(
    url: str,
    auth: str,
    sid: str,
    post_id: int,
    parent_id: str | None,
    settings: dict,
) -> str:
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
            {"post_id": post_id, "settings": {"post_status": "publish"}},
        )
    )


def setup_hub(url: str, auth: str, sid: str, post_id: int, html_path: Path) -> str:
    delete_content(url, auth, sid, post_id)
    row = add_container(
        url,
        auth,
        sid,
        post_id,
        None,
        {"content_width": "full", "flex_direction": "row", "flex_gap": {"unit": "px", "column": "24", "row": "24", "isLinked": False}},
    )
    inner = add_container(
        url,
        auth,
        sid,
        post_id,
        row,
        {"content_width": "full", "flex_direction": "column", "width": {"unit": "%", "size": 100, "sizes": []}},
    )
    wid = add_html_widget(url, auth, sid, post_id, inner, "<p>Loading…</p>")
    update_widget_html(url, auth, sid, post_id, wid, html_path.read_text(encoding="utf-8"))
    publish(url, auth, sid, post_id)
    return wid


def setup_policy(url: str, auth: str, sid: str, post_id: int, shell_path: Path, content_path: Path) -> tuple[str, str]:
    delete_content(url, auth, sid, post_id)
    row = add_container(
        url,
        auth,
        sid,
        post_id,
        None,
        {"content_width": "full", "flex_direction": "row", "flex_gap": {"unit": "px", "column": "40", "row": "32", "isLinked": False}},
    )
    c_left = add_container(
        url,
        auth,
        sid,
        post_id,
        row,
        {"content_width": "full", "flex_direction": "column", "width": {"unit": "%", "size": 28, "sizes": []}},
    )
    c_right = add_container(
        url,
        auth,
        sid,
        post_id,
        row,
        {"content_width": "full", "flex_direction": "column", "width": {"unit": "%", "size": 72, "sizes": []}},
    )
    w_shell = add_html_widget(url, auth, sid, post_id, c_left, "<p>…</p>")
    w_main = add_html_widget(url, auth, sid, post_id, c_right, "<p>…</p>")
    update_widget_html(url, auth, sid, post_id, w_shell, shell_path.read_text(encoding="utf-8"))
    update_widget_html(url, auth, sid, post_id, w_main, content_path.read_text(encoding="utf-8"))
    publish(url, auth, sid, post_id)
    return w_shell, w_main


def main() -> None:
    if not MCP_JSON.is_file():
        sys.exit(f"Missing {MCP_JSON}")

    url, auth = load_mcp()
    sid = mcp_init(url, auth)

    eh = ROOT / "elementor-html"
    hub_html = eh / "legal-hub-index-2026.html"
    shell = eh / "legal-shell-2026.html"
    c_terms = eh / "legal-content-terms-2026.html"
    c_priv = eh / "legal-content-privacy-2026.html"
    c_ref = eh / "legal-content-refund-2026.html"
    c_del = eh / "legal-content-delivery-2026.html"
    for p in (hub_html, shell, c_terms, c_priv, c_ref, c_del):
        if not p.is_file():
            sys.exit(f"Missing {p}")

    mapping: dict = {}

    print("Setting up Legal hub", POST_LEGAL_HUB)
    mapping["legal_hub"] = {"post_id": POST_LEGAL_HUB, "html_widget": setup_hub(url, auth, sid, POST_LEGAL_HUB, hub_html)}

    print("Setting up Terms", POST_TERMS)
    a, b = setup_policy(url, auth, sid, POST_TERMS, shell, c_terms)
    mapping["terms"] = {"post_id": POST_TERMS, "shell_widget": a, "content_widget": b}

    print("Setting up Privacy", POST_PRIVACY)
    a, b = setup_policy(url, auth, sid, POST_PRIVACY, shell, c_priv)
    mapping["privacy"] = {"post_id": POST_PRIVACY, "shell_widget": a, "content_widget": b}

    print("Setting up Refund", POST_REFUND)
    a, b = setup_policy(url, auth, sid, POST_REFUND, shell, c_ref)
    mapping["refund"] = {"post_id": POST_REFUND, "shell_widget": a, "content_widget": b}

    print("Setting up Delivery", POST_DELIVERY)
    a, b = setup_policy(url, auth, sid, POST_DELIVERY, shell, c_del)
    mapping["delivery"] = {"post_id": POST_DELIVERY, "shell_widget": a, "content_widget": b}

    OUT_IDS.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print("Wrote", OUT_IDS.relative_to(ROOT))
    print(json.dumps(mapping, indent=2))


if __name__ == "__main__":
    main()
