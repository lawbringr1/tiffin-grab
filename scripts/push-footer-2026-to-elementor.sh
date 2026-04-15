#!/usr/bin/env bash
# Push repo footer HTML to Elementor Theme Builder footer template.
# 1) In WP: Templates → Theme Builder → Footer → edit template (ID 1907 on tiffingrab.ca).
# 2) Add a single HTML widget (or select existing), copy its element id from Structure panel / DevTools (data-id on .elementor-element).
# 3) Run:
#    ELEMENT_ID=xxxxxxxx ./scripts/push-footer-2026-to-elementor.sh
#
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${ELEMENT_ID:?Set ELEMENT_ID to the HTML widget element id (e.g. ELEMENT_ID=abc12345)}"
exec python3 "$ROOT/scripts/elementor_mcp_push_html_widget.py" \
  --post-id 1907 \
  --element-id "$ELEMENT_ID" \
  --html "$ROOT/elementor-html/site-footer-2026.html"
