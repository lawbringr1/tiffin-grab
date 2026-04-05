$ErrorActionPreference = "Stop"
$workspaceRoot = $PSScriptRoot
$mcpPath = Join-Path $workspaceRoot ".mcp.json"
$serverUrl = "https://tiffingrab.ca/wp-json/mcp/elementor-mcp-server"

$mcpRaw = Get-Content -Raw $mcpPath
if ($mcpRaw -notmatch '"elementor-mcp"\s*:\s*\{\s*"url"\s*:\s*"[^"]+"\s*,\s*"headers"\s*:\s*\{\s*"Authorization"\s*:\s*"([^"]+)"') {
  throw "Could not extract elementor-mcp Authorization from .mcp.json"
}
$basicHeader = $Matches[1]
$sessionId = & (Join-Path $workspaceRoot "tmp-mcp-init.ps1")
if (-not $sessionId) { throw "MCP initialize did not return a session id." }

# Hero thali image (template 9825, widget 0315b55): LCP tuning per Elementor image schema.
$settingsObj = [ordered]@{
  image = [ordered]@{
    url = "https://tiffingrab.ca/wp-content/uploads/2025/02/Maharaja-Thali-Non-veg.webp"
    id  = 0
    alt = "Maharaja Thali (Non-veg)"
  }
  image_size              = "custom"
  image_custom_dimension  = @{ width = 1200; height = 1200 }
  eos_image_lazy_loading  = "no_lazy"
  _attributes             = "fetchpriority|high`nloading|eager"
}

$bodyObj = @{
  jsonrpc = "2.0"
  id = 42
  method = "tools/call"
  params = @{
    name = "elementor-mcp-update-widget"
    arguments = @{
      post_id = 9825
      element_id = "0315b55"
      settings = $settingsObj
    }
  }
}
$body = $bodyObj | ConvertTo-Json -Depth 20 -Compress
$payloadPath = Join-Path $workspaceRoot ".tmp-mcp-lcp-image-payload.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($payloadPath, $body, $utf8NoBom)

Write-Output "POSTing LCP image settings for 9825 / 0315b55 ..."
& curl.exe -sS -m 90 -X POST $serverUrl `
  -H ("Authorization: {0}" -f $basicHeader) `
  -H ("Mcp-Session-Id: {0}" -f $sessionId) `
  -H "Content-Type: application/json" `
  --data-binary ("@$payloadPath")
