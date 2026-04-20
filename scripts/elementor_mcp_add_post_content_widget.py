#!/usr/bin/env python3
"""
Add Elementor Pro Theme Builder "Post Content" widget (theme-post-content) to a template.

Required on Single Post/Page templates so "Edit with Elementor" works on pages that use this template.

Example (Single Page template that wraps Home 2026 — post_id 1589, root container 3b4d6f4):
  python3 scripts/elementor_mcp_add_post_content_widget.py \\
    --post-id 1589 --parent-id 3b4d6f4

If the hero appeared twice after adding Post Content, the Single template also had a native hero
block — remove that container (e.g. `elementor-mcp-remove-element` on template post_id, element_id
of the duplicate hero row) so only the page body (embedded Home 2026 Hero template + sections) shows.
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
    mcp_call_tool,
    mcp_initialize,
)


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
    root = Path(__file__).resolve().parent.parent
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Add theme-post-content widget via elementor-mcp-add-widget.")
    p.add_argument("--post-id", type=int, default=1589, help="Elementor library post ID (Single Page template).")
    p.add_argument(
        "--parent-id",
        default="3b4d6f4",
        help="Container element_id to attach the widget (default: root section on template 1589).",
    )
    p.add_argument(
        "--widget-type",
        default="theme-post-content",
        help="Elementor widget slug (default: theme-post-content).",
    )
    p.add_argument("--mcp-json", type=Path, default=default_mcp)
    p.add_argument(
        "--extra-json",
        type=Path,
        help="Optional JSON file merged into add-widget arguments (e.g. insert_after).",
    )
    args = p.parse_args()

    mcp_path = args.mcp_json.expanduser().resolve()
    if not mcp_path.is_file():
        sys.exit(f"MCP config not found: {mcp_path}")

    arguments: dict = {
        "post_id": args.post_id,
        "parent_id": args.parent_id,
        "widget_type": args.widget_type,
        "settings": {},
    }
    if args.extra_json:
        extra = json.loads(Path(args.extra_json).read_text(encoding="utf-8"))
        arguments.update(extra)

    base_url, auth = load_elementor_mcp_config(mcp_path)
    session_id = mcp_initialize(base_url, auth)

    print(
        json.dumps(
            {"post_id": args.post_id, "parent_id": args.parent_id, "widget_type": args.widget_type},
            indent=2,
        )
    )
    out = mcp_call_tool(
        base_url,
        auth,
        session_id,
        tool_name="elementor-mcp-add-widget",
        arguments=arguments,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    check_mcp_response(out)
    sc = (out.get("result") or {}).get("structuredContent") or {}
    eid = sc.get("element_id")
    if eid:
        print(f"Added Post Content widget element_id={eid}. Publish the template in Elementor if needed.")
    else:
        print("Warning: structuredContent had no element_id; check MCP response above.")


if __name__ == "__main__":
    main()
