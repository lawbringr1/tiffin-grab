# Hosting and third-party performance (TiffinGrab)

Use this checklist alongside the code in `wp-content/mu-plugins/tg-performance.php` and the Elementor/HTML updates in the main repo.

## TTFB / document latency (~2s in Lighthouse)

- **Page cache:** Enable Hostinger / LiteSpeed / Cloudflare full-page cache for anonymous HTML. Purge after deploys.
- **PHP:** Use PHP 8.2+ with **OPcache** enabled.
- **Object cache:** Consider Redis if many plugins (WooCommerce + Elementor + Site Kit).
- **Plugins:** Disable Site Kit modules you do not use (each module adds JS). Audit Query Monitor on staging for slow queries.

## Google Site Kit (long critical-path chains)

- In **Site Kit**, turn off modules you do not need (e.g. AdSense if unused, extra Analytics features).
- Prefer a single **delay / defer JS** strategy (Hostinger cache plugin, WP Rocket, or Flying Scripts) and test checkout and analytics after enabling.
- Do not defer `jquery` or WooCommerce cart scripts on cart/checkout without testing.

## Google Tag Manager (`GT-P3JPFHLH`) and reflow

- In **GTM**, load non-essential tags on **Window Loaded** or **DOM Ready** instead of as early as possible.
- Review tags that read layout (`offsetWidth`, etc.); reduce custom HTML tags that run synchronously on first paint.

## Legacy JavaScript (Lighthouse “Legacy JavaScript”)

Third-party bundles (for example Facebook `fbevents.js` or AWS S3 `clientParamBuilder.bundle.js`) ship polyfills you cannot strip from this repo. Mitigations:

- Fire those tags **after** `window.load` or via a **delay JS** plugin so they do not compete with LCP.
- Remove or consolidate tags you no longer need (duplicate pixels, unused CAPI helpers).

## Deploying the MU plugin

1. Copy `wordpress/wp-content/mu-plugins/tg-performance.php` to the live server at the same path under your WordPress root.
2. MU plugins load automatically; no activation step.
3. Clear all caches and re-run Lighthouse on `https://tiffingrab.ca/home-2026/`.

## Verification

- DevTools → Network: confirm **preconnect** count dropped (after HTML widget dedupe deploy).
- Elements panel: hero LCP `<img>` shows `fetchpriority="high"` and `loading="eager"`.
- Lighthouse: re-check LCP, Font display (eicons), and TTFB after caching is on.
