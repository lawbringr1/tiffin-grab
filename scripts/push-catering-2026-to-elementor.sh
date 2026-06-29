#!/usr/bin/env bash
# Push catering-page-2026.html to the existing Catering Elementor page.
# Idempotent: setup_catering_page_2026.py updates the HTML widget when the map exists.
# TLS: system python lacks CA certs, so pin SSL_CERT_FILE.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAP="$ROOT/elementor-html/.catering-page-element-id.json"
if [[ ! -f "$MAP" ]]; then
  echo "Missing $MAP — run: SSL_CERT_FILE=/etc/ssl/cert.pem python3 scripts/setup_catering_page_2026.py" >&2
  exit 1
fi
exec env SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/ssl/cert.pem}" python3 "$ROOT/scripts/setup_catering_page_2026.py"
