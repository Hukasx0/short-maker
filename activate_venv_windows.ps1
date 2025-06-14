Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Short Maker - Virtual Environment (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to the script's directory (handles double-click from Windows Explorer)
Set-Location -Path $PSScriptRoot
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

if (!(Test-Path "venv")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup_windows.bat or setup_windows.ps1 first to create the virtual environment." -ForegroundColor Yellow
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Green

# Activate virtual environment
try {
    & .\venv\Scripts\Activate.ps1
} catch {
    Write-Host "⚠ Warning: Could not activate using PowerShell script, trying batch file..." -ForegroundColor Yellow
    & .\venv\Scripts\activate.bat
}

# Show Python version info
Write-Host "[INFO] Python version in virtual environment:" -ForegroundColor Yellow
python --version
Write-Host ""
Write-Host "[INFO] Virtual environment activated!" -ForegroundColor Green
Write-Host "To deactivate later, type: deactivate" -ForegroundColor White
Write-Host ""
Write-Host "You can now run Short Maker with:" -ForegroundColor White
Write-Host "python short-maker.py --gui" -ForegroundColor Yellow
Write-Host ""

# Keep PowerShell session open with the virtual environment activated
Write-Host "Press any key to continue with activated environment..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 