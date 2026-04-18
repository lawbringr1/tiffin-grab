<?php
/**
 * Plugin Name: TiffinGrab Weekly Menu REST
 * Description: Public GET /wp-json/tiffingrab/v1/weekly-menu — reads the same Elementor Weekly Menu page (post 1098, /menu/) as staff already update: hero copy, date heading, menu image widget, optional PDF, plans CTA.
 * Version: 1.1.2
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Public Weekly Menu URL (/menu/) — HTML shell lives here. */
const TIFFINGRAB_WEEKLY_MENU_PUBLIC_PAGE_ID = 1098;

/**
 * Elementor “source” page ID whose `_elementor_data` the REST route parses (image, headings, text, PDF).
 * After `scripts/setup_weekly_menu_page_2026.py` runs, this points at the cloned “Weekly Menu — Data” page.
 * Until then, keep the same as the public page ID.
 */
const TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID = 11118;

/**
 * @param string $html
 */
function tiffingrab_weekly_menu_plain_text( string $html ): string {
	$t = wp_strip_all_tags( $html, true );
	$t = preg_replace( '/\s+/u', ' ', $t );
	return is_string( $t ) ? trim( $t ) : '';
}

/**
 * @param string $url
 */
function tiffingrab_weekly_menu_url_is_logo( string $url ): bool {
	return (bool) preg_match( '/logo|cropped-Tiffin-Grab-Site-LOGO|32x32|150x150|192x192|180x180|270x270/i', $url );
}

/**
 * WooCommerce / UE grid product thumbs on the menu page — not the weekly menu graphic.
 *
 * @param string $url
 */
function tiffingrab_weekly_menu_url_is_product_thumb( string $url ): bool {
	return (bool) preg_match(
		'/Trial-meal|Maharaja-Thali|Sabzi-only|8oz-|tiffin-service|product[_-]/i',
		$url
	);
}

/**
 * @param list<string> $urls
 */
function tiffingrab_weekly_menu_pick_menu_image_url( array $urls ): string {
	$urls = array_values(
		array_unique(
			array_filter(
				array_map(
					static function ( string $u ): string {
						return esc_url_raw( $u );
					},
					$urls
				)
			)
		)
	);
	$urls = array_values(
		array_filter(
			$urls,
			static function ( string $u ): bool {
				return $u !== '' && ! tiffingrab_weekly_menu_url_is_logo( $u ) && ! tiffingrab_weekly_menu_url_is_product_thumb( $u );
			}
		)
	);
	if ( array() === $urls ) {
		return '';
	}
	foreach ( $urls as $u ) {
		if ( stripos( $u, 'whatsapp' ) !== false ) {
			return $u;
		}
	}
	usort(
		$urls,
		static function ( string $a, string $b ): int {
			return strlen( $b ) <=> strlen( $a );
		}
	);
	return $urls[0] ?? '';
}

/**
 * @param mixed $nodes
 * @param array<string, mixed> $acc
 */
function tiffingrab_weekly_menu_walk_elementor( $nodes, array &$acc, string &$html_blob ): void {
	if ( ! is_array( $nodes ) ) {
		return;
	}
	foreach ( $nodes as $node ) {
		if ( ! is_array( $node ) ) {
			continue;
		}
		$el_type = isset( $node['elType'] ) ? (string) $node['elType'] : '';
		$widget  = isset( $node['widgetType'] ) ? (string) $node['widgetType'] : '';
		$st      = isset( $node['settings'] ) && is_array( $node['settings'] ) ? $node['settings'] : array();

		if ( 'widget' === $el_type && 'image' === $widget ) {
			$url = '';
			if ( isset( $st['image'] ) && is_array( $st['image'] ) && ! empty( $st['image']['url'] ) ) {
				$url = (string) $st['image']['url'];
			}
			if ( $url !== '' && ! tiffingrab_weekly_menu_url_is_logo( $url ) ) {
				$acc['image_widget_urls'][] = $url;
			}
		}

		if ( 'widget' === $el_type && 'heading' === $widget && ! empty( $st['title'] ) ) {
			$title = tiffingrab_weekly_menu_plain_text( (string) $st['title'] );
			if ( $title !== '' ) {
				$acc['headings'][] = $title;
				if ( preg_match( '/weekly\s*menu/i', $title ) ) {
					$acc['heading_weekly'] = $title;
				}
			}
		}

		if ( 'widget' === $el_type && 'text-editor' === $widget && ! empty( $st['editor'] ) ) {
			$plain = tiffingrab_weekly_menu_plain_text( (string) $st['editor'] );
			if ( $plain !== '' && strlen( $plain ) > 24 ) {
				$acc['text_blocks'][] = $plain;
			}
			$html_blob .= ' ' . (string) $st['editor'];
		}

		if ( 'widget' === $el_type && 'html' === $widget && ! empty( $st['html'] ) ) {
			$html_blob .= ' ' . (string) $st['html'];
		}

		if ( 'widget' === $el_type && 'button' === $widget && ! empty( $st['link']['url'] ) ) {
			$u = (string) $st['link']['url'];
			if ( preg_match( '/\.pdf(\?|$)/i', $u ) ) {
				$acc['pdfs'][] = $u;
			} else {
				$label = '';
				if ( isset( $st['text'] ) ) {
					$label = tiffingrab_weekly_menu_plain_text( (string) $st['text'] );
				}
				$acc['buttons'][] = array(
					'url'   => $u,
					'label' => $label,
				);
			}
		}

		if ( ! empty( $node['elements'] ) ) {
			tiffingrab_weekly_menu_walk_elementor( $node['elements'], $acc, $html_blob );
		}
	}
}

/**
 * @return array<string, mixed>
 */
function tiffingrab_weekly_menu_parse_elementor_json( string $raw ): array {
	$data = json_decode( $raw, true );
	if ( JSON_ERROR_NONE !== json_last_error() ) {
		$data = json_decode( wp_unslash( $raw ), true );
	}
	$acc = array(
		'image_widget_urls' => array(),
		'headings'          => array(),
		'heading_weekly'    => '',
		'text_blocks'       => array(),
		'pdfs'              => array(),
		'buttons'           => array(),
	);
	$html_blob = '';
	if ( is_array( $data ) ) {
		tiffingrab_weekly_menu_walk_elementor( $data, $acc, $html_blob );
	}

	$scraped_images = array();
	$scraped_pdfs   = array();
	if ( $html_blob !== '' ) {
		if ( preg_match_all( '/https?:\/\/[^\s\"\'<>()]+\.(?:jpe?g|png|webp)(?:\?[^\s\"\'<>()]*)?/i', $html_blob, $m ) ) {
			foreach ( $m[0] as $u ) {
				if ( ! tiffingrab_weekly_menu_url_is_logo( $u ) ) {
					$scraped_images[] = $u;
				}
			}
		}
		if ( preg_match_all( '/https?:\/\/[^\s\"\'<>()]+\.pdf(?:\?[^\s\"\'<>()]*)?/i', $html_blob, $m2 ) ) {
			foreach ( $m2[0] as $p ) {
				$scraped_pdfs[] = $p;
			}
		}
	}

	return array(
		'acc'             => $acc,
		'scraped_images'  => $scraped_images,
		'scraped_pdfs'    => $scraped_pdfs,
	);
}

/**
 * @param list<string> $pdfs
 */
function tiffingrab_weekly_menu_pick_pdf( array $pdfs ): string {
	$pdfs = array_values( array_unique( array_filter( array_map( 'esc_url_raw', $pdfs ) ) ) );
	return $pdfs[0] ?? '';
}

/**
 * @param array<string, mixed> $parsed
 * @return array<string, mixed>|WP_Error
 */
function tiffingrab_weekly_menu_build_payload_from_parsed( array $parsed, string $raw_meta ): array {
	$acc = $parsed['acc'];

	$image = tiffingrab_weekly_menu_pick_menu_image_url( $acc['image_widget_urls'] );
	if ( $image === '' ) {
		$merged = array_merge( $acc['image_widget_urls'], $parsed['scraped_images'] );
		$image   = tiffingrab_weekly_menu_pick_menu_image_url( $merged );
	}
	if ( $image === '' && preg_match_all( '/https?:\/\/[^\s\"\'<>()]+\/wp-content\/uploads\/[^\s\"\'<>()]+\.(?:jpe?g|png|webp)/i', $raw_meta, $fallback ) ) {
		$image = tiffingrab_weekly_menu_pick_menu_image_url( $fallback[0] );
	}

	$pdfs = array_merge( $acc['pdfs'], $parsed['scraped_pdfs'] );
	$pdf  = tiffingrab_weekly_menu_pick_pdf( $pdfs );

	$heading_weekly = (string) ( $acc['heading_weekly'] ?? '' );
	$date_line      = '';
	if ( $heading_weekly !== '' ) {
		$date_line = preg_replace( '/^\s*weekly\s*menu\s*-\s*/i', '', $heading_weekly );
		$date_line = is_string( $date_line ) ? trim( $date_line ) : '';
	}

	$lede = '';
	foreach ( $acc['text_blocks'] as $block ) {
		if ( strlen( $block ) < 60 ) {
			continue;
		}
		if ( preg_match( '/^home\s*\/\s*weekly\s*menu/i', $block ) ) {
			continue;
		}
		if ( preg_match( '/explore\s+our\s+tiffin\s+plans/i', $block ) ) {
			continue;
		}
		$lede = $block;
		break;
	}

	$plans_title = '';
	foreach ( $acc['headings'] as $h ) {
		if ( preg_match( '/explore.*tiffin.*plan/i', $h ) ) {
			$plans_title = $h;
			break;
		}
	}
	if ( $plans_title === '' ) {
		$plans_title = __( 'Explore Our Tiffin Plans', 'tiffingrab' );
	}

	$plans_lede = '';
	foreach ( $acc['text_blocks'] as $block ) {
		if ( $block === $lede ) {
			continue;
		}
		if ( strlen( $block ) < 50 ) {
			continue;
		}
		if ( preg_match( '/popular\s+tiffin|every\s+lifestyle|student|professional|family/i', $block ) ) {
			$plans_lede = $block;
			break;
		}
	}
	if ( $plans_lede === '' && isset( $acc['text_blocks'][1] ) ) {
		$plans_lede = (string) $acc['text_blocks'][1];
	}

	$plans_url   = home_url( '/tiffin-plans/' );
	$plans_label = __( 'View All Plans', 'tiffingrab' );
	foreach ( $acc['buttons'] as $btn ) {
		$u = isset( $btn['url'] ) ? (string) $btn['url'] : '';
		if ( $u === '' || preg_match( '/\.pdf(\?|$)/i', $u ) ) {
			continue;
		}
		$plans_url = esc_url_raw( $u );
		if ( ! empty( $btn['label'] ) ) {
			$plans_label = (string) $btn['label'];
		}
		break;
	}

	return array(
		'image_url'       => $image,
		'image_alt'       => __( 'Current weekly menu', 'tiffingrab' ),
		'heading_raw'     => $heading_weekly,
		'date_line'       => $date_line,
		'pdf_url'         => $pdf,
		'lede'            => $lede,
		'plans_title'     => $plans_title,
		'plans_lede'      => $plans_lede,
		'plans_cta_url'   => $plans_url,
		'plans_cta_label' => $plans_label,
		'source_id'       => TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID,
		'public_page_id'  => TIFFINGRAB_WEEKLY_MENU_PUBLIC_PAGE_ID,
		'source_path'     => '/menu/',
	);
}

/**
 * @return array<string, mixed>|WP_Error
 */
function tiffingrab_weekly_menu_build_payload(): array {
	$post = get_post( TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID );
	if ( ! $post || 'publish' !== $post->post_status ) {
		return new WP_Error( 'tiffingrab_weekly_menu_missing', __( 'Weekly menu source is not available.', 'tiffingrab' ), array( 'status' => 404 ) );
	}

	$raw = get_post_meta( TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID, '_elementor_data', true );
	if ( ! is_string( $raw ) || $raw === '' ) {
		return new WP_Error( 'tiffingrab_weekly_menu_no_elementor', __( 'Weekly menu layout data is missing.', 'tiffingrab' ), array( 'status' => 500 ) );
	}

	$parsed = tiffingrab_weekly_menu_parse_elementor_json( $raw );
	return tiffingrab_weekly_menu_build_payload_from_parsed( $parsed, $raw );
}

add_action(
	'rest_api_init',
	static function (): void {
		register_rest_route(
			'tiffingrab/v1',
			'/weekly-menu',
			array(
				'methods'             => 'GET',
				'permission_callback' => '__return_true',
				'callback'            => static function () {
					$post = get_post( TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID );
					if ( ! $post ) {
						return new WP_Error( 'tiffingrab_weekly_menu_missing', __( 'Weekly menu source is not available.', 'tiffingrab' ), array( 'status' => 404 ) );
					}
					$ver = (string) get_post_modified_time( 'U', true, $post );
					$key = 'tg_wm_v1_' . TIFFINGRAB_WEEKLY_MENU_SOURCE_POST_ID . '_' . $ver;
					$cached = get_transient( $key );
					if ( is_array( $cached ) ) {
						return rest_ensure_response( $cached );
					}
					$payload = tiffingrab_weekly_menu_build_payload();
					if ( is_wp_error( $payload ) ) {
						return $payload;
					}
					set_transient( $key, $payload, 5 * MINUTE_IN_SECONDS );
					return rest_ensure_response( $payload );
				},
			)
		);
	}
);

add_action(
	'wp_footer',
	static function (): void {
		if ( is_admin() ) {
			return;
		}
		if ( ! function_exists( 'is_page' ) ) {
			return;
		}
		if ( ! is_page( TIFFINGRAB_WEEKLY_MENU_PUBLIC_PAGE_ID ) && ! is_page( 'menu' ) ) {
			return;
		}
		$payload = array(
			'url' => rest_url( 'tiffingrab/v1/weekly-menu' ),
		);
		echo '<script>window.TIFFINGRAB_WEEKLY_MENU=' . wp_json_encode( $payload ) . ';</script>' . "\n";
	},
	5
);
