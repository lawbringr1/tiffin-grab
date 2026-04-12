<?php
/**
 * Plugin Name: TiffinGrab Performance (MU)
 * Description: Front-end tweaks for Lighthouse: Elementor eicons font-display, LCP hero img hints, optional emoji removal.
 * Version: 1.0.4
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Home 2026 page (body.elementor-page-10016). */
const TG_PERF_HOME_2026_PAGE_ID = 10016;

/** Hero LCP asset (substring match so minor URL differences still work). */
const TG_PERF_LCP_IMG_FRAGMENT = 'Maharaja-Thali';

/** Elementor self-hosted Google Fonts got stuck pointing at the wrong domain. */
const TG_PERF_OLD_FONT_HOST = 'foodmonks.ca';

/**
 * Inline @font-face after Elementor’s eicons stylesheet so font-display: swap applies (Lighthouse “Font display”).
 */
add_action(
	'wp_enqueue_scripts',
	static function () {
		if ( is_admin() ) {
			return;
		}
		if ( ! defined( 'ELEMENTOR_FILE' ) || ! defined( 'ELEMENTOR_PATH' ) ) {
			return;
		}
		if ( ! wp_style_is( 'elementor-icons', 'registered' ) ) {
			return;
		}
		$rel = 'assets/lib/eicons/fonts/eicons.woff2';
		$file = ELEMENTOR_PATH . $rel;
		if ( ! is_readable( $file ) ) {
			return;
		}
		$font_url = plugins_url( $rel, ELEMENTOR_FILE );
		$css      = '@font-face{font-family:eicons;font-style:normal;font-weight:400;font-display:swap;src:url('
			. esc_url( $font_url ) . ') format("woff2");}';
		wp_add_inline_style( 'elementor-icons', $css );
	},
	25
);

/**
 * Preload LCP image on Home 2026 (complements fetchpriority on the tag).
 */
add_action(
	'wp_head',
	static function () {
		if ( is_admin() || ! function_exists( 'is_page' ) || ! is_page( TG_PERF_HOME_2026_PAGE_ID ) ) {
			return;
		}
		$url = content_url( '/uploads/2025/02/Maharaja-Thali-Non-veg.webp' );
		printf(
			'<link rel="preload" as="image" href="%s" fetchpriority="high" />' . "\n",
			esc_url( $url )
		);
	},
	1
);

/**
 * Elementor bypasses wp_content_img_tag for many widgets — patch the first hero thali <img> in the final HTML.
 *
 * @param string $html Full document.
 * @return string
 */
function tg_perf_patch_lcp_img_tag( $html ) {
	if ( ! is_string( $html ) || $html === '' ) {
		return $html;
	}

	// Fix 404s for Elementor self-hosted Google Fonts URLs pointing to a previous domain.
	// If the same files exist under tiffingrab.ca, rewriting these URLs resolves the issue.
	$newPrefix = rtrim( home_url(), '/' ) . '/wp-content/uploads/elementor/google-fonts/';
	$html      = str_replace(
		'https://' . TG_PERF_OLD_FONT_HOST . '/wp-content/uploads/elementor/google-fonts/',
		$newPrefix,
		$html
	);
	$html      = str_replace(
		'http://' . TG_PERF_OLD_FONT_HOST . '/wp-content/uploads/elementor/google-fonts/',
		$newPrefix,
		$html
	);

	// If LCP fragment isn't present, avoid unnecessary work.
	if ( strpos( $html, TG_PERF_LCP_IMG_FRAGMENT ) === false ) {
		return $html;
	}

	return (string) preg_replace_callback(
		'/<img\b[^>]*' . preg_quote( TG_PERF_LCP_IMG_FRAGMENT, '/' ) . '[^>]*>/i',
		static function ( $m ) {
			$tag = $m[0];
			// 1) Ensure fetchpriority="high"
			if ( preg_match( '/\sfetchpriority\s*=\s*["\']/i', $tag ) ) {
				$tag = preg_replace(
					'/\sfetchpriority\s*=\s*["\'][^"\']*["\']/i',
					' fetchpriority="high"',
					$tag,
					1
				);
			} else {
				$tag = preg_replace( '/^<img\b/i', '<img fetchpriority="high"', $tag, 1 );
			}

			// 2) Ensure loading="eager" (replace lazy if present, otherwise inject)
			if ( preg_match( '/\sloading\s*=\s*["\']lazy["\']/i', $tag ) ) {
				$tag = preg_replace( '/\sloading\s*=\s*["\']lazy["\']/i', ' loading="eager"', $tag, 1 );
			} elseif ( ! preg_match( '/\sloading\s*=\s*["\']/i', $tag ) ) {
				$tag = preg_replace( '/^<img\b/i', '<img loading="eager"', $tag, 1 );
			}

			return $tag;
		},
		$html,
		1
	);
}

add_action(
	'template_redirect',
	static function () {
		if ( is_admin() || ! function_exists( 'is_page' ) || ! is_page( TG_PERF_HOME_2026_PAGE_ID ) ) {
			return;
		}
		ob_start( 'tg_perf_patch_lcp_img_tag' );
	},
	99999
);

/**
 * Reinforce LCP attributes when WordPress filters post content (WP 6.4+).
 */
add_filter(
	'wp_content_img_tag',
	static function ( $tag, $context, $attachment_id ) {
		if ( ! is_string( $tag ) || $tag === '' ) {
			return $tag;
		}
		if ( strpos( $tag, TG_PERF_LCP_IMG_FRAGMENT ) === false ) {
			return $tag;
		}
		// fetchpriority="high"
		if ( preg_match( '/\sfetchpriority\s*=\s*["\']/i', $tag ) ) {
			$tag = preg_replace(
				'/\sfetchpriority\s*=\s*["\'][^"\']*["\']/i',
				' fetchpriority="high"',
				$tag,
				1
			);
		} else {
			$tag = preg_replace( '/^<img\b/i', '<img fetchpriority="high"', $tag, 1 );
		}

		// loading="eager"
		if ( preg_match( '/\sloading\s*=\s*["\']lazy["\']/i', $tag ) ) {
			$tag = preg_replace( '/\sloading\s*=\s*["\']lazy["\']/i', ' loading="eager"', $tag, 1 );
		} elseif ( ! preg_match( '/\sloading\s*=\s*["\']/i', $tag ) ) {
			$tag = preg_replace( '/^<img\b/i', '<img loading="eager"', $tag, 1 );
		}

		return $tag;
	},
	10,
	3
);

/**
 * Skip core emoji scripts/styles on the front.
 */
add_action(
	'init',
	static function () {
		if ( is_admin() ) {
			return;
		}
		remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
		remove_action( 'wp_print_styles', 'print_emoji_styles' );
		remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
		remove_action( 'admin_print_styles', 'print_emoji_styles' );
	},
	100
);
