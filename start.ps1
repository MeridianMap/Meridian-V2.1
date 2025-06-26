# PowerShell start script for the Meridian astrological web application

Write-Host "Starting Meridian application..." -ForegroundColor Green

# Check if ports are in use and stop any existing processes
$backendPort = 5000
$frontendPort = 3000

Write-Host "Checking for existing processes on ports $backendPort and $frontendPort..." -ForegroundColor Yellow

# Kill processes using port 5000 (backend)
$backendProcess = Get-NetTCPConnection -LocalPort $backendPort -ErrorAction SilentlyContinue
if ($backendProcess) {
    $processId = $backendProcess.OwningProcess
    Write-Host "Stopping existing process on port $backendPort (PID: $processId)" -ForegroundColor Yellow
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}

# Kill processes using port 3000 (frontend)
$frontendProcess = Get-NetTCPConnection -LocalPort $frontendPort -ErrorAction SilentlyContinue
if ($frontendProcess) {
    $processId = $frontendProcess.OwningProcess
    Write-Host "Stopping existing process on port $frontendPort (PID: $processId)" -ForegroundColor Yellow
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start the Flask backend
Write-Host "`nStarting Flask backend..." -ForegroundColor Green
$backendPath = Join-Path $scriptDir "backend"
$pythonExe = Join-Path $scriptDir "venv\Scripts\python.exe"
$apiScript = Join-Path $backendPath "api.py"

Set-Location $backendPath
$backendJob = Start-Job -ScriptBlock {
    param($pythonPath, $apiPath)
    & $pythonPath $apiPath
} -ArgumentList $pythonExe, $apiScript

Write-Host "Flask backend job started with ID: $($backendJob.Id)" -ForegroundColor Green

# Wait for Flask to initialize
Write-Host "Waiting for Flask to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start the Vite frontend
Write-Host "Starting Vite frontend..." -ForegroundColor Green
$frontendPath = Join-Path $scriptDir "frontend"
Set-Location $frontendPath

$frontendJob = Start-Job -ScriptBlock {
    param($frontendDir)
    Set-Location $frontendDir
    npm run dev
} -ArgumentList $frontendPath

Write-Host "Vite frontend job started with ID: $($frontendJob.Id)" -ForegroundColor Green

Write-Host "`nApplication is running!" -ForegroundColor Green
Write-Host "- Backend API: http://localhost:5000" -ForegroundColor Cyan
Write-Host "- Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "`nPress 'q' and Enter to stop both servers, or Ctrl+C to force exit" -ForegroundColor Yellow

# Wait for user input to stop
do {
    $input = Read-Host "`nEnter 'q' to quit"
} while ($input -ne 'q')

# Clean up jobs
Write-Host "`nStopping servers..." -ForegroundColor Yellow
Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue

Write-Host "Application stopped." -ForegroundColor Green
