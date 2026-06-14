## Learned User Preferences

- After editing `elementor-html/` markup or CSS, push live via Elementor MCP (`scripts/push-*-to-elementor.sh` or `scripts/elementor_mcp_push_*.py`), not only git.
- Match site-wide CTA/button styling to the home “Why Choose Our Tiffin Service Across the GTA?” pill button (reference section in repo HTML).
- On mobile, use simple buttons without arrow/slide animations; keep animated pill buttons on desktop.
- Hero and section headings should use bold Geist (700), not thin/light weights.
- Elementor Free only: use WPCode (or similar) for `<head>` font snippets; do not rely on Elementor Pro Custom Code.
- Do not load Geist and Material Symbols from both WPCode `<head>` and Elementor kit `@import` (duplicate requests cause FOUT and Lighthouse noise).
- Mobile nav should use the bottom dock pattern and stay stable across page loads (no full reload flicker).

## Learned Workspace Facts

- `elementor-html/` is the source of truth for Elementor HTML/CSS; deploy with `scripts/elementor_mcp_push_*.py` and `scripts/push-*-to-elementor.sh`.
- Elementor MCP endpoint: `https://tiffingrab.ca/wp-json/mcp/elementor-mcp-server`; credentials in `.cursor/mcp.json` (`elementor-mcp`); follow-up calls require `Mcp-Session-Id`.
- Default Kit custom CSS: post **591** (`elementor-kit-global-custom-css.css`); Geist loads from WPCode `elementor-head-geist-preload-snippet.html`, not kit `@import`.
- Theme Builder header post **1863**; navbar CSS in `site-header-navbar-2026.css` via `scripts/elementor_mcp_push_header_css.py`; inline HTML widget **b706311** (`elementor-html/header-navbar-inline-element.id`).
- Canonical WhatsApp meal-plans URL: `elementor-html/tg-whatsapp-meal-plans.url`; floating beacon and mobile dock ship with the header push script.
- Home 2026 page **10016**; hero library template **9825** (HTML widget **4fd2df8**); Theme Builder single wrapper **1589**; footer template **1907**.
- `scripts/push-home-2026-to-elementor.sh` also applies `home-9825-whatsapp-button-link.json`; `scripts/push-whatsapp-links-to-elementor.sh` runs footer, home, contact, referral, and legal WhatsApp pushes.
- LiteSpeed “Font Display Optimization” should stay **Default** (not Swap) to reduce Geist bold-then-light flash with variable fonts.
- Healthy Meals page **13039** (`/healthy-meals/`, published); HTML widget **a4fc580**, container **bb1ed53**; source `elementor-html/healthy-meals-page-2026.html`, push `scripts/push-healthy-meals-2026-to-elementor.sh`, sidecar `.healthy-meals-page-element-id.json`. Section 4 lists WC **Store API** products in category slug `healthy-meals` (recreate the category + add products to populate). Old "Healthy Meals" page **6581** (slug `healthy-meals-home`) was trashed 2026-06-14.
- Header promo banner (`.tg-referral-banner-link`, header 1863) is **currently disabled** (removed on request 2026-06-14): the inject block in `elementor_mcp_push_header_css.py` removes any existing strip, and the navbar CSS sets it `display:none`. The green Healthy Meals launch copy + restore snippet are kept in the script comment. To bring back referral or a promo, re-enable both the JS create block and the CSS `display`.
- Healthy Meals page primary color is **green `#34C363`** (not site orange): `--hm-primary` is green and the sitewide `tg-h26-btn--primary` pill is overridden green scoped to `#tg-healthy-2026`.
- Push the header script with the uv graphify python (`graphify-out/.graphify_python`), which has working TLS; system `python3` fails CA verification.
- Header is a **floating pill** navbar (2026 revamp, bottom of `site-header-navbar-2026.css`): header location is a transparent sticky wrapper; the active nav row (`ef53437` desktop / `67924b6` mobile) is a centered rounded pill with blur + shadow + side gaps. Pure CSS so it paints with the document (no JS layout shift). To add a "Healthy Meals" nav link later, add it to the Ultimate Addons nav menu widget `21c3db0` (do NOT add yet, per request).
- **LiteSpeed Cache defers inline JS** site-wide (console logs `[LiteSpeed] Start Lazy Load`). Inline `<script>` in Elementor HTML widgets does NOT run until first user interaction. Never gate visible content behind JS: the Healthy Meals page reveal was switched from IntersectionObserver to **CSS scroll-driven animation** (`animation-timeline: view()`, gated by `@supports`, content visible by default) after JS-delay left every `[data-reveal]` stuck at `opacity:0`. The Store API meal showcase + flip-card JS are also delayed (skeleton shows until interaction); fine since LiteSpeed fires JS on first scroll/touch and no products exist yet.
- Writing `_elementor_data` via WP REST meta alone does NOT render on the frontend — Elementor needs a real save to regen assets. After a REST data write, trigger one `elementor-mcp` update (e.g. `update-element` on the container) to force render. The `scripts/elementor_mcp_push_*.py` path fails locally with `SSL: CERTIFICATE_VERIFY_FAILED` (system python lacks CA certs); use the elementor-mcp tools directly until certs are fixed.
