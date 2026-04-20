#!/usr/bin/env bash
# Push Home 2026 repo HTML + hero button-row CSS to Elementor via elementor-mcp.
# Requires .cursor/mcp.json with elementor-mcp Authorization.
#
# The visible homepage uses Theme Builder single template 1589 (wrapper for page 10016).
# Hero is embedded from page 10016 (shortcode → template 9825), not duplicated as native widgets on 1589.
# Optional: bundled widget updates on 1589 (usually empty — see home-2026-single-page-template-1589-widgets.json).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/scripts/elementor_mcp_push_html_widget.py"
BUNDLE_PY="$ROOT/scripts/elementor_mcp_push_widgets_bundle.py"

python3 "$BUNDLE_PY" "$ROOT/elementor-html/home-2026-single-page-template-1589-widgets.json"

# Template "Home 2026 Hero" (embedded on Home 2026 page)
python3 "$PY" --post-id 9825 --element-id 4fd2df8 --html "$ROOT/elementor-html/home-2026-hero-tags.html"
python3 "$PY" --post-id 9825 --element-id a2cdc57 --custom-css "$ROOT/elementor-html/home-2026-hero-button-row.css"

# Page "Home 2026" (post 10016)
python3 "$PY" --post-id 10016 --element-id 7b9fa4e5 --html "$ROOT/elementor-html/service-area-delivery.html"
python3 "$PY" --post-id 10016 --element-id 7d59786 --html "$ROOT/elementor-html/why-choose-us.html"
python3 "$PY" --post-id 10016 --element-id 69d903a6 --html "$ROOT/elementor-html/who-its-perfect-for.html"
python3 "$PY" --post-id 10016 --element-id 6b8b3925 --html "$ROOT/elementor-html/common-questions-faq.html"

echo "Done. Purge LiteSpeed / Elementor cache on the server if needed."
