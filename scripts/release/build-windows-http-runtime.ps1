[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^desktop-v\d+\.\d+\.\d+(?:-(?:dev|test|beta|rc)\.[1-9]\d*)?$')]
    [string]$TagName
)

$ErrorActionPreference = "Stop"

function Write-GitHubOutput {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Value
    )

    if (-not $env:GITHUB_OUTPUT) {
        return
    }

    "$Name=$Value" | Out-File -FilePath $env:GITHUB_OUTPUT -Append -Encoding utf8
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$serviceRoot = Join-Path $repoRoot "service"
$distRoot = Join-Path $repoRoot "dist"
$runtimeName = "mt5-service-http-runtime"
$runtimePath = Join-Path $distRoot $runtimeName

$tagPattern = '^desktop-(?<version>v\d+\.\d+\.\d+(?:-(?:dev|test|beta|rc)\.[1-9]\d*)?)$'
if ($TagName -match $tagPattern) {
    $releaseVersion = $Matches["version"]
} else {
    throw "Invalid release tag '$TagName'. Expected desktop-v1.2.3, desktop-v1.2.3-dev.1, desktop-v1.2.3-test.1, desktop-v1.2.3-beta.1, or desktop-v1.2.3-rc.1"
}

$assetName = "metatrader5-service-desktop-$releaseVersion-windows-x64.zip"
$assetPath = Join-Path $distRoot $assetName

Remove-Item -Recurse -Force $runtimePath -ErrorAction SilentlyContinue
Remove-Item -Force $assetPath -ErrorAction SilentlyContinue

Set-Location $serviceRoot

uv run pyinstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name "mt5-service" `
    --distpath $runtimePath `
    --workpath (Join-Path $repoRoot "build/pyinstaller") `
    --specpath (Join-Path $repoRoot "build/pyinstaller") `
    --collect-all MetaTrader5 `
    --collect-all fastapi `
    --collect-all uvicorn `
    --collect-all starlette `
    main.py

$appDir = Join-Path $runtimePath "mt5-service"
$exePath = Join-Path $appDir "mt5-service.exe"
if (-not (Test-Path $exePath)) {
    throw "PyInstaller output exe not found: $exePath"
}

Compress-Archive -Path $appDir -DestinationPath $assetPath -Force

Write-GitHubOutput -Name "asset_path" -Value $assetPath
Write-GitHubOutput -Name "asset_name" -Value $assetName

Write-Host "Built release asset: $assetPath"
