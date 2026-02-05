# Traffic Classifier SDN - Windows/WSL2 Build Script
# Run this in PowerShell to set up and build the project in WSL2

Write-Host "=========================================="
Write-Host "Traffic Classifier SDN - Build Script"
Write-Host "=========================================="
Write-Host ""

# Check if WSL is installed
Write-Host "Checking WSL installation..." -ForegroundColor Cyan
$wslInstalled = $true
try {
    $null = wsl --list --quiet 2>&1
    if ($LASTEXITCODE -ne 0) {
        $wslInstalled = $false
    }
} catch {
    $wslInstalled = $false
}

if ($wslInstalled) {
    Write-Host "OK WSL is installed" -ForegroundColor Green
} else {
    Write-Host "ERROR WSL is not installed or not working properly" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install WSL2, run in PowerShell (as Administrator):" -ForegroundColor Yellow
    Write-Host "  wsl --install" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# Get the project directory
# Get the project directory dynamically
$projectPath = $PSScriptRoot
# Convert to WSL path (e.g., D:\Projects... -> /mnt/d/Projects...)
$drive = $projectPath.Substring(0,1).ToLower()
$path = $projectPath.Substring(3).Replace("\", "/")
$wslProjectPath = "/mnt/$drive/$path"

Write-Host "Project directory: $projectPath" -ForegroundColor Cyan
Write-Host "WSL path: $wslProjectPath" -ForegroundColor Cyan
Write-Host ""

# Check if project directory exists
if (-not (Test-Path $projectPath)) {
    Write-Host "ERROR Project directory not found: $projectPath" -ForegroundColor Red
    exit 1
}

Write-Host "=========================================="
Write-Host "Step 1: Making scripts executable"
Write-Host "=========================================="
Write-Host ""

wsl -e bash -c "cd $wslProjectPath; chmod +x setup_wsl.sh verify_setup.sh test_classifier.sh"
Write-Host "OK Scripts are now executable" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================="
Write-Host "Step 2: Running setup script"
Write-Host "=========================================="
Write-Host ""
Write-Host "This will install all dependencies (may take 10-20 minutes)..." -ForegroundColor Yellow
Write-Host ""

# Run the setup script
wsl -e bash -c "cd $wslProjectPath; ./setup_wsl.sh"

Write-Host ""
Write-Host "=========================================="
Write-Host "Step 3: Verifying installation"
Write-Host "=========================================="
Write-Host ""

# Run verification
wsl -e bash -c "cd $wslProjectPath; ./verify_setup.sh"

Write-Host ""
Write-Host "=========================================="
Write-Host "Build Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Green
Write-Host ""
Write-Host "Option 1: Run Quick Test" -ForegroundColor Cyan
Write-Host "  wsl -e bash -c 'cd $wslProjectPath; sudo ./test_classifier.sh'"
Write-Host ""
Write-Host "Option 2: Manual Run (Recommended for learning)" -ForegroundColor Cyan
Write-Host "  Terminal 1 - Start Mininet:"
Write-Host "    wsl -e bash -c 'cd $wslProjectPath; sudo mn --topo single,3 --mac --switch ovsk --controller remote'"
Write-Host ""
Write-Host "  Terminal 2 - Start Classifier (in a new PowerShell window):"
Write-Host "    wsl -e bash -c 'cd $wslProjectPath; sudo python3 traffic_classifier.py logistic'"
Write-Host ""
Write-Host "Option 3: Enter WSL for interactive use" -ForegroundColor Cyan
Write-Host "  wsl"
Write-Host "  cd $wslProjectPath"
Write-Host ""
Write-Host "For detailed instructions, see QUICK_START.md" -ForegroundColor Yellow
Write-Host ""
