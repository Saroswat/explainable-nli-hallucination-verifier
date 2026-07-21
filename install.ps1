[CmdletBinding()]
param(
    [string]$InstallDirectory = (Join-Path `
        ([Environment]::GetFolderPath("LocalApplicationData")) `
        "VeriNLI"),

    [string]$Branch = "main",

    [ValidateRange(1024, 65535)]
    [int]$Port = 8000,

    [switch]$NoBrowser,

    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"
$repository = "https://github.com/Saroswat/explainable-nli-hallucination-verifier.git"
$resolvedInstallDirectory = [System.IO.Path]::GetFullPath($InstallDirectory)

function Invoke-CheckedGit {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git $($Arguments -join ' ')"
    }
}

Write-Host ""
Write-Host "  VeriNLI installer" -ForegroundColor Cyan
Write-Host "  -----------------" -ForegroundColor DarkCyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw @"
Git is required but was not found on PATH.
Install Git for Windows from https://git-scm.com/download/win, open a new PowerShell
window, and run this installer again.
"@
}

$gitDirectory = Join-Path $resolvedInstallDirectory ".git"
if (-not (Test-Path -LiteralPath $resolvedInstallDirectory)) {
    $installParent = Split-Path -Parent $resolvedInstallDirectory
    New-Item -ItemType Directory -Path $installParent -Force | Out-Null
    Write-Host "[1/3] Downloading VeriNLI to $resolvedInstallDirectory" -ForegroundColor Yellow
    Invoke-CheckedGit -Arguments @(
        "clone",
        "--branch", $Branch,
        "--single-branch",
        $repository,
        $resolvedInstallDirectory
    )
}
elseif (Test-Path -LiteralPath $gitDirectory) {
    $remote = (& git -C $resolvedInstallDirectory remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0 -or $remote -notmatch "github\.com[:/]Saroswat/explainable-nli-hallucination-verifier(?:\.git)?$") {
        throw "The existing folder is not the expected VeriNLI GitHub repository: $resolvedInstallDirectory"
    }

    $localChanges = & git -C $resolvedInstallDirectory status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect the existing VeriNLI repository."
    }
    if ($localChanges) {
        throw "The existing VeriNLI repository has local changes. Commit or remove them before updating."
    }

    Write-Host "[1/3] Updating the existing VeriNLI installation." -ForegroundColor Yellow
    Invoke-CheckedGit -Arguments @("-C", $resolvedInstallDirectory, "fetch", "origin", $Branch)

    & git -C $resolvedInstallDirectory show-ref --verify --quiet "refs/heads/$Branch"
    if ($LASTEXITCODE -eq 0) {
        Invoke-CheckedGit -Arguments @("-C", $resolvedInstallDirectory, "switch", $Branch)
    }
    else {
        Invoke-CheckedGit -Arguments @(
            "-C", $resolvedInstallDirectory,
            "switch", "--track", "-c", $Branch, "origin/$Branch"
        )
    }
    Invoke-CheckedGit -Arguments @(
        "-C", $resolvedInstallDirectory,
        "pull", "--ff-only", "origin", $Branch
    )
}
else {
    throw @"
The installation path already exists but is not a VeriNLI repository:
$resolvedInstallDirectory

Choose another path with -InstallDirectory.
"@
}

$launcher = Join-Path $resolvedInstallDirectory "run.ps1"
if (-not (Test-Path -LiteralPath $launcher)) {
    throw "The VeriNLI launcher was not found after installation: $launcher"
}

Write-Host "[2/3] VeriNLI source is ready." -ForegroundColor Green
if ($NoLaunch) {
    Write-Host "[3/3] Launch skipped. Run $launcher when ready." -ForegroundColor DarkGray
    exit 0
}

Write-Host "[3/3] Preparing the isolated environment and starting VeriNLI." -ForegroundColor Yellow
$launcherArguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $launcher,
    "-Port", "$Port"
)
if ($NoBrowser) {
    $launcherArguments += "-NoBrowser"
}

& powershell.exe @launcherArguments
if ($LASTEXITCODE -ne 0) {
    throw "VeriNLI stopped with exit code $LASTEXITCODE."
}
