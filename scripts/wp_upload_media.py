#!/usr/bin/env python3
"""Upload a file to WordPress media via REST, reusing elementor-mcp Basic auth from .cursor/mcp.json.

Usage: wp_upload_media.py <local-file> [remote-filename] [content-type]
Prints the resulting source_url.
"""
from __future__ import annotations

import json
import mimetypes
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def auth_header() -> str:
    d = json.loads((ROOT / ".cursor" / "mcp.json").read_text())
    auth = (d["mcpServers"]["elementor-mcp"].get("headers") or {}).get("Authorization")
    if not auth:
        sys.exit("No Basic auth in .cursor/mcp.json elementor-mcp headers")
    return auth


def main() -> None:
    src = Path(sys.argv[1]).expanduser()
    if not src.is_file():
        sys.exit(f"File not found: {src}")
    remote = sys.argv[2] if len(sys.argv) > 2 else src.name
    ctype = sys.argv[3] if len(sys.argv) > 3 else (mimetypes.guess_type(remote)[0] or "application/octet-stream")

    req = urllib.request.Request(
        "https://tiffingrab.ca/wp-json/wp/v2/media",
        data=src.read_bytes(),
        method="POST",
    )
    req.add_header("Authorization", auth_header())
    req.add_header("Content-Type", ctype)
    req.add_header("Content-Disposition", f'attachment; filename="{remote}"')
    with urllib.request.urlopen(req, timeout=120) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    print(json.dumps({"id": out.get("id"), "source_url": out.get("source_url")}, indent=2))


if __name__ == "__main__":
    main()
