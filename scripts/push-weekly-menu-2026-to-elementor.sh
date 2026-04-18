#!/usr/bin/env bash
# Push weekly-menu-page-2026.html to Elementor (Weekly Menu page, default post 1098).
# Copy elementor-html/.weekly-menu-page-element-id.example.json to
# elementor-html/.weekly-menu-page-element-id.json and set html_widget.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAP="$ROOT/elementor-html/.weekly-menu-page-element-id.json"
PY="$ROOT/scripts/elementor_mcp_push_html_widget.py"
if [[ ! -f "$MAP" ]]; then
  echo "Missing $MAP — copy .weekly-menu-page-element-id.example.json and fill html_widget." >&2
  exit 1
fi
POST_ID="${POST_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['post_id'])")}"
EL="${ELEMENT_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['html_widget'])")}"
exec "$PY" --post-id "$POST_ID" --element-id "$EL" --html "$ROOT/elementor-html/weekly-menu-page-2026.html"
