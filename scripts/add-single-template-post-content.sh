#!/usr/bin/env bash
# One-time: add Theme Builder "Post Content" (theme-post-content) to Single Page template 1589.
# Requires .cursor/mcp.json with elementor-mcp. Do not run twice (only one Post Content per template).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$ROOT/scripts/elementor_mcp_add_post_content_widget.py" \
  --post-id 1589 \
  --parent-id 3b4d6f4 \
  "$@"
