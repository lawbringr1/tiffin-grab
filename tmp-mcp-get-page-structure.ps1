param([Parameter(Mandatory = $true)][int]$PostId)

$ErrorActionPreference = "Stop"
$mcpPath = Join-Path $PSScriptRoot ".cursor/mcp.json"
$mcpRaw = Get-Content -Raw $mcpPath
if ($mcpRaw -notmatch '"elementor-mcp"\s*:\s*\{\s*"url"\s*:\s*"[^"]+"\s*,\s*"headers"\s*:\s*\{\s*"Authorization"\s*:\s*"([^"]+)"') {
  throw "Could not extract elementor-mcp Authorization from .cursor/mcp.json"
}
$basicHeader = $Matches[1]
$serverUrl = "https://tiffingrab.ca/wp-json/mcp/elementor-mcp-server"

$sessionId = & (Join-Path $PSScriptRoot "tmp-mcp-init.ps1")
if (-not $sessionId) { throw "MCP initialize did not return a session id." }

$bodyObj = @{
  jsonrpc = "2.0"
  id = 2
  method = "tools/call"
  params = @{
    name = "elementor-mcp-get-page-structure"
    arguments = @{ post_id = $PostId }
  }
}
$json = $bodyObj | ConvertTo-Json -Depth 20 -Compress
$payloadPath = Join-Path $PSScriptRoot ".tmp-mcp-get-structure-payload.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($payloadPath, $json, $utf8NoBom)

& curl.exe -sS -m 45 -X POST $serverUrl `
  -H ("Authorization: {0}" -f $basicHeader) `
  -H ("Mcp-Session-Id: {0}" -f $sessionId) `
  -H "Content-Type: application/json" `
  --data-binary ("@$payloadPath")
