# Weekly Menu — 2026 design & data

This document ties the **Elementor HTML widget** (`elementor-html/weekly-menu-page-2026.html`) and **MU plugin** (`wordpress/wp-content/mu-plugins/tiffingrab-weekly-menu-rest.php`) to the live [Weekly Menu page](https://tiffingrab.ca/menu/).

## Visual narrative (design system)

- **Warmth + clarity:** Orange primary `#E37B3E`, greens `#2ECC71` / `#27AE60`, light surfaces `#FFF8F6`, peach panels `#FFF1EB` / `#F7E4DC`.
- **Typography:** Headlines **Manrope**; body **Work Sans** (same pattern as Contact 2026).
- **Geometry:** ~8–12px radius, comfortable spacing, hero card with dark field + gold-accent script line “Current weekly menu” and the **live menu image**.

## How content stays in sync with the old page

After `scripts/setup_weekly_menu_page_2026.py`, the public **`/menu/`** page (**post `1098`**) is a single HTML widget, while the previous Elementor layout lives on a separate published page (**“Weekly Menu — Data”**, e.g. post **`11118`**) that staff edit each week. The REST route **`GET /wp-json/tiffingrab/v1/weekly-menu`** reads **`_elementor_data`** from **`TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID`** (clone page) and returns:

| Field | Source on `/menu/` |
|--------|----------------------|
| `lede` | First long `text-editor` (intro under “Our Weekly Menu”) |
| `heading_raw` / `date_line` | `heading` widget whose title matches “Weekly Menu …” |
| `image_url` | **`image` widget URL(s)** first (the weekly graphic); avoids Woo product thumbs from the UE grid |
| `pdf_url` | First `.pdf` link in buttons or HTML on the data page; if none, **`TIFFINGRAB_WEEKLY_MENU_DEFAULT_PDF_URL`** in `tiffingrab-weekly-menu-rest.php` (currently [Tiffingrab-Menu.pdf](https://tiffingrab.ca/wp-content/uploads/2026/04/Tiffingrab-Menu.pdf)) |
| `plans_title` | Heading matching “Explore … Tiffin … Plans” |
| `plans_lede` | Second `text-editor` or copy matching plan/lifestyle keywords |
| `plans_cta_url` / `plans_cta_label` | First non-PDF Elementor **button** (e.g. View All Plans), else `/tiffin-plans/` |

The widget calls that endpoint (or `window.TIFFINGRAB_WEEKLY_MENU.url` from `wp_footer` on the menu page) and fills the intro, dates, image, download CTA, and plans strip—**no second place to edit** weekly copy for those fields.

**Note:** The WooCommerce / Unlimited Elements **product grid** on the classic menu page is not duplicated inside this HTML block (it depends on UE/Woo runtime). The 2026 block links visitors to **Tiffin plans** with the same title and body copy Elementor already stores. Live product cards remain on `/tiffin-plans/`.

## Deploy checklist

1. Copy **`tiffingrab-weekly-menu-rest.php`** to production `wp-content/mu-plugins/`.
2. Push **`weekly-menu-page-2026.html`** into the menu page’s HTML widget (`scripts/push-weekly-menu-2026-to-elementor.sh` after creating `elementor-html/.weekly-menu-page-element-id.json` from the example file).
3. If WordPress ever recreates `/menu/` or the data clone, update **`TIFFINGRAB_WEEKLY_MENU_PUBLIC_PAGE_ID`** (HTML shell) and **`TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID`** (Elementor fields the API reads) in the MU plugin.

## QA

- Open `/menu/` with the new widget: image should match the Elementor **image** widget, dates should match the “Weekly Menu – …” heading, intro/plans text should match the two **text-editor** blocks.
- “View All Plans” should match the Elementor button target.
- With no PDF in Elementor, the primary CTA should still open the full-size menu image (same behaviour as before when only a graphic is published).
