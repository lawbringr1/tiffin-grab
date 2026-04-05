param(
  [Parameter(Mandatory = $false)]
  [string]$Title = "Tiffin plans (new design)",

  [Parameter(Mandatory = $false)]
  [ValidateSet("draft", "publish")]
  [string]$Status = "draft"
)

$ErrorActionPreference = "Stop"
$workspaceRoot = $PSScriptRoot
$mcpPath = Join-Path $workspaceRoot ".mcp.json"
$serverUrl = "https://tiffingrab.ca/wp-json/mcp/elementor-mcp-server"

$mcpRaw = Get-Content -Raw $mcpPath
if ($mcpRaw -notmatch '"elementor-mcp"\s*:\s*\{\s*"url"\s*:\s*"[^"]+"\s*,\s*"headers"\s*:\s*\{\s*"Authorization"\s*:\s*"([^"]+)"') {
  throw "Could not extract elementor-mcp Authorization header from .mcp.json"
}
$basicHeader = $Matches[1]

$sessionId = & (Join-Path $workspaceRoot "tmp-mcp-init.ps1")
if (-not $sessionId) { throw "MCP initialize did not return a session id." }

$bodyObj = @{
  jsonrpc = "2.0"
  id      = 50
  method  = "tools/call"
  params  = @{
    name      = "elementor-mcp-create-page"
    arguments = @{
      title     = $Title
      status    = $Status
      post_type = "page"
    }
  }
}
$body = $bodyObj | ConvertTo-Json -Depth 10 -Compress
$payloadPath = Join-Path $workspaceRoot ".tmp-mcp-create-page-payload.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($payloadPath, $body, $utf8NoBom)

Write-Output "Creating page: $Title ($Status) ..."
& curl.exe -sS -m 120 -X POST $serverUrl `
  -H ("Authorization: {0}" -f $basicHeader) `
  -H ("Mcp-Session-Id: {0}" -f $sessionId) `
  -H "Content-Type: application/json" `
  --data-binary ("@$payloadPath")
