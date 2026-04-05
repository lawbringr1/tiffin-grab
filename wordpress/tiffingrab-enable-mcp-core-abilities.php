<?php
/**
 * Plugin Name: Tiffin Grab — Enable core abilities for MCP
 * Description: Marks WordPress core Abilities as MCP-public so the default MCP Adapter server can discover and execute them (requires WordPress 6.9+ Abilities API and MCP Adapter plugin).
 * Version: 1.0.0
 * Author: Tiffin Grab
 *
 * Install: copy this file to wp-content/plugins/tiffingrab-enable-mcp-core-abilities/tiffingrab-enable-mcp-core-abilities.php
 * and activate in WP Admin → Plugins.
 *
 * @see https://developer.wordpress.org/news/2026/02/from-abilities-to-ai-agents-introducing-the-wordpress-mcp-adapter/
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_filter( 'wp_register_ability_args', 'tiffingrab_enable_core_abilities_mcp_access', 10, 2 );

/**
 * Enable MCP default-server access for core abilities.
 *
 * @param array  $args         Ability registration arguments.
 * @param string $ability_name Ability ID.
 * @return array
 */
function tiffingrab_enable_core_abilities_mcp_access( array $args, string $ability_name ): array {
	$core_abilities = array(
		'core/get-site-info',
		'core/get-user-info',
		'core/get-environment-info',
	);

	if ( ! in_array( $ability_name, $core_abilities, true ) ) {
		return $args;
	}

	if ( ! isset( $args['meta'] ) || ! is_array( $args['meta'] ) ) {
		$args['meta'] = array();
	}
	if ( ! isset( $args['meta']['mcp'] ) || ! is_array( $args['meta']['mcp'] ) ) {
		$args['meta']['mcp'] = array();
	}

	$args['meta']['mcp']['public'] = true;

	return $args;
}
