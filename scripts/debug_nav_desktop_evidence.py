#!/usr/bin/env python3
"""Runtime evidence for desktop UE navbar visibility — writes NDJSON session logs."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / ".cursor" / "debug-2aa4cd.log"
SESSION_ID = "2aa4cd"
RUN_ID = "desktop-nav-evidence"

# Mirrors site-header-navbar-2026.css @media (min-width:768px) UE-root + :not(id) toggle rules — injected to verify fix pre-deploy.
PATCH_UE_NAV_ROOT_CSS = """
@media (min-width: 768px) {
  .elementor-1863 .elementor-element-ef53437 .elementor-element-39bbf37 [id^="uc_nav_menu_elementor_"].ue-nav-menu {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: center !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-width: 0 !important;
    max-width: 100% !important;
    flex: 1 1 auto !important;
    pointer-events: auto !important;
  }
  .elementor-1863 .elementor-element-ef53437 .elementor-element-39bbf37 .ue-left-open:not([id^="uc_nav_menu_elementor_"]),
  .elementor-1863 .elementor-element-ef53437 .elementor-element-39bbf37 .ue-left-close:not([id^="uc_nav_menu_elementor_"]),
  .elementor-1863 .elementor-element-ef53437 .elementor-element-39bbf37 .elementor-menu-toggle {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
  }
}
"""

PROBE_JS = """() => {
  const root = document.querySelector('[id^="uc_nav_menu_elementor_"]');
  const ul = document.querySelector('[id^="uc_nav_menu_elementor_"] ul.ue-menu');
  const header = document.querySelector('header.elementor-location-header');

  function ancestry(el, depthLimit = 12) {
    if (!el) return [];
    const chain = [];
    let cur = el;
    while (cur && chain.length < depthLimit) {
      const cs = window.getComputedStyle(cur);
      const r = cur.getBoundingClientRect();
      chain.push({
        tag: cur.tagName,
        id: cur.id || '',
        cls:
          typeof cur.className === 'string'
            ? cur.className.slice(0, 160)
            : '',
        display: cs.display,
        visibility: cs.visibility,
        opacity: cs.opacity,
        overflowX: cs.overflowX,
        overflowY: cs.overflowY,
        width_px: Math.round(r.width * 100) / 100,
        height_px: Math.round(r.height * 100) / 100,
      });
      cur = cur.parentElement;
    }
    return chain;
  }

  function summarizeUl(UlEl, lbl) {
    if (!UlEl) return null;
    const cs = window.getComputedStyle(UlEl);
    const r = UlEl.getBoundingClientRect();
    return {
      label: lbl,
      display: cs.display,
      visibility: cs.visibility,
      opacity: cs.opacity,
      pointerEvents: cs.pointerEvents,
      transform: cs.transform,
      position: cs.position,
      width_px: Math.round(r.width * 100) / 100,
      height_px: Math.round(r.height * 100) / 100,
      li_count: UlEl.querySelectorAll(':scope > li').length,
      first_a_text:
        (UlEl.querySelector('a') && UlEl.querySelector('a').textContent) || '',
      ancestry: ancestry(UlEl),
    };
  }

  let ulViaHeaderSelector = null;
  if (header) {
    const u = header.querySelector('ul.ue-menu');
    if (u) ulViaHeaderSelector = summarizeUl(u, 'header ul.ue-menu');
  }

  const ulViaRoot = summarizeUl(ul, 'document root ue ul.ue-menu');

  let rulesTouchingUeMenuOpacity = [];
  try {
    for (const sheet of document.styleSheets) {
      let rules;
      try {
        rules = sheet.cssRules;
      } catch (e) {
        continue;
      }
      if (!rules) continue;
      for (let i = 0; i < Math.min(rules.length, 5000); i++) {
        const rule = rules[i];
        const text = rule && rule.cssText ? rule.cssText : '';
        if (text.includes('uc_nav_menu_elementor') && text.includes('.ue-menu') && text.includes('opacity')) {
          rulesTouchingUeMenuOpacity.push(text.slice(0, 380));
          if (rulesTouchingUeMenuOpacity.length >= 12) break;
        }
      }
      if (rulesTouchingUeMenuOpacity.length >= 12) break;
    }
  } catch (_) {}

  return {
    rootId: root ? root.id : null,
    rootClasses: root && root.className,
    ulViaRoot,
    ulViaHeaderSelector,
    ueOpacityRuleSamples: rulesTouchingUeMenuOpacity,
  };
}"""

# Hypotheses H6–H9: white circle = checkbox, label[for], .ue-nav-menu-mobile label::before, drawer toggle, etc.
CIRCLE_ARTIFACT_JS = """() => {
  const root = document.querySelector('[id^="uc_nav_menu_elementor_"]');
  if (!root) return { error: 'no_ue_root' };

  function brief(el) {
    const cs = window.getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {
      tag: el.tagName,
      type: el.getAttribute('type') || '',
      id: el.id || '',
      cls: typeof el.className === 'string' ? el.className.slice(0, 140) : '',
      w: Math.round(r.width * 100) / 100,
      h: Math.round(r.height * 100) / 100,
      top: Math.round(r.top * 100) / 100,
      left: Math.round(r.left * 100) / 100,
      display: cs.display,
      visibility: cs.visibility,
      opacity: cs.opacity,
      bg: cs.backgroundColor,
      br: cs.borderRadius,
      border: cs.borderWidth + ' ' + cs.borderStyle + ' ' + cs.borderColor.split(' ').slice(0, 5).join(' '),
      content: cs.content && cs.content !== 'none' ? cs.content.slice(0, 40) : '',
    };
  }

  const directChildren = [...root.children].map((el, idx) => ({ order: idx, ...brief(el) }));

  const candidates = [];
  const inputs = root.querySelectorAll('input, label');
  inputs.forEach((el) => candidates.push({ reason: 'input_or_label', ...brief(el) }));

  root.querySelectorAll('*').forEach((el) => {
    if (el === root) return;
    const cs = window.getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const bw = parseFloat(cs.borderTopWidth) || 0;
    const brPix = cs.borderRadius;
    const circular =
      brPix.includes('%') ||
      (/px/.test(brPix) && parseFloat(brPix.split('px')[0] || '0') > 14);
    const smallish = r.width >= 12 && r.width <= 64 && r.height >= 12 && r.height <= 64;
    const pale =
      /^rgb/.test(cs.backgroundColor) &&
      (cs.backgroundColor.includes('255') || cs.backgroundColor.includes('rgb(255'));

    const hasVisible =
      cs.visibility !== 'hidden' &&
      cs.display !== 'none' &&
      parseFloat(cs.opacity || '1') > 0.05 &&
      r.width > 1 &&
      r.height > 1;

    const looksLikeChip =
      hasVisible &&
      smallish &&
      (circular || el.tagName === 'INPUT') &&
      (pale || el.tagName === 'INPUT');

    if (looksLikeChip) candidates.push({ reason: 'rounded_or_white_chip', ...brief(el) });
  });

  return { directChildren, candidatesTail: candidates.slice(0, 24) };
}"""

# H7: circle from ::before/::after (list markers, UC icons, Elementor chrome)
PSEUDO_PROBE_JS = """() => {
  function pseudo(el, name) {
    if (!el) return null;
    try {
      const cs = window.getComputedStyle(el, name);
      return {
        pseudo: name,
        display: cs.display,
        content: cs.content,
        width: cs.width,
        height: cs.height,
        opacity: cs.opacity,
        bg: cs.backgroundColor,
        br: cs.borderRadius,
        boxShadow: (cs.boxShadow && cs.boxShadow !== 'none') ? cs.boxShadow.slice(0, 80) : 'none',
      };
    } catch (e) {
      return { pseudo: name, error: String(e) };
    }
  }

  const root = document.querySelector('[id^="uc_nav_menu_elementor_"]');
  const ueWidget = document.querySelector('.elementor-element-21c3db0.elementor-widget-ucaddon_nav_menu');
  const navCol = document.querySelector('.elementor-element-39bbf37');
  const ul = document.querySelector('[id^="uc_nav_menu_elementor_"] ul.ue-menu');

  const targets = [
    { key: 'ue_root', el: root },
    { key: 'ue_widget_21c3db0', el: ueWidget },
    { key: 'nav_col_39bbf37', el: navCol },
    { key: 'ul_ue_menu', el: ul },
  ];

  const out = {};
  targets.forEach(({ key, el }) => {
    if (!el) {
      out[key] = null;
      return;
    }
    out[key] = {
      tag: el.tagName,
      id: el.id || '',
      cls: typeof el.className === 'string' ? el.className.slice(0, 100) : '',
      before: pseudo(el, '::before'),
      after: pseudo(el, '::after'),
    };
  });
  return out;
}"""


def emit(hypothesis_id: str, message: str, data: dict) -> None:
    # #region agent log
    payload = {
        "sessionId": SESSION_ID,
        "runId": RUN_ID,
        "hypothesisId": hypothesis_id,
        "timestamp": int(time.time() * 1000),
        "location": "scripts/debug_nav_desktop_evidence.py",
        "message": message,
        "data": data,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.open("a", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False) + "\n")
    # #endregion agent log


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        emit(
            "H0_TOOLING",
            "Playwright not installed",
            {"hint": "pip install playwright && python -m playwright install chromium"},
        )
        return 2

    args = [a for a in sys.argv[1:] if a != "--verify-patch"]
    verify_patch = "--verify-patch" in sys.argv[1:]
    url = args[0] if args else "https://tiffingrab.ca/"
    viewport_w = int(args[1]) if len(args) > 1 else 1440
    viewport_h = int(args[2]) if len(args) > 2 else 900

    emit(
        "H_NAV_PROBE_START",
        "Starting playwright probe",
        {
            "url": url,
            "viewport": {"width": viewport_w, "height": viewport_h},
            "verify_patch": verify_patch,
        },
    )

    def probe_and_log(phase: str) -> dict:
        root_present = page.evaluate("""() => !!document.querySelector('[id^="uc_nav_menu_elementor_"]')""")
        emit("H4_DOM_ROOT", f"UE widget root exists? ({phase})", {"present": root_present, "phase": phase})
        detail = page.evaluate(PROBE_JS)
        emit("H_STYLE_DETAILS", f"Computed styles & ancestry ({phase})", {"phase": phase, **detail})
        ul = detail.get("ulViaRoot") or {}
        ov = ul.get("opacity")
        emit(
            "H1_OPACITY_ZERO",
            f"Primary ul opacity ({phase})",
            {
                "phase": phase,
                "opacity": ov,
                "confirmed_opacity_blocked": ov is not None and float(str(ov)) < 1,
            },
        )
        emit(
            "H2_DISPLAY",
            f"Primary ul display ({phase})",
            {"phase": phase, "display": ul.get("display"), "looks_hidden": ul.get("display") in {"none"}},
        )
        box_w = ul.get("width_px")
        box_h = ul.get("height_px")
        emit(
            "H3_DIMENSIONS",
            f"Bounding box ({phase})",
            {
                "phase": phase,
                "width_px": box_w,
                "height_px": box_h,
                "zero_box": box_w == 0 or box_h == 0,
            },
        )
        root_chain = (ul.get("ancestry") or [])[1] if len(ul.get("ancestry") or []) > 1 else None
        emit(
            "H5_UE_ROOT_DISPLAY",
            f"Parent #uc_nav_menu_* computed display ({phase})",
            {
                "phase": phase,
                "parent_div_display": root_chain.get("display") if root_chain else None,
                "parent_div_visibility": root_chain.get("visibility") if root_chain else None,
                "parent_div_id": root_chain.get("id") if root_chain else None,
            },
        )
        return detail

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": viewport_w, "height": viewport_h})
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=45000)

        probe_and_log("baseline")

        artifact = page.evaluate(CIRCLE_ARTIFACT_JS)
        emit("H6_CIRCLE_ARTIFACT", "UE root children + checkbox/rounded chip scan", artifact)

        pseudo = page.evaluate(PSEUDO_PROBE_JS)
        emit("H7_PSEUDO_ELEMENTS", "::before/::after on nav nodes", pseudo)

        if verify_patch:
            page.add_style_tag(content=PATCH_UE_NAV_ROOT_CSS)
            probe_and_log("after_injected_patch")

        browser.close()

    emit("H_NAV_PROBE_END", "Playwright probe complete", {"exit": "ok", "verify_patch": verify_patch})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
