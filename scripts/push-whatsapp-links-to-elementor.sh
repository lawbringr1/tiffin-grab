#!/usr/bin/env bash
# Push all repo snippets that contain WhatsApp CTAs + hero native button link (9825).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT/scripts/push-footer-2026-to-elementor.sh"
"$ROOT/scripts/push-home-2026-to-elementor.sh"
"$ROOT/scripts/push-contact-2026-to-elementor.sh"
"$ROOT/scripts/push-referral-program-2026-to-elementor.sh"
"$ROOT/scripts/push-legal-2026-to-elementor.sh"

echo "WhatsApp link push complete."
