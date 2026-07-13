<#
.SYNOPSIS
Starts the Traeger API and Vite frontend in two PowerShell windows.

.DESCRIPTION
Run this script from any directory. It uses its own location to find the
repository, then starts:
  - FastAPI at http://localhost:8000
  - Vite at http://localhost:5173

Prerequisites (one-time):
  1. Create backend\venv and install requirements.txt.
  2. Run npm install in frontend.
  3. Create backend\.env with SIMULATE=true for local simulated data.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot 'backend\venv\Scripts\python.exe'
$FrontendDirectory = Join-Path $RepoRoot 'frontend'
$EnvFile = Join-Path $RepoRoot 'backend\.env'

if (-not (Test-Path $Python)) {
    throw "Could not find $Python. Set up the backend environment first: cd `"$RepoRoot\backend`"; python -m venv venv; .\venv\Scripts\Activate.ps1; cd ..; pip install -r requirements.txt"
}

if (-not (Test-Path (Join-Path $FrontendDirectory 'node_modules'))) {
    throw "Could not find frontend\node_modules. Install frontend dependencies first: cd `"$FrontendDirectory`"; npm.cmd install"
}

if (-not (Test-Path $EnvFile)) {
    Write-Warning "backend\.env is missing. The backend will try to connect to a real Traeger account. For safe local demo data, create $EnvFile containing: SIMULATE=true"
}

$BackendCommand = "& `"$Python`" -m uvicorn backend.main:app --reload"
$FrontendCommand = "npm.cmd run dev"

Write-Host "Starting backend at http://localhost:8000 ..."
Start-Process powershell.exe -WorkingDirectory $RepoRoot -ArgumentList '-NoExit', '-Command', $BackendCommand

Write-Host "Starting frontend at http://localhost:5173 ..."
Start-Process powershell.exe -WorkingDirectory $FrontendDirectory -ArgumentList '-NoExit', '-Command', $FrontendCommand

Write-Host "Both development servers are starting in separate windows."
