#!/usr/bin/env bash
# Push Home 2026 repo HTML + hero button-row CSS to Elementor via elementor-mcp.
# Requires .cursor/mcp.json with elementor-mcp Authorization.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/scripts/elementor_mcp_push_html_widget.py"

# Template "Home 2026 Hero" (embedded on Home 2026 page)
"$PY" --post-id 9825 --element-id 4fd2df8 --html "$ROOT/elementor-html/home-2026-hero-tags.html"
"$PY" --post-id 9825 --element-id a2cdc57 --custom-css "$ROOT/elementor-html/home-2026-hero-button-row.css"

# Page "Home 2026" (post 10016)
"$PY" --post-id 10016 --element-id 7b9fa4e5 --html "$ROOT/elementor-html/service-area-delivery.html"
"$PY" --post-id 10016 --element-id 7d59786 --html "$ROOT/elementor-html/why-choose-us.html"
"$PY" --post-id 10016 --element-id 69d903a6 --html "$ROOT/elementor-html/who-its-perfect-for.html"
"$PY" --post-id 10016 --element-id 6b8b3925 --html "$ROOT/elementor-html/common-questions-faq.html"

echo "Done. Purge LiteSpeed / Elementor cache on the server if needed."
