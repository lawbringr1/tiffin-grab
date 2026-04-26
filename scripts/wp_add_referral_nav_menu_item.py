#!/usr/bin/env python3
"""
Add the Referral Program page to the WordPress menu used by the header (Theme Builder nav).

Uses credentials from .cursor/mcp.json → mcpServers.wordpress-http-default.env
(WP_API_USERNAME / WP_API_PASSWORD application password).

Also sets the page slug to `referral-program` if the REST user can edit the page.

Usage:
  python3 scripts/wp_add_referral_nav_menu_item.py
"""

from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MCP_JSON = ROOT / ".cursor" / "mcp.json"
MAP_JSON = ROOT / "elementor-html" / ".referral-program-page-element-id.json"
BASE = "https://tiffingrab.ca/wp-json"


def load_wp_basic_auth() -> tuple[str, str]:
    data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    env = (data.get("mcpServers") or {}).get("wordpress-http-default", {}).get("env") or {}
    user = (env.get("WP_API_USERNAME") or "").strip()
    pw = (env.get("WP_API_PASSWORD") or "").replace(" ", "").strip()
    if not user or not pw:
        sys.exit("Missing WP_API_USERNAME / WP_API_PASSWORD in mcp.json wordpress-http-default.env")
    return user, pw


def auth_header(user: str, pw: str) -> str:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return f"Basic {token}"


def request_json(method: str, path: str, user: str, pw: str, body: dict | None = None) -> tuple[int, object]:
    url = BASE.rstrip("/") + path
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", auth_header(user, pw))
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            code = resp.getcode()
            if not raw:
                return code, None
            return code, json.loads(raw)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        return e.code, json.loads(err) if err.strip().startswith("{") else err


def pick_header_menu_id(user: str, pw: str) -> tuple[int, str]:
    """Use registered menu location for Header (menu-1 on this theme) when available."""
    code, locs = request_json("GET", "/wp/v2/menu-locations", user, pw)
    if code == 200 and isinstance(locs, dict):
        for key, meta in locs.items():
            desc = str((meta or {}).get("description") or "").lower()
            if "header" in desc or key == "menu-1":
                mid = int((meta or {}).get("menu") or 0)
                if mid > 0:
                    return mid, f"{key} ({desc or 'header'})"
    code, menus = request_json("GET", "/wp/v2/menus?per_page=100", user, pw)
    if code != 200 or not isinstance(menus, list) or not menus:
        sys.exit(f"Could not resolve header menu: locations={code} menus={menus}")
    preferred = ("primary", "header", "main", "desktop", "navigation")
    scored: list[tuple[int, str, int]] = []
    for m in menus:
        mid = int(m.get("id") or 0)
        name = str(m.get("name") or "").lower()
        slug = str(m.get("slug") or "").lower()
        score = 0
        for p in preferred:
            if p in name or p in slug:
                score += 10
        scored.append((score, str(m.get("name") or slug or str(mid)), mid))
    scored.sort(reverse=True)
    _score, label, mid = scored[0]
    return mid, label


def menu_has_page_link(items: list, page_id: int) -> bool:
    for it in items:
        if str(it.get("object")) == "page" and int(it.get("object_id") or 0) == page_id:
            return True
        if page_id and it.get("url") and f"/{page_id}" in str(it.get("url")):
            return True
    return False


def main() -> None:
    user, pw = load_wp_basic_auth()
    page_id = int(json.loads(MAP_JSON.read_text(encoding="utf-8"))["post_id"])

    code, patch = request_json(
        "PATCH",
        f"/wp/v2/pages/{page_id}",
        user,
        pw,
        {"slug": "referral-program"},
    )
    if code in (200, 201):
        print("Page slug set to /referral-program/")
    else:
        print("Note: could not set page slug (non-fatal):", code, patch)

    menu_id, menu_label = pick_header_menu_id(user, pw)
    print("Using menu:", menu_label, "id=", menu_id)

    q = urllib.parse.urlencode({"menus": menu_id, "per_page": 100})
    code, items = request_json("GET", f"/wp/v2/menu-items?{q}", user, pw)
    if code != 200 or not isinstance(items, list):
        sys.exit(f"Failed to list menu items: {code} {items}")

    if menu_has_page_link(items, page_id):
        print("Menu already contains this page — nothing to do.")
        return

    code, created = request_json(
        "POST",
        "/wp/v2/menu-items",
        user,
        pw,
        {
            "title": "Referral Program",
            "type": "post_type",
            "object": "page",
            "object_id": page_id,
            "menus": menu_id,
            "status": "publish",
        },
    )
    if code not in (200, 201):
        sys.exit(f"Failed to create menu item: {code} {created}")
    print("Added nav menu item:", created.get("id"), created.get("title", {}).get("raw", created))


if __name__ == "__main__":
    main()
