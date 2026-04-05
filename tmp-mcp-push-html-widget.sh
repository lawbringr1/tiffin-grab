#!/usr/bin/env bash
# Push an HTML file into an Elementor HTML widget via elementor-mcp (macOS / Linux).
# Same behavior as tmp-mcp-push-html-widget.ps1 — no PowerShell required.
#
# Usage:
#   ./tmp-mcp-push-html-widget.sh <post_id> <element_id> <path/to/file.html>
#
# Example:
#   ./tmp-mcp-push-html-widget.sh 10297 24caf9c elementor-html/tiffin-plans-listing-editorial-2026.html

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <post_id> <element_id> <path/to.html>" >&2
  exit 1
fi

exec python3 "$ROOT/scripts/elementor_mcp_push_html_widget.py" \
  --post-id "$1" \
  --element-id "$2" \
  --html "$3"
