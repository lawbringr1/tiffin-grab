#!/usr/bin/env python3
"""
Apply multiple Elementor widget setting updates in one session (elementor-mcp-update-widget).

Bundle JSON format:
  {
    "post_id": 1589,
    "widgets": [
      { "element_id": "e0e1ecb", "settings": { "title": "..." } },
      { "element_id": "c867914", "settings": { "editor": "<p>...</p>" } }
    ]
  }

Requires: .cursor/mcp.json with elementor-mcp url + Authorization.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from elementor_mcp_push_html_widget import (
    load_elementor_mcp_config,
    mcp_initialize,
    mcp_update_widget_settings,
)


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent.parent


def check_mcp_response(out: dict) -> None:
    err = out.get("error")
    if err:
        sys.exit(1)
    result = out.get("result") or {}
    if result.get("isError"):
        sys.exit(1)
    structured = result.get("structuredContent") or {}
    if structured.get("success") is False:
        sys.exit(1)


def main() -> None:
    root = repo_root_from_script()
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Push bundled Elementor widget settings via elementor-mcp.")
    p.add_argument(
        "bundle",
        type=Path,
        help="JSON file with post_id and widgets[].",
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

    bundle_path = args.bundle
    if not bundle_path.is_absolute():
        bundle_path = (root / bundle_path).resolve()
    if not bundle_path.is_file():
        sys.exit(f"Bundle not found: {bundle_path}")

    data = json.loads(bundle_path.read_text(encoding="utf-8"))
    post_id = int(data["post_id"])
    widgets = data.get("widgets") or []
    if not widgets:
        print("Bundle has no widgets — nothing to push (ok).")
        return

    base_url, auth = load_elementor_mcp_config(mcp_path)
    session_id = mcp_initialize(base_url, auth)

    for i, w in enumerate(widgets):
        eid = w.get("element_id")
        settings = w.get("settings")
        if not eid or not isinstance(settings, dict):
            sys.exit(f"widgets[{i}] needs element_id and settings object")
        print(f"Updating post {post_id} element {eid} ...")
        out = mcp_update_widget_settings(
            base_url,
            auth,
            session_id,
            post_id=post_id,
            element_id=str(eid),
            settings=settings,
        )
        print(json.dumps(out, indent=2, ensure_ascii=False))
        check_mcp_response(out)

    print("Done.")


if __name__ == "__main__":
    main()
