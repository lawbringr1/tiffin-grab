#!/usr/bin/env bash
# Push contact-us-page-2026.html to Elementor (post 562 by default).
# Run scripts/setup_contact_page_2026.py first to create .contact-page-element-id.json.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAP="$ROOT/elementor-html/.contact-page-element-id.json"
PY="$ROOT/scripts/elementor_mcp_push_html_widget.py"
POST_ID="${POST_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['post_id'])")}"
EL="${ELEMENT_ID:-$(python3 -c "import json; print(json.load(open('$MAP'))['html_widget'])")}"
exec "$PY" --post-id "$POST_ID" --element-id "$EL" --html "$ROOT/elementor-html/contact-us-page-2026.html"
