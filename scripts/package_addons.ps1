param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$DistPath = "dist"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Convert-ToSlug {
    param([string]$Value)
    $slug = $Value.ToLowerInvariant()
    $slug = $slug -replace "[^a-z0-9]+", "-"
    $slug = $slug.Trim("-")
    if ([string]::IsNullOrWhiteSpace($slug)) {
        return "addon"
    }
    return $slug
}

$projectResolved = (Resolve-Path $ProjectPath).Path
$pyFiles = @(Get-ChildItem -Path $projectResolved -File -Filter *.py)
if ($pyFiles.Count -ne 1) {
    throw "Expected exactly one .py addon entry file in '$projectResolved'. Found $($pyFiles.Count)."
}

$entryFile = $pyFiles[0]
$content = Get-Content -Path $entryFile.FullName -Raw

$nameMatch = [regex]::Match($content, '"name"\s*:\s*"([^"]+)"')
if (-not $nameMatch.Success) {
    throw "Could not parse bl_info name from $($entryFile.Name)"
}

$versionMatch = [regex]::Match($content, '"version"\s*:\s*\(([^)]+)\)')
if (-not $versionMatch.Success) {
    throw "Could not parse bl_info version from $($entryFile.Name)"
}

$productName = $nameMatch.Groups[1].Value
$versionRaw = $versionMatch.Groups[1].Value
$version = ($versionRaw -replace "\s+", "") -replace ",", "."
$productSlug = Convert-ToSlug $productName

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$distResolved = Join-Path $repoRoot $DistPath
New-Item -ItemType Directory -Force -Path $distResolved | Out-Null

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("smg403_pack_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

try {
    Copy-Item -Path $entryFile.FullName -Destination (Join-Path $tempRoot $entryFile.Name)

    $zipName = "$productSlug-$version.zip"
    $zipPath = Join-Path $distResolved $zipName
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }

    Compress-Archive -Path (Join-Path $tempRoot "*") -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Output "Packaged: $zipPath"
    Write-Output "Entry: $($entryFile.Name)"
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Recurse -Force
    }
}
