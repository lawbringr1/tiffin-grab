# Healthy Meals Landing Page — Design Spec

**Date:** 2026-06-14
**Status:** Approved (sections + color); awaiting meal data for Section 4
**Owner:** lawbringr

## Goal

New marketing landing page for a "Healthy Meals" offering on tiffingrab.ca. Editorial,
conversion-focused, matching the existing TiffinGrab 2026 design language. The live
product **listing** (WooCommerce Healthy Meals items) is a separate, later step — this
page markets the offering and showcases sample meals.

## Design Language (inherited)

Source of truth: `elementor-html/tiffin-plans-listing-editorial-2026.html`.

- **Surface:** `#fef8f3` (warm cream) · **cards:** `#ffffff` · **panel:** `#fff3e8`
- **Primary orange:** `#f06b1a` · mid `#d3540f` · on-primary `#ffffff`
- **Nutrition accent (NEW):** `#34C363` green — used for the Nutrition/Goals band
  (Section 5), macro bars, and "healthy" badges on meal cards. Used as an accent only;
  orange remains the primary brand/CTA color.
- **Text:** on `#1d1b19` · muted `#5c5854` · outline `#e0c0b4`
- **Font:** Geist (display + body), bold (700) headings — never thin. Loaded via existing
  WPCode head snippet, not Elementor kit `@import` (avoid duplicate font requests / FOUT).
- **Layout:** full-bleed `100vw` breakout only at `min-width: 1200px`; vw-clip safety on
  mobile/tablet (`overflow-x: clip`) to prevent horizontal scroll — copy the guard CSS
  pattern from the listing page.
- **CTAs:** pill buttons matching the home "Why Choose Our Tiffin Service" reference.
  Desktop = animated pill; mobile = simple button, no arrow/slide animation.

## Page Structure

Single Elementor HTML widget, scoped under a unique root id (e.g. `#tg-healthy-2026`),
following the self-contained `<section><style>…</style>…</section>` pattern.

| # | Section | Content | Accent |
|---|---------|---------|--------|
| 1 | **Hero** | Bold H1 ("Healthy Meals, Built for Your Goals"), subcopy, primary pill CTA → order (WhatsApp meal-plans URL / plans page), trust tags (calorie-counted · fresh-cooked · GTA delivery) | orange |
| 2 | **Why Healthy Meals** | 3–4 benefit cards: macro-balanced, portion-controlled, chef + nutrition-minded, zero prep | orange |
| 3 | **How It Works** | 3-step row: choose your meals → we cook fresh daily → delivered to your door | orange |
| 4 | **Meal Showcase** | Responsive grid of meal cards, **dynamically pulled from WooCommerce** (see Data Source below). Each card: product image, name, short description, price, "Order" link. Optional macro chips (kcal / protein / carbs / fat) if stored as product meta/attributes, rendered green | green chips |
| 5 | **Nutrition / Goals band** | Weight-loss / muscle-gain / balanced angle on a green-tinted panel; reinforces the health positioning | **green `#34C363`** |
| 6 | **Final CTA** | Pill button band → order, matching site CTA | orange |

## Data Source — Section 4 (dynamic)

Meals are added as **WooCommerce products** (later step), then the page lists them live.

- **API:** WooCommerce **Store API** — `GET /wp-json/wc/store/v1/products?category=<slug-or-id>`.
  Public, unauthenticated, CORS-safe, designed for browser use. **No admin
  app-password / consumer keys in client JS.**
- **Filter:** a dedicated "Healthy Meals" product **category** (recreate it during the
  listing step — it was deleted on 2026-06-14). Category slug drives the query.
- **Card fields:** `name`, `images[0].src`, `prices.price` (+ currency minor-unit),
  `short_description`, `permalink` → "Order". Macro chips read from product attributes
  or meta if present; otherwise omitted.
- **States:** loading skeleton → rendered grid → graceful empty state ("Fresh healthy
  meals coming soon") when zero products. Network error → quiet fallback message.
- **Build now:** Section 4 ships with the fetch wired + a skeleton/empty state, so the
  page is complete and self-populates the moment products are published. A few static
  demo cards may be shown behind a flag for layout review only.

## Deploy Workflow

Match the existing per-page pattern (weekly-menu / contact / referral):

1. New markup file: `elementor-html/healthy-meals-page-2026.html`
2. New WordPress page "Healthy Meals 2026" (status **draft** first for review).
3. Element-id sidecar: `elementor-html/.healthy-meals-page-element-id.json`
   (gitignored values; `.example.json` committed).
4. Push script: `scripts/push-healthy-meals-2026-to-elementor.sh` → wraps
   `scripts/elementor_mcp_push_html_widget.py`, using `.cursor/mcp.json` elementor-mcp creds.
5. Geist/Material fonts already loaded site-wide via WPCode — do not re-import.

## Out of Scope (later step)

- Creating the WooCommerce Healthy Meals products themselves.
- Recreating the "Healthy Meals" product category (was deleted 2026-06-14) — required
  before Section 4 shows anything; do it when adding products.
- Real meal photography.

## Resolved Decisions

- **Hero + final CTA target:** canonical WhatsApp meal-plans URL
  (`elementor-html/tg-whatsapp-meal-plans.url`).
- **Store API verified live** on tiffingrab.ca (public, no auth). Prices in minor units.

## Open Items

- Category vs. tag for filtering (default: category, slug `healthy-meals`) — finalize in
  the listing/products step.
