param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [string]$DistPath = "dist"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

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

function Remove-CacheDirs {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Get-ChildItem -LiteralPath $Path -Directory -Recurse -Force |
        Where-Object { $_.Name -eq "__pycache__" } |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
}

function New-PortableZip {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceRoot,

        [Parameter(Mandatory = $true)]
        [string]$ZipPath
    )

    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }

    $sourceRootResolved = (Resolve-Path $SourceRoot).Path.TrimEnd([char[]]@('\', '/'))
    $zip = [System.IO.Compression.ZipFile]::Open(
        $ZipPath,
        [System.IO.Compression.ZipArchiveMode]::Create
    )

    try {
        Get-ChildItem -LiteralPath $sourceRootResolved -Recurse -File |
            Sort-Object FullName |
            ForEach-Object {
                $relative = $_.FullName.Substring($sourceRootResolved.Length + 1)
                $entryName = $relative -replace '\\', '/'

                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $zip,
                    $_.FullName,
                    $entryName,
                    [System.IO.Compression.CompressionLevel]::Optimal
                ) | Out-Null
            }
    }
    finally {
        $zip.Dispose()
    }
}

function Test-PortableZipEntries {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ZipPath
    )

    $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)

    try {
        $badEntries = @(
            $zip.Entries |
            Where-Object { $_.FullName -like "*\*" } |
            Select-Object -ExpandProperty FullName
        )

        if ($badEntries.Count -gt 0) {
            throw "ZIP contains non-portable entry names: $($badEntries -join ', ')"
        }
    }
    finally {
        $zip.Dispose()
    }
}

function Copy-AddonPayload {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EntryType,

        [Parameter(Mandatory = $true)]
        [string]$EntryPath,

        [Parameter(Mandatory = $true)]
        [string]$DestinationRoot
    )

    if ($EntryType -eq "single_file") {
        $entryName = [System.IO.Path]::GetFileName($EntryPath)
        Copy-Item -Path $EntryPath -Destination (Join-Path $DestinationRoot $entryName)
        return
    }

    if ($EntryType -eq "package") {
        $packageName = Split-Path -Path $EntryPath -Leaf
        $packageDestination = Join-Path $DestinationRoot $packageName
        Copy-Item -Path $EntryPath -Destination $packageDestination -Recurse
        Remove-CacheDirs -Path $packageDestination
        return
    }

    throw "Unknown entry type: $EntryType"
}

function Copy-ExtensionPayload {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EntryType,

        [Parameter(Mandatory = $true)]
        [string]$EntryPath,

        [Parameter(Mandatory = $true)]
        [string]$DestinationRoot
    )

    if ($EntryType -eq "single_file") {
        Copy-Item -Path $EntryPath -Destination (Join-Path $DestinationRoot "__init__.py")
        return
    }

    if ($EntryType -eq "package") {
        Get-ChildItem -LiteralPath $EntryPath -Force | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination (Join-Path $DestinationRoot $_.Name) -Recurse
        }
        Remove-CacheDirs -Path $DestinationRoot
        return
    }

    throw "Unknown entry type: $EntryType"
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

$licensePath = Join-Path $repoRoot "LICENSE"
$marketReadmePath = Join-Path $projectResolved "README.market.md"
$releaseReadmePath = Join-Path $projectResolved "README.release.md"
$manifestPath = if ($entryType -eq "package") {
    Join-Path $entryPath "blender_manifest.toml"
} else {
    Join-Path $projectResolved "blender_manifest.toml"
}

$tempLegacyRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("smg403_legacy_" + [guid]::NewGuid().ToString("N"))
$tempExtensionRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("smg403_extension_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempLegacyRoot | Out-Null
New-Item -ItemType Directory -Path $tempExtensionRoot | Out-Null

try {
    Copy-AddonPayload -EntryType $entryType -EntryPath $entryPath -DestinationRoot $tempLegacyRoot

    if (Test-Path $licensePath) {
        Copy-Item -Path $licensePath -Destination (Join-Path $tempLegacyRoot "LICENSE")
    }

    if (Test-Path $marketReadmePath) {
        Copy-Item -Path $marketReadmePath -Destination (Join-Path $tempLegacyRoot "README.md")
    }
    elseif (Test-Path $releaseReadmePath) {
        Copy-Item -Path $releaseReadmePath -Destination (Join-Path $tempLegacyRoot "README.md")
    }

    $legacyZipName = "$productSlug-$version.zip"
    $legacyZipPath = Join-Path $distResolved $legacyZipName
    New-PortableZip -SourceRoot $tempLegacyRoot -ZipPath $legacyZipPath
    Test-PortableZipEntries -ZipPath $legacyZipPath

    Write-Output "Packaged: $legacyZipPath"
    Write-Output "Entry type: $entryType"
    if ($entryType -eq "single_file") {
        Write-Output "Entry: $([System.IO.Path]::GetFileName($entryPath))"
    }
    else {
        Write-Output "Entry: $(Split-Path -Path $entryPath -Leaf)/__init__.py"
    }
    Write-Output "Includes LICENSE: $(Test-Path $licensePath)"
    Write-Output "Includes buyer README: $((Test-Path $marketReadmePath) -or (Test-Path $releaseReadmePath))"

    if (Test-Path $manifestPath) {
        Copy-ExtensionPayload -EntryType $entryType -EntryPath $entryPath -DestinationRoot $tempExtensionRoot

        if (Test-Path $licensePath) {
            Copy-Item -Path $licensePath -Destination (Join-Path $tempExtensionRoot "LICENSE")
        }

        if (Test-Path $marketReadmePath) {
            Copy-Item -Path $marketReadmePath -Destination (Join-Path $tempExtensionRoot "README.md")
        }
        elseif (Test-Path $releaseReadmePath) {
            Copy-Item -Path $releaseReadmePath -Destination (Join-Path $tempExtensionRoot "README.md")
        }

        $extensionZipName = "$productSlug-$version-extension.zip"
        $extensionZipPath = Join-Path $distResolved $extensionZipName
        New-PortableZip -SourceRoot $tempExtensionRoot -ZipPath $extensionZipPath
        Test-PortableZipEntries -ZipPath $extensionZipPath
        Write-Output "Packaged extension: $extensionZipPath"
    }
    else {
        Write-Output "Packaged extension: skipped (no blender_manifest.toml)"
    }
}
finally {
    if (Test-Path $tempLegacyRoot) {
        Remove-Item -Path $tempLegacyRoot -Recurse -Force
    }
    if (Test-Path $tempExtensionRoot) {
        Remove-Item -Path $tempExtensionRoot -Recurse -Force
    }
}
