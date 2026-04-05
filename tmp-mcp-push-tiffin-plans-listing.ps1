# Push Editorial tiffin plans listing HTML to the Elementor draft page via MCP.
# Draft: "Tiffin plans (new design)" post_id=10297, HTML widget element_id=24caf9c (parent container 7674e61).
param(
  [string]$HtmlRelativePath = "elementor-html/tiffin-plans-listing-editorial-2026.html"
)

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "tmp-mcp-push-html-widget.ps1") -PostId 10297 -ElementId "24caf9c" -HtmlRelativePath $HtmlRelativePath
