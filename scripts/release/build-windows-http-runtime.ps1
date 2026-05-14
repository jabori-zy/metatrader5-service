[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^mt5-service-v\d+\.\d+\.\d+(?:-(?:dev|test|staging)(?:\.[1-9]\d*)?)?$')]
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

$tagPattern = '^mt5-service-v(?<version>\d+\.\d+\.\d+)(?:-(?<env>dev|test|staging)(?:\.(?<build>[1-9]\d*))?)?$'
if ($TagName -match $tagPattern) {
    $assetVersion = "v$($Matches["version"])"
    $assetEnv = $Matches["env"]
    $assetBuild = $Matches["build"]
} else {
    throw "Invalid release tag '$TagName'. Expected mt5-service-v1.2.3 or mt5-service-v1.2.3-dev/test/staging with optional .1/.2 prerelease build suffix"
}

$assetPrerelease = if ($assetBuild) { "$assetEnv.$assetBuild" } else { $assetEnv }
$assetSuffix = if ($assetPrerelease) { "$assetVersion-$assetPrerelease" } else { $assetVersion }
$assetName = "mt5-service-windows-x64-$assetSuffix.zip"
$assetPath = Join-Path $distRoot $assetName

Remove-Item -Recurse -Force $runtimePath -ErrorAction SilentlyContinue
Remove-Item -Force $assetPath -ErrorAction SilentlyContinue

Set-Location $serviceRoot

uv run pyinstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name "mt5-service-http" `
    --distpath $runtimePath `
    --workpath (Join-Path $repoRoot "build/pyinstaller") `
    --specpath (Join-Path $repoRoot "build/pyinstaller") `
    --collect-all MetaTrader5 `
    --collect-all fastapi `
    --collect-all uvicorn `
    --collect-all starlette `
    main.py

$appDir = Join-Path $runtimePath "mt5-service-http"
$exePath = Join-Path $appDir "mt5-service-http.exe"
if (-not (Test-Path $exePath)) {
    throw "PyInstaller output exe not found: $exePath"
}

Compress-Archive -Path $appDir -DestinationPath $assetPath -Force

Write-GitHubOutput -Name "asset_path" -Value $assetPath
Write-GitHubOutput -Name "asset_name" -Value $assetName

Write-Host "Built release asset: $assetPath"
