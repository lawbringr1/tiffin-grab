#!/usr/bin/env bash
# Push healthy-meals-page-2026.html to Elementor (Healthy Meals page).
# Copy elementor-html/.healthy-meals-page-element-id.example.json to
# elementor-html/.healthy-meals-page-element-id.json and set post_id + html_widget.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAP="$ROOT/elementor-html/.healthy-meals-page-element-id.json"
PY="$ROOT/scripts/elementor_mcp_push_html_widget.py"
if [[ ! -f "$MAP" ]]; then
  echo "Missing $MAP — copy .healthy-meals-page-element-id.example.json and fill post_id + html_widget." >&2
  exit 1
fi
POST_ID="${POST_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['post_id'])")}"
EL="${ELEMENT_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['html_widget'])")}"
exec "$PY" --post-id "$POST_ID" --element-id "$EL" --html "$ROOT/elementor-html/healthy-meals-page-2026.html"
