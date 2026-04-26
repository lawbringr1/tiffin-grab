#!/usr/bin/env python3
"""
Download WordPress page `content.rendered` from the public REST API into elementor-html/.

Use for pages built with the block editor (e.g. WooCommerce cart) where there is no single
Elementor HTML widget in this repo. Re-run after you change the page in WP admin.

Example:
  python3 scripts/pull-wp-page-content.py --slug cart
  python3 scripts/pull-wp-page-content.py --post-id 1343
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "elementor-html"


def fetch_page_json(base: str, *, slug: str | None, post_id: int | None) -> dict:
    if post_id is not None:
        url = f"{base.rstrip('/')}/wp-json/wp/v2/pages/{post_id}"
    elif slug is not None:
        url = f"{base.rstrip('/')}/wp-json/wp/v2/pages?slug={urllib.parse.quote(slug)}"
    else:
        raise ValueError("Need --slug or --post-id")
    req = urllib.request.Request(url, headers={"User-Agent": "tiffin-grab-pull-wp-content/1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, list):
        if not data:
            sys.exit("No page returned for that slug.")
        return data[0]
    return data


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="https://tiffingrab.ca", help="WordPress site base URL")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--slug", help="Page slug, e.g. cart")
    g.add_argument("--post-id", type=int, help="Page ID, e.g. 1343")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output path (default: elementor-html/<slug or id>-page-content.html)",
    )
    args = p.parse_args()

    page = fetch_page_json(args.base_url, slug=args.slug, post_id=args.post_id)
    pid = int(page["id"])
    slug = page.get("slug") or f"page-{pid}"
    title = page.get("title", {}).get("rendered", "")
    modified = page.get("modified", "")
    link = page.get("link", "")
    html = (page.get("content") or {}).get("rendered") or ""

    out = args.output
    if out is None:
        safe = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
        out = OUT_DIR / f"{safe}-page-content.html"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"""<!--
  PULL SNAPSHOT (WordPress `post_content` rendered HTML, public REST)
  source:  {args.base_url.rstrip("/")}/wp-json/wp/v2/pages/{pid}
  page_id:  {pid}
  slug:     {slug}
  title:    {title}
  link:     {link}
  modified: {modified} (from API)
  pulled:   {when}
  note:     Cart/checkout pages may use WooCommerce blocks; not the same as elementor-mcp
            HTML widget pushes. Edit in WP or copy sections into a custom template as needed.
-->

"""
    out.write_text(header + html + "\n", encoding="utf-8")
    meta = {
        "post_id": pid,
        "slug": slug,
        "title": title,
        "link": link,
        "modified": modified,
        "output_file": str(out.relative_to(ROOT)),
        "rest_url": f"{args.base_url.rstrip('/')}/wp-json/wp/v2/pages/{pid}",
    }
    meta_path = OUT_DIR / f".{safe}-page-wp.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(html)} chars body)")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
