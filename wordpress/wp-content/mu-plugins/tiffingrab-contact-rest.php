<?php
/**
 * Plugin Name: TiffinGrab Contact REST
 * Description: Public POST /wp-json/tiffingrab/v1/contact — validates nonce, rate-limits, sends wp_mail to info@tiffingrab.ca. Exposes window.TIFFINGRAB_CONTACT on the Contact page for the Elementor HTML form.
 * Version: 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** WordPress page ID for “Contact us” (Elementor). Update if the page is recreated. */
const TIFFINGRAB_CONTACT_PAGE_ID = 562;

/** Nonce action for the contact form (must match JS). */
const TIFFINGRAB_CONTACT_NONCE_ACTION = 'tiffingrab_contact_v1';

/**
 * @param string $ip
 */
function tiffingrab_contact_rate_limited( string $ip ): bool {
	$key = 'tg_ct_' . md5( $ip );
	if ( get_transient( $key ) ) {
		return true;
	}
	set_transient( $key, 1, 30 );
	return false;
}

/**
 * @param array<string, mixed> $params
 * @return string|WP_Error
 */
function tiffingrab_contact_handle( array $params ) {
	$nonce = isset( $params['nonce'] ) ? (string) $params['nonce'] : '';
	if ( ! wp_verify_nonce( $nonce, TIFFINGRAB_CONTACT_NONCE_ACTION ) ) {
		return new WP_Error( 'tiffingrab_contact_bad_nonce', __( 'Invalid security token. Please reload the page.', 'tiffingrab' ), array( 'status' => 403 ) );
	}

	// Honeypot — bots often fill hidden “website”.
	if ( ! empty( $params['website'] ) ) {
		return new WP_Error( 'tiffingrab_contact_spam', __( 'Could not send message.', 'tiffingrab' ), array( 'status' => 400 ) );
	}

	$ip = isset( $_SERVER['REMOTE_ADDR'] ) ? (string) $_SERVER['REMOTE_ADDR'] : '';
	if ( $ip !== '' && tiffingrab_contact_rate_limited( $ip ) ) {
		return new WP_Error( 'tiffingrab_contact_rate', __( 'Please wait a moment before sending again.', 'tiffingrab' ), array( 'status' => 429 ) );
	}

	$name = isset( $params['name'] ) ? sanitize_text_field( (string) $params['name'] ) : '';
	$email = isset( $params['email'] ) ? sanitize_email( (string) $params['email'] ) : '';
	$message = isset( $params['message'] ) ? sanitize_textarea_field( (string) $params['message'] ) : '';
	$topics = isset( $params['topics'] ) && is_array( $params['topics'] ) ? array_map( 'sanitize_text_field', $params['topics'] ) : array();

	if ( $name === '' || $email === '' || ! is_email( $email ) || $message === '' ) {
		return new WP_Error( 'tiffingrab_contact_fields', __( 'Please fill in your name, a valid email, and a message.', 'tiffingrab' ), array( 'status' => 400 ) );
	}

	$to = 'info@tiffingrab.ca';
	$subject = '[TiffinGrab Contact] ' . ( $topics ? implode( ', ', $topics ) : 'General' );

	$body_lines = array(
		'Name: ' . $name,
		'Email: ' . $email,
		'Topics: ' . ( $topics ? implode( ', ', $topics ) : '(none)' ),
		'',
		$message,
		'',
		'— Sent from tiffingrab.ca contact form',
	);
	if ( $ip !== '' ) {
		$body_lines[] = 'IP: ' . $ip;
	}

	$headers = array(
		'Content-Type: text/plain; charset=UTF-8',
		'Reply-To: ' . $name . ' <' . $email . '>',
	);

	$sent = wp_mail( $to, $subject, implode( "\n", $body_lines ), $headers );
	if ( ! $sent ) {
		return new WP_Error( 'tiffingrab_contact_mail', __( 'Could not send message. Please try again or email us directly.', 'tiffingrab' ), array( 'status' => 500 ) );
	}

	return array( 'success' => true );
}

add_action(
	'rest_api_init',
	static function (): void {
		register_rest_route(
			'tiffingrab/v1',
			'/contact',
			array(
				'methods'             => 'POST',
				'permission_callback' => '__return_true',
				'callback'            => static function ( WP_REST_Request $request ) {
					$params = $request->get_json_params();
					if ( ! is_array( $params ) ) {
						$params = array();
					}
					$result = tiffingrab_contact_handle( $params );
					if ( is_wp_error( $result ) ) {
						return $result;
					}
					return rest_ensure_response( $result );
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
		if ( ! is_page( TIFFINGRAB_CONTACT_PAGE_ID ) && ! is_page( 'contact-us' ) && ! is_page( 'contact' ) ) {
			return;
		}
		$payload = array(
			'url'   => rest_url( 'tiffingrab/v1/contact' ),
			'nonce' => wp_create_nonce( TIFFINGRAB_CONTACT_NONCE_ACTION ),
		);
		echo '<script>window.TIFFINGRAB_CONTACT=' . wp_json_encode( $payload ) . ';</script>' . "\n";
	},
	5
);
