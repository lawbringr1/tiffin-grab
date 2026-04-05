<?php
/**
 * Ensures `window.deliverySlots` exists (ajaxUrl + nonce) for custom Elementor HTML that calls
 * `check_delivery_slot`. The child theme already defines this when `delivery-slots-frontend.js` is
 * enqueued (e.g. pages with the original shortcode). On other pages, this fills the gap.
 *
 * Install: require_once in hello-elementor-child-v2/functions.php, or use a mu-plugin.
 *
 * If AJAX returns -1 or “nonce failed”, change $nonce_action to match check_ajax_referer() in the
 * theme’s delivery handler (often the same string as the AJAX action).
 */
add_action(
	'wp_footer',
	static function (): void {
		if ( is_admin() ) {
			return;
		}
		$nonce_action = 'check_delivery_slot';
		$payload        = array(
			'ajaxUrl' => admin_url( 'admin-ajax.php' ),
			'nonce'   => wp_create_nonce( $nonce_action ),
		);
		?>
		<script>
		(function () {
			var w = window;
			if (w.deliverySlots && w.deliverySlots.nonce) {
				return;
			}
			w.deliverySlots = Object.assign({}, w.deliverySlots || {}, <?php echo wp_json_encode( $payload ); ?>);
			w.tiffinGrabDelivery = Object.assign({}, w.tiffinGrabDelivery || {}, w.deliverySlots);
		})();
		</script>
		<?php
	},
	100
);
