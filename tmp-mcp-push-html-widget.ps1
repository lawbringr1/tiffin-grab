param(
  [Parameter(Mandatory = $true)][int]$PostId,
  [Parameter(Mandatory = $true)][string]$ElementId,
  [Parameter(Mandatory = $true)][string]$HtmlRelativePath
)

$ErrorActionPreference = "Stop"
$workspaceRoot = $PSScriptRoot
$mcpPath = Join-Path $workspaceRoot ".cursor/mcp.json"
$htmlPath = Join-Path $workspaceRoot $HtmlRelativePath
$serverUrl = "https://tiffingrab.ca/wp-json/mcp/elementor-mcp-server"

$mcpRaw = Get-Content -Raw $mcpPath
if ($mcpRaw -notmatch '"elementor-mcp"\s*:\s*\{\s*"url"\s*:\s*"[^"]+"\s*,\s*"headers"\s*:\s*\{\s*"Authorization"\s*:\s*"([^"]+)"') {
  throw "Could not extract elementor-mcp Authorization header from .cursor/mcp.json"
}
$basicHeader = $Matches[1]

$sessionId = & (Join-Path $workspaceRoot "tmp-mcp-init.ps1")
if (-not $sessionId) { throw "MCP initialize did not return a session id." }

$htmlPathResolved = (Resolve-Path -LiteralPath $htmlPath).Path
$utf8 = New-Object System.Text.UTF8Encoding $false
$html = [System.IO.File]::ReadAllText($htmlPathResolved, $utf8)
if ($html -isnot [string]) { throw "Expected plain string HTML from file." }

$htmlJson = ConvertTo-Json -InputObject $html -Compress
if ($htmlJson -match 'PSPath|PSParentPath|PSChildName') {
  throw "HTML was serialized with PowerShell metadata; aborting."
}

$json = @"
{"jsonrpc":"2.0","id":41,"method":"tools/call","params":{"name":"elementor-mcp-update-widget","arguments":{"post_id":$PostId,"element_id":"$ElementId","settings":{"html":$htmlJson}}}}
"@
$payloadPath = Join-Path $workspaceRoot (".tmp-mcp-payload-{0}.json" -f $ElementId)
[System.IO.File]::WriteAllText($payloadPath, $json, $utf8)

Write-Output ("POSTing {0} -> post {1} element {2} ..." -f $HtmlRelativePath, $PostId, $ElementId)

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
& curl.exe @curlArgs 2>&1
