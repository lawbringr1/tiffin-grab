#!/usr/bin/env python3
"""
Push TiffinGrab navbar CSS for the Theme Builder **header** template (default post **1863**).

1. **Custom CSS on the header library post** — `elementor-mcp-add-custom-css` so Elementor stores
   rules on the header template (what you edit in Theme Builder).

2. **Inline `<style>` in an HTML widget (recommended)** — rules are output **inside the header
   markup**, so they apply on every page that uses this header (including new home pages), even
   when LiteSpeed combines CSS or omits `post-1863.css` from the `<head>`.

Optional: merge the same navbar CSS into the **Default Kit** (post 591) with `--kit-post-id 591`
if you also want kit-level copies (not required when the inline widget is used).

Requires `.cursor/mcp.json` with `mcpServers.elementor-mcp` url + Authorization.

Examples:
  python3 scripts/elementor_mcp_push_header_css.py
  python3 scripts/elementor_mcp_push_header_css.py --create-inline-widget
  python3 scripts/elementor_mcp_push_header_css.py --kit-post-id 591
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_BUILD_STAMP_RE = re.compile(r"^\s*/\* tg-header-build:[^\n]+?\*/\s*\n?")

KIT_NAV_BANNER = """
/*
  --- Header navbar (source: elementor-html/site-header-navbar-2026.css) ---
  Merged into Default Kit when --kit-post-id is set.
*/
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_mcp(mcp_path: Path) -> tuple[str, str]:
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    ec = data.get("mcpServers", {}).get("elementor-mcp")
    if not ec:
        sys.exit(f"No mcpServers.elementor-mcp in {mcp_path}")
    auth = (ec.get("headers") or {}).get("Authorization")
    url = ec.get("url")
    if not auth or not url:
        sys.exit("elementor-mcp missing url or headers.Authorization")
    return str(url).rstrip("/"), auth


def mcp_post(url: str, auth: str, body: dict, session_id: str | None, timeout: int = 120) -> tuple[dict[str, str], dict]:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", auth)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        raw = json.loads(resp.read().decode("utf-8"))
    return headers, raw


def mcp_initialize(base_url: str, auth: str) -> str:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "tiffin-grab-header-css", "version": "1"},
        },
    }
    headers, _ = mcp_post(base_url, auth, body, session_id=None, timeout=30)
    sid = headers.get("mcp-session-id")
    if not sid:
        sys.exit("MCP initialize did not return Mcp-Session-Id header.")
    return sid.strip()


def with_push_build_stamp(css: str) -> str:
    stripped = _BUILD_STAMP_RE.sub("", css, count=1)
    stamp = f"/* tg-header-build: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} */\n"
    return stamp + stripped.lstrip("\n")


TG_MOBILE_DOCK_VERSION = "tg-dock-v3"


def tg_mobile_dock_inner_html() -> str:
    """Anchors-only fragment (shared by SSR markup and JS fallback)."""
    base = (
        '<a class="tg-mobile-dock__item" href="https://tiffingrab.ca/">'
        '<span class="material-symbols-outlined tg-mobile-dock__icon" aria-hidden="true">home</span>'
        '<span class="tg-mobile-dock__label">Home</span></a>'
        '<a class="tg-mobile-dock__item" href="https://tiffingrab.ca/referral-program/">'
        '<span class="material-symbols-outlined tg-mobile-dock__icon" aria-hidden="true">card_giftcard</span>'
        '<span class="tg-mobile-dock__label">Referral</span></a>'
        '<a class="tg-mobile-dock__item" href="https://tiffingrab.ca/tiffin-plans/">'
        '<span class="material-symbols-outlined tg-mobile-dock__icon" aria-hidden="true">set_meal</span>'
        '<span class="tg-mobile-dock__label">Plans</span></a>'
        '<a class="tg-mobile-dock__item" href="https://tiffingrab.ca/menu/">'
        '<span class="material-symbols-outlined tg-mobile-dock__icon" aria-hidden="true">menu_book</span>'
        '<span class="tg-mobile-dock__label">Menu</span></a>'
        '<a class="tg-mobile-dock__item" href="https://tiffingrab.ca/contact-us/">'
        '<span class="material-symbols-outlined tg-mobile-dock__icon" aria-hidden="true">chat_bubble</span>'
        '<span class="tg-mobile-dock__label">Contact</span></a>'
    )
    return base


def wrap_inline_style(css: str) -> str:
    dock_inner_js = json.dumps(tg_mobile_dock_inner_html(), ensure_ascii=False)
    dock_nav_ssr = (
        "<nav "
        'class="tg-mobile-dock" '
        f'data-tg-dock-version="{TG_MOBILE_DOCK_VERSION}" '
        'aria-label="Mobile bottom navigation">'
        f"{tg_mobile_dock_inner_html()}</nav>"
    )
    script_tpl = """
<script id="tg-header-referral-banner-script">
(function () {
  var header = document.querySelector('header.elementor.elementor-1863.elementor-location-header, .elementor-location-header.elementor-1863');
  /*
    Promo banner link: create if missing, always sync copy/href. Kept as the last child of the
    header so it renders below Theme Builder navbar rows (desktop + mobile).
  */
  if (header) {
    var link = header.querySelector('.tg-referral-banner-link');
    if (!link) {
      link = document.createElement('a');
      link.className = 'tg-referral-banner-link';
      header.appendChild(link);
    } else if (link.parentNode === header && header.lastElementChild !== link) {
      header.appendChild(link);
    }
    link.href = 'https://tiffingrab.ca/tiffin-plans/';
    link.textContent = 'Use coupon code FREE4TIFFINS - Offer valid till 18th May.';
    link.setAttribute('aria-label', 'Tiffin plans: coupon FREE4TIFFINS. Valid till 18th May.');
  }

  /* Cart quantity badge on Elementor icon widgets that link to the cart page (not Menu Cart widget). */
  function tgIsCartPageHref(href) {
    if (!href) return false;
    try {
      var u = new URL(href, window.location.origin);
      var p = u.pathname || '/';
      while (p.length > 1 && p.charAt(p.length - 1) === '/') p = p.slice(0, -1);
      if (!p) p = '/';
      return p === '/cart' || p.endsWith('/cart');
    } catch (_e) {
      return false;
    }
  }

  function tgSumCartQty(data) {
    if (!data || !Array.isArray(data.items)) return 0;
    var t = 0;
    for (var i = 0; i < data.items.length; i++) {
      var q = data.items[i].quantity;
      t += typeof q === 'number' ? q : parseInt(q, 10) || 0;
    }
    return t;
  }

  function tgCartBadgeLabel(n) {
    if (n > 99) return '99+';
    return String(n);
  }

  function tgEnsureBadgeOnCartIcon(anchor) {
    var wrap = anchor.parentElement;
    if (!wrap || !wrap.classList.contains('elementor-icon-wrapper')) return null;
    wrap.classList.add('tg-cart-icon-wrap');
    var badge = wrap.querySelector('.tg-cart-count-badge');
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'tg-cart-count-badge';
      badge.setAttribute('aria-hidden', 'true');
      wrap.appendChild(badge);
    }
    return badge;
  }

  var tgCartBadgeTimer = null;
  function tgRefreshCartBadges() {
    var hdr =
      document.querySelector('header.elementor.elementor-1863.elementor-location-header') ||
      document.querySelector('.elementor-location-header.elementor-1863');
    if (!hdr) return;
    var anchors = hdr.querySelectorAll('a.elementor-icon[href]');
    var cartAnchors = [];
    anchors.forEach(function (a) {
      if (a.closest('.elementor-widget-woocommerce-menu-cart')) return;
      if (!tgIsCartPageHref(a.getAttribute('href'))) return;
      cartAnchors.push(a);
    });
    if (!cartAnchors.length) return;

    var cartJsonUrl = new URL('/wp-json/wc/store/v1/cart', window.location.origin).href;

    fetch(cartJsonUrl, {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    })
      .then(function (r) {
        return r.ok ? r.json() : null;
      })
      .then(function (data) {
        if (!data) return;
        var n = tgSumCartQty(data);
        cartAnchors.forEach(function (a) {
          var badge = tgEnsureBadgeOnCartIcon(a);
          if (!badge) return;
          if (!a.dataset.tgCartAriaDefault && a.getAttribute('aria-label')) {
            a.dataset.tgCartAriaDefault = a.getAttribute('aria-label');
          }
          if (n > 0) {
            badge.textContent = tgCartBadgeLabel(n);
            badge.setAttribute('data-tg-cart-visible', '1');
            a.setAttribute('aria-label', 'Cart, ' + n + (n === 1 ? ' item' : ' items'));
          } else {
            badge.textContent = '';
            badge.removeAttribute('data-tg-cart-visible');
            var def = a.dataset.tgCartAriaDefault;
            if (def) a.setAttribute('aria-label', def);
            else a.removeAttribute('aria-label');
          }
        });
      })
      .catch(function () {});
  }

  function tgScheduleCartBadgeRefresh() {
    if (tgCartBadgeTimer) clearTimeout(tgCartBadgeTimer);
    tgCartBadgeTimer = setTimeout(tgRefreshCartBadges, 200);
  }

  tgRefreshCartBadges();

  function tgBindCartBadgeListeners() {
    if (!document.body) return;
    try {
      if (window.jQuery) {
        window.jQuery(document.body).on('added_to_cart removed_from_cart', tgScheduleCartBadgeRefresh);
        window.jQuery(document.body).on('wc_fragment_refresh', tgScheduleCartBadgeRefresh);
      }
    } catch (_e) {}
    document.addEventListener('wc-blocks_added_to_cart', tgScheduleCartBadgeRefresh);
    window.addEventListener('load', tgScheduleCartBadgeRefresh);
    window.addEventListener('pageshow', function (e) {
      if (e.persisted) tgScheduleCartBadgeRefresh();
    });
  }
  tgBindCartBadgeListeners();

  function ensureMobileDock() {
    var isMobile = window.matchMedia('(max-width: 767px)').matches;
    var existing = document.querySelector('.tg-mobile-dock');
    if (!isMobile) {
      document.body.style.paddingBottom = '';
      /* Desktop hides .tg-mobile-dock via CSS — do NOT remove DOM (avoids teardown on every resize / paint). */
      return;
    }

    /* Upgrade path when markup revision changes */
    var DOCK_VERSION = __DOCK_VERSION__;
    if (existing && existing.getAttribute('data-tg-dock-version') !== DOCK_VERSION) {
      existing.remove();
      existing = null;
    }

    if (!existing) {
      var nav = document.createElement('nav');
      nav.className = 'tg-mobile-dock';
      nav.setAttribute('data-tg-dock-version', DOCK_VERSION);
      nav.setAttribute('aria-label', 'Mobile bottom navigation');
      nav.innerHTML = __DOCK_INNER_JSON__;
      document.body.appendChild(nav);
      existing = nav;
    }

    /* SSR nav sits in header widget DOM first — move once to body for reliable fixed/z-index layering */
    if (existing.parentNode !== document.body) {
      document.body.appendChild(existing);
    }

    var dock = document.querySelector('.tg-mobile-dock');
    /*
      Marker only: navigation is delegated in bindGlobalSingleTapNav() using composedPath + deferred assign.
      (Duplicate capture listeners on both document and dock used to confuse iOS event ordering.)
    */
    if (dock && !dock.dataset.tgBound) {
      dock.dataset.tgBound = '1';
    }

    var path = (window.location.pathname || '/').replace(/\/+$/, '') || '/';
    document.querySelectorAll('.tg-mobile-dock a').forEach(function (a) {
      var hrefPath = new URL(a.href, window.location.origin).pathname.replace(/\/+$/, '') || '/';
      if (hrefPath === path) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });

    document.body.style.paddingBottom = 'calc(4.15rem + env(safe-area-inset-bottom))';
  }

  function bindGlobalSingleTapNav() {
    if (document.documentElement.dataset.tgFastTapBound === '1') return;
    document.documentElement.dataset.tgFastTapBound = '1';

    /*
      Broad defaults: viewport-based phones/tablets plus any coarse pointer (covers odd Safari UA reporting).
      Handlers gate on actual touch-like pointer types / touchend so desktop mouse is unaffected.
    */
    function useFastTapChrome() {
      if (!window.matchMedia) return true;
      if (window.matchMedia('(max-width: 1024px)').matches) return true;
      if (
        window.matchMedia('(hover: none)').matches &&
        window.matchMedia('(any-pointer: coarse)').matches
      )
        return true;
      return false;
    }

    function shouldHandleAnchor(a) {
      if (!a || !a.getAttribute) return false;
      if (a.dataset && a.dataset.tgNoFasttap === '1') return false;
      if (a.hasAttribute('download')) return false;
      var href = (a.getAttribute('href') || '').trim();
      if (!href) return false;
      if (href === '#' || href.indexOf('javascript:') === 0) return false;
      return true;
    }

    /*
      Prefer composedPath(): fixes shadow-boundary / odd targeting where target.closest skips the link.
    */
    function anchorFromEvent(e) {
      var a = null;
      if (typeof e.composedPath === 'function') {
        var path = e.composedPath();
        for (var i = 0; i < path.length; i++) {
          var node = path[i];
          if (!node || !node.closest) continue;
          if (node.matches && node.matches('a[href]')) {
            a = node;
            break;
          }
        }
      }
      if (!a && e.target && e.target.closest) {
        a = e.target.closest('a[href]');
      }
      return a;
    }

    function assignNav(url) {
      /*
        Navigate in the same turn as the user gesture. Deferring with rAF can detach navigation
        from the tap on mobile WebKit and leave the next document visibly “idle” until a second tap.
      */
      window.location.assign(url);
    }

    var __tgLastNavUrl = '';
    var __tgLastNavAt = 0;

    function fastNavigate(e) {
      if (!useFastTapChrome()) return;
      /* Only emulate nav for real touch streams (mouse path keeps native click). */
      var isTouchEnded = e.type === 'touchend';
      var isPenOrTouchPointer =
        e.pointerType === 'touch' || e.pointerType === 'pen' || (!e.pointerType && isTouchEnded);
      if (!isPenOrTouchPointer) return;

      var a = anchorFromEvent(e);
      if (!shouldHandleAnchor(a)) return;
      /*
        Limit to Theme Builder header + our mobile dock only. A site-wide capture handler
        breaks accordions, block interactions, and third-party widgets (e.g. UC menus).
      */
      if (!a.closest('.elementor-location-header, .tg-mobile-dock')) return;
      var hrefRaw = (a.getAttribute('href') || '').trim();
      if (hrefRaw.charAt(0) === '#') return;

      if (document.documentElement.dataset.tgGoing === '1' || a.dataset.tgNavigating === '1') return;

      /* Same tap often emits pointerup then touchend (or reverse); collapse to one navigate. */
      var nowMs = typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now();
      var absUrl = '';
      try {
        absUrl = new URL(a.getAttribute('href'), window.location.href).href;
      } catch (_e) {
        absUrl = a.href;
      }
      if (absUrl && absUrl === __tgLastNavUrl && nowMs - __tgLastNavAt < 500) return;
      __tgLastNavUrl = absUrl;
      __tgLastNavAt = nowMs;

      a.dataset.tgNavigating = '1';
      document.documentElement.dataset.tgGoing = '1';
      window.setTimeout(function () {
        if (a.dataset) delete a.dataset.tgNavigating;
        delete document.documentElement.dataset.tgGoing;
      }, 1800);

      e.preventDefault();
      e.stopPropagation();

      var targetAttr = (a.getAttribute('target') || '').toLowerCase();
      if (targetAttr === '_blank') {
        delete document.documentElement.dataset.tgGoing;
        delete a.dataset.tgNavigating;
        window.open(a.href, '_blank', 'noopener,noreferrer');
        return;
      }
      assignNav(a.href);
    }

    document.addEventListener(
      'touchend',
      function (e) {
        fastNavigate(e);
      },
      { capture: true, passive: false }
    );
    document.addEventListener(
      'pointerup',
      function (e) {
        fastNavigate(e);
      },
      true
    );

    /*
      BFCache restore: anchors can retain stale tgNavigating; allow taps after back/forward.
    */
    window.addEventListener('pageshow', function () {
      document.querySelectorAll('a[data-tg-navigating]').forEach(function (el) {
        delete el.dataset.tgNavigating;
      });
      delete document.documentElement.dataset.tgGoing;
      __tgLastNavUrl = '';
      __tgLastNavAt = 0;
    });
  }

  ensureMobileDock();
  bindGlobalSingleTapNav();
  var mqlDock = window.matchMedia('(max-width: 767px)');
  function onDockBreakpoint() {
    ensureMobileDock();
  }
  if (mqlDock.addEventListener) {
    mqlDock.addEventListener('change', onDockBreakpoint);
  } else if (mqlDock.addListener) {
    mqlDock.addListener(onDockBreakpoint);
  }
  /* iOS address bar / orientation: debounce — avoid work on every intermediate resize frame */
  var dockResizeT = null;
  window.addEventListener(
    'resize',
    function () {
      if (dockResizeT) clearTimeout(dockResizeT);
      dockResizeT = setTimeout(ensureMobileDock, 120);
    },
    { passive: true }
  );
})();
</script>
"""
    script = (
        script_tpl.strip()
        .replace("__DOCK_VERSION__", json.dumps(TG_MOBILE_DOCK_VERSION))
        .replace("__DOCK_INNER_JSON__", dock_inner_js)
    )
    return (
        f'<style id="tg-header-navbar-rules">\n{css.rstrip()}\n</style>\n'
        f"{dock_nav_ssr}\n"
        f"{script}\n"
    )


def structured_from_result(raw: dict) -> dict:
    res = raw.get("result") or {}
    if res.get("isError"):
        txt = res.get("content", [{}])[0].get("text", str(res))
        sys.exit(f"MCP tool error: {txt[:2000]}")
    return res.get("structuredContent") or {}


def mcp_add_custom_css(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    post_id: int,
    css: str,
    replace: bool,
    rpc_id: int,
) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "tools/call",
        "params": {
            "name": "elementor-mcp-add-custom-css",
            "arguments": {"post_id": post_id, "css": css, "replace": replace},
        },
    }
    _h, raw = mcp_post(base_url, auth, body, session_id=session_id)
    if raw.get("error"):
        sys.exit(f"MCP error: {raw['error']}")
    structured_from_result(raw)
    return raw


def mcp_call_tool(
    base_url: str,
    auth: str,
    session_id: str,
    *,
    name: str,
    arguments: dict,
    rpc_id: int,
) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    _h, raw = mcp_post(base_url, auth, body, session_id=session_id)
    if raw.get("error"):
        sys.exit(f"MCP error: {raw['error']}")
    sc = structured_from_result(raw)
    return sc


def main() -> None:
    root = repo_root()
    default_nav = root / "elementor-html" / "site-header-navbar-2026.css"
    default_kit = root / "elementor-html" / "elementor-kit-global-custom-css.css"
    default_inline_id = root / "elementor-html" / "header-navbar-inline-element.id"
    default_mcp = root / ".cursor" / "mcp.json"

    p = argparse.ArgumentParser(description="Push Theme Builder header navbar CSS via Elementor MCP.")
    p.add_argument("--nav-css", type=Path, default=default_nav, help="Navbar CSS file path")
    p.add_argument("--kit-css", type=Path, default=default_kit, help="Kit CSS file (only if --kit-post-id set)")
    p.add_argument("--kit-post-id", type=int, default=0, help="Default Kit post ID (591). 0 = skip kit merge.")
    p.add_argument("--header-post-id", type=int, default=1863, help="Theme Builder header template post ID.")
    p.add_argument(
        "--inline-element-id-file",
        type=Path,
        default=default_inline_id,
        help="File containing one line: HTML widget element id for inline <style> (optional).",
    )
    p.add_argument(
        "--create-inline-widget",
        action="store_true",
        help="Add an HTML widget to the header (parent column 6b4ffdd) and save its id to --inline-element-id-file.",
    )
    p.add_argument(
        "--inline-parent-id",
        default="6b4ffdd",
        help="Elementor container data-id to attach new HTML widget (default: logo column on desktop row).",
    )
    p.add_argument(
        "--append",
        action="store_true",
        help="Append custom CSS instead of replace (default: replace).",
    )
    p.add_argument("--mcp-json", type=Path, default=default_mcp, help="Path to Cursor MCP config")
    args = p.parse_args()

    nav_path = args.nav_css.expanduser().resolve()
    kit_path = args.kit_css.expanduser().resolve()
    if not nav_path.is_file():
        sys.exit(f"Navbar CSS not found: {nav_path}")
    if args.kit_post_id and not kit_path.is_file():
        sys.exit(f"Kit CSS not found: {kit_path}")

    mcp_path = args.mcp_json.expanduser().resolve()
    if not mcp_path.is_file():
        sys.exit(f"MCP config not found: {mcp_path}")

    nav_stamped = with_push_build_stamp(nav_path.read_text(encoding="utf-8"))
    base_url, auth = load_mcp(mcp_path)
    session_id = mcp_initialize(base_url, auth)
    replace = not args.append
    rpc = 2

    if args.kit_post_id:
        kit_text = kit_path.read_text(encoding="utf-8").rstrip() + "\n"
        combined_kit = kit_text + KIT_NAV_BANNER + "\n" + nav_stamped + "\n"
        print(f"Pushing kit + navbar → kit post_id={args.kit_post_id} ...")
        mcp_add_custom_css(
            base_url,
            auth,
            session_id,
            post_id=args.kit_post_id,
            css=combined_kit,
            replace=replace,
            rpc_id=rpc,
        )
        rpc += 1

    print(f"Pushing navbar CSS → header template post_id={args.header_post_id} ...")
    mcp_add_custom_css(
        base_url,
        auth,
        session_id,
        post_id=args.header_post_id,
        css=nav_stamped,
        replace=replace,
        rpc_id=rpc,
    )
    rpc += 1

    id_file = args.inline_element_id_file.expanduser().resolve()
    if args.create_inline_widget:
        if id_file.is_file() and id_file.read_text(encoding="utf-8").strip():
            sys.exit(f"Refusing to create widget: {id_file.name} already has an id. Delete it or remove --create-inline-widget.")
        print(
            f"Creating HTML widget under parent {args.inline_parent_id!r} on post {args.header_post_id} ..."
        )
        sc = mcp_call_tool(
            base_url,
            auth,
            session_id,
            name="elementor-mcp-add-widget",
            arguments={
                "post_id": args.header_post_id,
                "parent_id": args.inline_parent_id,
                "widget_type": "html",
                "settings": {"html": "<!-- TiffinGrab navbar styles (updated by MCP) -->\n"},
            },
            rpc_id=rpc,
        )
        rpc += 1
        new_id = sc.get("element_id")
        if not new_id:
            sys.exit(f"add_widget did not return element_id: {sc}")
        id_file.parent.mkdir(parents=True, exist_ok=True)
        id_file.write_text(str(new_id).strip() + "\n", encoding="utf-8")
        print(f"Wrote element id to {id_file.relative_to(root)}: {new_id}")

    if id_file.is_file():
        element_id = id_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if element_id:
            print(f"Pushing inline <style> → HTML widget {element_id} on post {args.header_post_id} ...")
            mcp_call_tool(
                base_url,
                auth,
                session_id,
                name="elementor-mcp-update-widget",
                arguments={
                    "post_id": args.header_post_id,
                    "element_id": element_id,
                    "settings": {"html": wrap_inline_style(nav_stamped)},
                },
                rpc_id=rpc,
            )

    print(
        "\nDone. Header template holds the navbar; inline HTML widget (if configured) outputs "
        "styles with the header on every page using this theme location.\n"
        "After changes: Elementor → Tools → Regenerate CSS & Data, then purge LiteSpeed / Hostinger cache.\n"
    )


if __name__ == "__main__":
    main()
