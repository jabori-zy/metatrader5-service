[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Fail {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

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

function Get-ProjectVersion {
    param([string]$PyprojectPath)

    if (-not (Test-Path $PyprojectPath)) {
        Fail "pyproject.toml not found: $PyprojectPath"
    }

    $inProjectTable = $false
    foreach ($line in Get-Content -Path $PyprojectPath) {
        $trimmed = $line.Trim()

        if ($trimmed -eq "[project]") {
            $inProjectTable = $true
            continue
        }

        if ($inProjectTable -and $trimmed.StartsWith("[") -and $trimmed -ne "[project]") {
            break
        }

        if ($inProjectTable -and $trimmed -match '^version\s*=\s*"([^"]+)"\s*$') {
            return $Matches[1]
        }
    }

    Fail "project.version not found in $PyprojectPath"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $repoRoot

$tagName = $env:GITHUB_REF_NAME
if (-not $tagName) {
    $tagName = git describe --tags --exact-match HEAD 2>$null
}

if (-not $tagName) {
    Fail "Unable to resolve release tag from GITHUB_REF_NAME or git describe"
}

$tagPattern = '^mt5-service-v(?<version>\d+\.\d+\.\d+)(?:-(?<env>dev|test|staging)(?:\.(?<build>[1-9]\d*))?)?$'
if ($tagName -match $tagPattern) {
    $tagVersion = $Matches["version"]
    $releaseEnv = $Matches["env"]
    $releaseBuild = $Matches["build"]
} else {
    Fail "Invalid release tag '$tagName'. Expected mt5-service-v1.2.3 or mt5-service-v1.2.3-dev/test/staging with optional .1/.2 prerelease build suffix"
}

if (-not $releaseEnv) {
    $releaseEnv = "production"
}

$projectVersion = Get-ProjectVersion -PyprojectPath (Join-Path $repoRoot "service/pyproject.toml")
if ($tagVersion -ne $projectVersion) {
    Fail "Tag version '$tagVersion' does not match service/pyproject.toml project.version '$projectVersion'"
}

$branchByEnv = @{
    production = "main"
    dev = "develop"
    test = "test"
    staging = "staging"
}

$requiredBranch = $branchByEnv[$releaseEnv]
$requiredRemoteRef = "origin/$requiredBranch"

git fetch origin "+refs/heads/*:refs/remotes/origin/*" --tags
git rev-parse --verify "$requiredRemoteRef" *> $null
if ($LASTEXITCODE -ne 0) {
    Fail "Required release branch '$requiredRemoteRef' does not exist"
}

git merge-base --is-ancestor HEAD "$requiredRemoteRef"
if ($LASTEXITCODE -ne 0) {
    Fail "Release tag '$tagName' must point to a commit contained in '$requiredRemoteRef'"
}

$isPrerelease = if ($releaseEnv -eq "production") { "false" } else { "true" }

Write-GitHubOutput -Name "tag_name" -Value $tagName
Write-GitHubOutput -Name "release_name" -Value $tagName
Write-GitHubOutput -Name "release_env" -Value $releaseEnv
Write-GitHubOutput -Name "release_build" -Value $releaseBuild
Write-GitHubOutput -Name "version" -Value $tagVersion
Write-GitHubOutput -Name "prerelease" -Value $isPrerelease

Write-Host "Validated $tagName for $releaseEnv release from $requiredRemoteRef"
