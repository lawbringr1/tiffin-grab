#!/usr/bin/env bash
# Push repo footer HTML to Elementor Theme Builder footer template (post 1907, "New Footer").
# HTML widget element id is set after the 2026 MCP migration; override if Elementor regenerates ids.
#
# Usage:
#   ./scripts/push-footer-2026-to-elementor.sh
#   ELEMENT_ID=xxxxxxxx ./scripts/push-footer-2026-to-elementor.sh
#
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ELEMENT_ID="${ELEMENT_ID:-e725757}"
exec python3 "$ROOT/scripts/elementor_mcp_push_html_widget.py" \
  --post-id 1907 \
  --element-id "$ELEMENT_ID" \
  --html "$ROOT/elementor-html/site-footer-2026.html"
