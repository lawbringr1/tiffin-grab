$ErrorActionPreference = "Stop"
$mcpPath = Join-Path $PSScriptRoot ".mcp.json"
$mcpRaw = Get-Content -Raw $mcpPath
if ($mcpRaw -notmatch '"elementor-mcp"\s*:\s*\{\s*"url"\s*:\s*"[^"]+"\s*,\s*"headers"\s*:\s*\{\s*"Authorization"\s*:\s*"([^"]+)"') {
  throw "Could not extract elementor-mcp Authorization from .mcp.json"
}
$basicHeader = $Matches[1]
$serverUrl = "https://tiffingrab.ca/wp-json/mcp/elementor-mcp-server"

$initBody = @{
  jsonrpc = "2.0"
  id = 1
  method = "initialize"
  params = @{
    protocolVersion = "2025-06-18"
    capabilities = @{}
    clientInfo = @{ name = "tiffin-grab-cli"; version = "1" }
  }
} | ConvertTo-Json -Depth 10 -Compress

$utf8 = New-Object System.Text.UTF8Encoding $false
$reqPath = Join-Path $PSScriptRoot ".tmp-mcp-init-req.json"
[System.IO.File]::WriteAllText($reqPath, $initBody, $utf8)

$hdrPath = Join-Path $PSScriptRoot ".tmp-mcp-init-hdr.txt"
$bodyPath = Join-Path $PSScriptRoot ".tmp-mcp-init-body.txt"
Remove-Item $hdrPath, $bodyPath -ErrorAction SilentlyContinue

& curl.exe -sS -m 25 -D $hdrPath -o $bodyPath -X POST $serverUrl `
  -H ("Authorization: {0}" -f $basicHeader) `
  -H "Content-Type: application/json" `
  --data-binary ("@$reqPath")

$sessionLine = Select-String -Path $hdrPath -Pattern 'mcp-session-id:\s*(.+)' -ErrorAction SilentlyContinue
if (-not $sessionLine) {
  Write-Output "No mcp-session-id in headers. Headers:"
  Get-Content $hdrPath
  Get-Content $bodyPath
  exit 1
}
$sessionId = $sessionLine.Matches[0].Groups[1].Value.Trim()
Write-Output $sessionId
