#!/usr/bin/env bash
# Editorial tiffin plans listing -> Elementor draft (post 10297, widget 24caf9c).
# macOS / Linux equivalent of tmp-mcp-push-tiffin-plans-listing.ps1
#
# Optional: first argument overrides the HTML path (relative to repo root).

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_REL="${1:-elementor-html/tiffin-plans-listing-editorial-2026.html}"

exec python3 "$ROOT/scripts/elementor_mcp_push_html_widget.py" \
  --post-id 10297 \
  --element-id "24caf9c" \
  --html "$HTML_REL"
