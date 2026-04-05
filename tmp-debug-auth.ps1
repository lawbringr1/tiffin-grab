$ErrorActionPreference = "Stop"

$mcpPath = Join-Path $PSScriptRoot ".cursor/mcp.json"
$mcpConfig = Get-Content -Raw $mcpPath | ConvertFrom-Json
$auth = $mcpConfig.mcpServers.'elementor-mcp'.headers.Authorization

if ($auth -notmatch '^Basic\s+(.+)$') {
  Write-Output "Unexpected Authorization format."
  exit 1
}

$b64 = $Matches[1]
$decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64))
$parts = $decoded -split ':', 2

Write-Output ("Decoded user: {0}" -f $parts[0])
if ($parts.Count -lt 2) {
  Write-Output "Decoded token has no ':' separator."
} else {
  $pwd = $parts[1]
  Write-Output ("Decoded password length: {0}" -f $pwd.Length)
}

