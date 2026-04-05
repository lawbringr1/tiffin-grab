param(
  # Elementor template post that Home 2026 embeds via [elementor-template id="9825"]
  [string]$WidgetPostId = "9825",
  [string]$WidgetElementId = "7349cd7"
)

$ErrorActionPreference = "Stop"

$workspaceRoot = $PSScriptRoot

$mcpPath = Join-Path $workspaceRoot ".cursor/mcp.json"
$htmlPath = Join-Path $workspaceRoot "elementor-html\home-2026-hero-card.html"
$serverUrl = "https://tiffingrab.ca/wp-json/mcp/elementor-mcp-server"

$mcpRaw = Get-Content -Raw $mcpPath
if ($mcpRaw -notmatch '"elementor-mcp"\s*:\s*\{\s*"url"\s*:\s*"[^"]+"\s*,\s*"headers"\s*:\s*\{\s*"Authorization"\s*:\s*"([^"]+)"') {
  throw "Could not extract elementor-mcp Authorization header from .cursor/mcp.json"
}
$basicHeader = $Matches[1]

$sessionId = & (Join-Path $workspaceRoot "tmp-mcp-init.ps1")
if (-not $sessionId) { throw "MCP initialize did not return a session id." }

# Use ReadAllText so $html is always a System.String. Do NOT use Get-Content without -Raw (line array) or
# pipeline to ConvertTo-Json can serialize extra PowerShell metadata — WordPress then prints literal "Array".
$htmlPathResolved = (Resolve-Path -LiteralPath $htmlPath).Path
$utf8 = New-Object System.Text.UTF8Encoding $false
$html = [System.IO.File]::ReadAllText($htmlPathResolved, $utf8)
if ($html -isnot [string]) { throw "Expected plain string HTML from file." }

# Escape HTML as a JSON string only (must be a string, not an object with PSPath/PSDrive, etc.).
$htmlJson = ConvertTo-Json -InputObject $html -Compress
if ($htmlJson -match 'PSPath|PSParentPath|PSChildName') {
  throw "HTML was serialized with PowerShell metadata; aborting (would show as Array on the site)."
}
$json = @"
{"jsonrpc":"2.0","id":40,"method":"tools/call","params":{"name":"elementor-mcp-update-widget","arguments":{"post_id":$([int]$WidgetPostId),"element_id":"$WidgetElementId","settings":{"html":$htmlJson}}}}
"@
$payloadPath = Join-Path $workspaceRoot ".tmp-mcp-update-home-2026-hero-payload.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($payloadPath, $json, $utf8NoBom)

Write-Output "POSTing MCP update via curl (timeout 90s)..."
Write-Output ("Payload chars: {0}" -f $json.Length)

$curlArgs = @(
  "-sS",
  "-m", "90",
  "-X", "POST",
  $serverUrl,
  "-H", ("Authorization: {0}" -f $basicHeader),
  "-H", ("Mcp-Session-Id: {0}" -f $sessionId),
  "-H", "Content-Type: application/json",
  "--data-binary", ("@$payloadPath")
)

$out = & curl.exe @curlArgs 2>&1
Write-Output $out

