<?php
/**
 * REST endpoint for Tally form webhooks (POST JSON).
 *
 * URL: https://yoursite.com/wp-json/tiffingrab/v1/tally-webhook
 *
 * In Tally: Integrations → Webhooks → set the endpoint URL above. Optionally enable a signing secret
 * and define TIFFINGRAB_TALLY_SIGNING_SECRET in wp-config.php (same value as in Tally).
 *
 * Handle submissions in your theme or a small mu-plugin:
 *
 *   add_action( 'tiffingrab_tally_form_response', function ( array $payload, WP_REST_Request $request ): void {
 *       $submission = $payload['data'] ?? array();
 *       // e.g. $submission['formId'], $submission['fields'], $submission['responseId']
 *   }, 10, 2 );
 *
 * Install: require_once in hello-elementor-child-v2/functions.php, or use as a mu-plugin.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_action(
	'rest_api_init',
	static function (): void {
		register_rest_route(
			'tiffingrab/v1',
			'/tally-webhook',
			array(
				'methods'             => 'POST',
				'callback'            => 'tiffingrab_tally_webhook_handle',
				'permission_callback' => 'tiffingrab_tally_webhook_permission_check',
			)
		);
	}
);

/**
 * @return true|WP_Error
 */
function tiffingrab_tally_webhook_permission_check( WP_REST_Request $request ) {
	$secret = tiffingrab_tally_webhook_signing_secret();
	if ( $secret === '' ) {
		return true;
	}

	$received = $request->get_header( 'tally-signature' );
	if ( $received === '' || $received === null ) {
		return new WP_Error(
			'tiffingrab_tally_no_signature',
			__( 'Missing Tally-Signature header.', 'tiffingrab' ),
			array( 'status' => 401 )
		);
	}

	$raw = $request->get_body();
	$expected = base64_encode( hash_hmac( 'sha256', $raw, $secret, true ) );

	if ( ! hash_equals( $expected, $received ) ) {
		return new WP_Error(
			'tiffingrab_tally_bad_signature',
			__( 'Invalid webhook signature.', 'tiffingrab' ),
			array( 'status' => 401 )
		);
	}

	return true;
}

function tiffingrab_tally_webhook_signing_secret(): string {
	if ( defined( 'TIFFINGRAB_TALLY_SIGNING_SECRET' ) && is_string( TIFFINGRAB_TALLY_SIGNING_SECRET ) ) {
		$secret = TIFFINGRAB_TALLY_SIGNING_SECRET;
	} else {
		$secret = '';
	}

	/**
	 * Signing secret must match the one configured in Tally’s webhook settings.
	 *
	 * @param string $secret Empty string means signature verification is skipped.
	 */
	return (string) apply_filters( 'tiffingrab_tally_webhook_signing_secret', $secret );
}

/**
 * @return WP_REST_Response|WP_Error
 */
function tiffingrab_tally_webhook_handle( WP_REST_Request $request ) {
	$raw = $request->get_body();
	if ( $raw === '' ) {
		return new WP_Error(
			'tiffingrab_tally_empty_body',
			__( 'Empty request body.', 'tiffingrab' ),
			array( 'status' => 400 )
		);
	}

	$data = json_decode( $raw, true );
	if ( ! is_array( $data ) ) {
		return new WP_Error(
			'tiffingrab_tally_invalid_json',
			__( 'Invalid JSON.', 'tiffingrab' ),
			array( 'status' => 400 )
		);
	}

	/**
	 * Fires for every valid Tally webhook JSON body.
	 *
	 * @param array              $data    Decoded JSON body.
	 * @param WP_REST_Request    $request REST request.
	 */
	do_action( 'tiffingrab_tally_webhook', $data, $request );

	$event_type = isset( $data['eventType'] ) ? (string) $data['eventType'] : '';
	$submission = isset( $data['data'] ) && is_array( $data['data'] ) ? $data['data'] : null;

	if ( $submission !== null && ( $event_type === 'FORM_RESPONSE' || $event_type === '' || isset( $submission['fields'] ) ) ) {
		/**
		 * Fires when the payload includes a form submission (`data` with typical Tally fields).
		 *
		 * @param array              $data    Full decoded JSON (eventId, eventType, createdAt, data, …).
		 * @param WP_REST_Request    $request REST request.
		 */
		do_action( 'tiffingrab_tally_form_response', $data, $request );
	}

	$response = array(
		'received' => true,
	);

	/**
	 * Short-circuit or extend the JSON returned to Tally (keep under ~10s total).
	 *
	 * @param array              $response Default response.
	 * @param array              $data     Decoded webhook JSON.
	 * @param WP_REST_Request    $request  REST request.
	 */
	$response = apply_filters( 'tiffingrab_tally_webhook_response', $response, $data, $request );

	return rest_ensure_response( $response );
}
