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
$rootPyFiles = @(Get-ChildItem -Path $projectResolved -File -Filter *.py)
$packageDirs = @(
    Get-ChildItem -Path $projectResolved -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName "__init__.py") }
)

$entryType = ""
$entryPath = ""
$content = ""

if ($rootPyFiles.Count -eq 1 -and $packageDirs.Count -eq 0) {
    $entryType = "single_file"
    $entryPath = $rootPyFiles[0].FullName
    $content = Get-Content -Path $entryPath -Raw
}
elseif ($rootPyFiles.Count -eq 0 -and $packageDirs.Count -eq 1) {
    $entryType = "package"
    $entryPath = $packageDirs[0].FullName
    $content = Get-Content -Path (Join-Path $entryPath "__init__.py") -Raw
}
else {
    throw "Expected either exactly one root .py addon file OR one package folder containing __init__.py in '$projectResolved'. Found root .py: $($rootPyFiles.Count), package dirs: $($packageDirs.Count)."
}

$nameMatch = [regex]::Match($content, '"name"\s*:\s*"([^"]+)"')
if (-not $nameMatch.Success) {
    throw "Could not parse bl_info name from addon entry."
}

$versionMatch = [regex]::Match($content, '"version"\s*:\s*\(([^)]+)\)')
if (-not $versionMatch.Success) {
    throw "Could not parse bl_info version from addon entry."
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
    if ($entryType -eq "single_file") {
        $entryName = [System.IO.Path]::GetFileName($entryPath)
        Copy-Item -Path $entryPath -Destination (Join-Path $tempRoot $entryName)
    }
    elseif ($entryType -eq "package") {
        $packageName = Split-Path -Path $entryPath -Leaf
        Copy-Item -Path $entryPath -Destination (Join-Path $tempRoot $packageName) -Recurse
    }
    else {
        throw "Unknown entry type: $entryType"
    }

    $zipName = "$productSlug-$version.zip"
    $zipPath = Join-Path $distResolved $zipName
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }

    Compress-Archive -Path (Join-Path $tempRoot "*") -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Output "Packaged: $zipPath"
    Write-Output "Entry type: $entryType"
    if ($entryType -eq "single_file") {
        Write-Output "Entry: $([System.IO.Path]::GetFileName($entryPath))"
    }
    else {
        Write-Output "Entry: $(Split-Path -Path $entryPath -Leaf)\__init__.py"
    }
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Recurse -Force
    }
}
