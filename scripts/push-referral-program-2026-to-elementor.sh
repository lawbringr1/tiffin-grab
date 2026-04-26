#!/usr/bin/env bash
# Push referral-program-2026.html to Elementor (map from setup_referral_program_page_2026.py).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAP="$ROOT/elementor-html/.referral-program-page-element-id.json"
PY="$ROOT/scripts/elementor_mcp_push_html_widget.py"
if [[ ! -f "$MAP" ]]; then
  echo "Missing $MAP — run: python3 scripts/setup_referral_program_page_2026.py" >&2
  exit 1
fi
POST_ID="${POST_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['post_id'])")}"
EL="${ELEMENT_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['html_widget'])")}"
exec "$PY" --post-id "$POST_ID" --element-id "$EL" --html "$ROOT/elementor-html/referral-program-2026.html"
