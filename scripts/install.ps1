param(
  [string]$Destination = "$env:USERPROFILE\.codex\skills"
)
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
$src = Join-Path $root '.codex\skills'
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Get-ChildItem -Directory $src | ForEach-Object {
  $target = Join-Path $Destination $_.Name
  if (Test-Path $target) {
    $backup = "$target.backup-$(Get-Date -Format yyyyMMddHHmmss)"
    Move-Item -LiteralPath $target -Destination $backup
    Write-Host "Backed up $target -> $backup"
  }
  Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse
  Write-Host "Installed $($_.Name) -> $target"
}
