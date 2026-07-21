[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8000,

    [switch]$NoBrowser,

    [switch]$Reinstall
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Resolve-Python {
    $candidates = @(
        @{ Command = "py"; Arguments = @("-3") },
        @{ Command = "python"; Arguments = @() },
        @{ Command = "python3"; Arguments = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }
        try {
            $executable = & $candidate.Command @($candidate.Arguments) -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $executable) {
                return ($executable | Select-Object -Last 1)
            }
        }
        catch {
            continue
        }
    }

    throw @"
Python was not found. Install Python 3.11 or newer from:
https://www.python.org/downloads/windows/

During installation, select 'Add python.exe to PATH', then run this script again.
"@
}

Write-Host ""
Write-Host "  VeriNLI local launcher" -ForegroundColor Cyan
Write-Host "  ----------------------" -ForegroundColor DarkCyan

$systemPython = Resolve-Python
& $systemPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "VeriNLI requires Python 3.11 or newer. Found: $(& $systemPython --version)"
}

$venvDirectory = Join-Path $PSScriptRoot ".venv"
$venvPython = Join-Path $venvDirectory "Scripts\python.exe"
$stampFile = Join-Path $venvDirectory ".verinli-project-hash"
$projectHash = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot "pyproject.toml") -Algorithm SHA256).Hash

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "[1/3] Creating an isolated Python environment..." -ForegroundColor Yellow
    & $systemPython -m venv $venvDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "Python could not create the virtual environment."
    }
}
else {
    Write-Host "[1/3] Reusing the existing Python environment." -ForegroundColor DarkGray
}

$installedHash = if (Test-Path -LiteralPath $stampFile) {
    (Get-Content -Raw -LiteralPath $stampFile).Trim()
}
else {
    ""
}

if ($Reinstall -or $installedHash -ne $projectHash) {
    Write-Host "[2/3] Installing VeriNLI and its local web dependencies..." -ForegroundColor Yellow
    & $venvPython -m pip install --disable-pip-version-check -e ".[api]"
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed. Check your internet connection and try again."
    }
    Set-Content -LiteralPath $stampFile -Value $projectHash -Encoding ASCII
}
else {
    Write-Host "[2/3] Dependencies are already up to date." -ForegroundColor DarkGray
}

$url = "http://127.0.0.1:$Port"
Write-Host "[3/3] Starting VeriNLI at $url" -ForegroundColor Green

$server = Start-Process -FilePath $venvPython -ArgumentList @(
    "-m", "uvicorn", "verinli.api:app", "--host", "127.0.0.1", "--port", "$Port"
) -NoNewWindow -PassThru

try {
    $healthy = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($server.HasExited) {
            throw "The local server stopped before it became ready. Port $Port may already be in use."
        }
        try {
            $response = Invoke-WebRequest -Uri "$url/health" -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }

    if (-not $healthy) {
        throw "The local server did not become ready within 15 seconds."
    }

    Write-Host ""
    Write-Host "VeriNLI is ready." -ForegroundColor Green
    Write-Host "Open $url in your browser. Press Ctrl+C here to stop the server."
    Write-Host ""

    if (-not $NoBrowser) {
        Start-Process $url
    }

    Wait-Process -Id $server.Id
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force
    }
}
