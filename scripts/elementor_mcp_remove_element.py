#!/usr/bin/env python3
"""
Remove one Elementor element (container or widget) via elementor-mcp-remove-element.

Example (already applied on production: duplicate hero container on Single template 1589):
  python3 scripts/elementor_mcp_remove_element.py --post-id 1589 --element-id 6760da1
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

    p = argparse.ArgumentParser(description="Remove Elementor element via elementor-mcp-remove-element.")
    p.add_argument("--post-id", type=int, required=True)
    p.add_argument("--element-id", required=True)
    p.add_argument("--mcp-json", type=Path, default=default_mcp)
    args = p.parse_args()

    mcp_path = args.mcp_json.expanduser().resolve()
    if not mcp_path.is_file():
        sys.exit(f"MCP config not found: {mcp_path}")

    base_url, auth = load_elementor_mcp_config(mcp_path)
    session_id = mcp_initialize(base_url, auth)

    out = mcp_call_tool(
        base_url,
        auth,
        session_id,
        tool_name="elementor-mcp-remove-element",
        arguments={"post_id": args.post_id, "element_id": args.element_id},
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    check_mcp_response(out)
    print("Done.")


if __name__ == "__main__":
    main()
