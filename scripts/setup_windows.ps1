#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$PythonVersion = '3.12.5',
    [string]$VenvDir = '.venv',
    [switch]$ForceRecreateVenv,
    [switch]$NoWinget
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    # Ensure TLS 1.2 for downloads
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    } catch {}

    Write-Host "== Klaviyo Setup (Windows) ==" -ForegroundColor Cyan

    # Resolve repo root (this script lives in repo\scripts)
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Resolve-Path (Join-Path $ScriptDir '..')
    Set-Location $RepoRoot
    Write-Host "Repo root: $RepoRoot"

    $Requirements = Join-Path $RepoRoot 'requirements.txt'
    if (-not (Test-Path $Requirements)) {
        throw "requirements.txt not found at $Requirements"
    }

    function Test-CommandExists {
        param([Parameter(Mandatory)][string]$Name)
        return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
    }

    function Get-InstalledPython {
        # Prefer an existing python.exe in PATH
        if (Test-CommandExists -Name 'python') {
            try {
                $ver = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $exe = (Get-Command python).Source
                    return @{ Exe=$exe; Version=$ver }
                }
            } catch {}
        }
        # Try py launcher
        if (Test-CommandExists -Name 'py') {
            try {
                $exe = (& py -c "import sys; import os; print(sys.executable)" 2>$null)
                if ($LASTEXITCODE -eq 0 -and $exe) {
                    $ver = (& py -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null)
                    return @{ Exe=$exe; Version=$ver }
                }
            } catch {}
        }
        return $null
    }

    function Install-Python-WithWinget {
        Write-Host "Attempting Python install via winget..." -ForegroundColor Yellow
        $id = 'Python.Python.3.12'
        $args = @('install','-e','--id', $id, '--accept-package-agreements','--accept-source-agreements','--source','winget')
        $p = Start-Process -FilePath 'winget' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
        if ($p.ExitCode -ne 0) {
            throw "winget install failed with exit code $($p.ExitCode)"
        }
        Write-Host "winget install completed." -ForegroundColor Green
    }

    function Install-Python-FromWeb {
        param([Parameter(Mandatory)][string]$Version)
        $url = "https://www.python.org/ftp/python/$Version/python-$Version-amd64.exe"
        $tmp = Join-Path $env:TEMP "python-$Version-amd64.exe"
        Write-Host "Downloading Python $Version from python.org..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing
        Write-Host "Installing Python $Version (per-user, add to PATH)..." -ForegroundColor Yellow
        $installArgs = '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1'
        $p = Start-Process -FilePath $tmp -ArgumentList $installArgs -Wait -PassThru
        if ($p.ExitCode -ne 0) {
            throw "Python installer exited with code $($p.ExitCode)"
        }
        Remove-Item $tmp -ErrorAction SilentlyContinue
        Write-Host "Python installed." -ForegroundColor Green
        # Update PATH for current session if needed
        $userPyRoot = Join-Path $env:LOCALAPPDATA 'Programs\Python'
        if (Test-Path $userPyRoot) {
            $latest = Get-ChildItem $userPyRoot -Directory | Sort-Object LastWriteTime | Select-Object -Last 1
            if ($latest) {
                $bin = $latest.FullName
                $scripts = Join-Path $bin 'Scripts'
                $env:PATH = "$bin;$scripts;$env:PATH"
            }
        }
    }

    function Ensure-Python {
        $py = Get-InstalledPython
        if ($py) {
            Write-Host "Found Python $($py.Version) at $($py.Exe)" -ForegroundColor Green
            return $py.Exe
        }

        if (-not $NoWinget -and (Test-CommandExists -Name 'winget')) {
            try { Install-Python-WithWinget } catch { Write-Warning $_.Exception.Message }
        } else {
            Write-Host "Skipping winget attempt (NoWinget or winget not found)." -ForegroundColor DarkYellow
        }

        $py = Get-InstalledPython
        if ($py) { return $py.Exe }

        Install-Python-FromWeb -Version $PythonVersion
        $py = Get-InstalledPython
        if (-not $py) {
            throw "Python installation did not succeed; please install Python manually and re-run."
        }
        return $py.Exe
    }

    $pythonExe = Ensure-Python

    # Create or reuse virtual environment
    $venvPath = Join-Path $RepoRoot $VenvDir
    if (Test-Path $venvPath -and $ForceRecreateVenv) {
        Write-Host "Removing existing venv: $venvPath" -ForegroundColor Yellow
        Remove-Item -Recurse -Force $venvPath
    }
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment at $venvPath" -ForegroundColor Cyan
        & $pythonExe -m venv $venvPath
    } else {
        Write-Host "Using existing virtual environment at $venvPath" -ForegroundColor Green
    }

    $venvPython = Join-Path $venvPath 'Scripts\python.exe'
    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment python not found at $venvPython"
    }

    # Upgrade pip and install requirements
    Write-Host "Upgrading pip/setuptools/wheel..." -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip setuptools wheel

    Write-Host "Installing project requirements..." -ForegroundColor Cyan
    & $venvPython -m pip install -r $Requirements

    # Done
    Write-Host "\nSetup complete." -ForegroundColor Green
    Write-Host "Activate the venv and run the GUI:" -ForegroundColor Gray
    Write-Host "  `"$venvPath\Scripts\Activate.ps1`"" -ForegroundColor Gray
    Write-Host "  python run_klaviyo_gui.py" -ForegroundColor Gray
    Write-Host "\nOr run the CLI (dry run):" -ForegroundColor Gray
    Write-Host "  python fetch_metrics.py --dry-run" -ForegroundColor Gray

} catch {
    Write-Error $_.Exception.Message
    exit 1
}


