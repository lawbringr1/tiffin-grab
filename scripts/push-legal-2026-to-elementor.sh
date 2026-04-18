#!/usr/bin/env bash
# Push legal hub + policy HTML to Elementor using widget IDs from setup_legal_elementor_2026.py.
#
# Prereq: run `python3 scripts/setup_legal_elementor_2026.py` once to create
# elementor-html/.legal-element-ids.json (or maintain IDs manually).
#
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAP="$ROOT/elementor-html/.legal-element-ids.json"
PY="$ROOT/scripts/elementor_mcp_push_html_widget.py"

if [[ ! -f "$MAP" ]]; then
  echo "Missing $MAP — run: python3 scripts/setup_legal_elementor_2026.py" >&2
  exit 1
fi

HUB_POST=$(python3 -c "import json; print(json.load(open('$MAP'))['legal_hub']['post_id'])")
HUB_EL=$(python3 -c "import json; print(json.load(open('$MAP'))['legal_hub']['html_widget'])")
"$PY" --post-id "$HUB_POST" --element-id "$HUB_EL" --html "$ROOT/elementor-html/legal-hub-index-2026.html"

for key in terms privacy refund delivery; do
  POST=$(python3 -c "import json; print(json.load(open('$MAP'))['$key']['post_id'])")
  SHELL=$(python3 -c "import json; print(json.load(open('$MAP'))['$key']['shell_widget'])")
  MAIN=$(python3 -c "import json; print(json.load(open('$MAP'))['$key']['content_widget'])")
  "$PY" --post-id "$POST" --element-id "$SHELL" --html "$ROOT/elementor-html/legal-shell-2026.html"
  "$PY" --post-id "$POST" --element-id "$MAIN" --html "$ROOT/elementor-html/legal-content-${key}-2026.html"
done

echo "Legal pages push complete."
