# Traffic Classifier SDN - One-Click Launcher
# This script provides an easy menu-driven interface to run the project

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Traffic Classifier SDN - Quick Launcher   " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check WSL
$wslInstalled = $true
try {
    $null = wsl --list --quiet 2>&1
    if ($LASTEXITCODE -ne 0) { $wslInstalled = $false }
} catch { $wslInstalled = $false }

if (-not $wslInstalled) {
    Write-Host "ERROR: WSL2 is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install WSL2, run in PowerShell (as Administrator):" -ForegroundColor Yellow
    Write-Host "  wsl --install" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Get the project directory dynamically
$projectPath = $PSScriptRoot
# Convert to WSL path (e.g., D:\Projects... -> /mnt/d/Projects...)
$drive = $projectPath.Substring(0,1).ToLower()
$path = $projectPath.Substring(3).Replace("\", "/")
$wslPath = "/mnt/$drive/$path"

# Menu
Write-Host "What would you like to do?" -ForegroundColor Green
Write-Host ""
Write-Host "1. Setup & Install (First time only)" -ForegroundColor White
Write-Host "2. Quick Test - Run with existing models" -ForegroundColor White
Write-Host "3. Validate Datasets" -ForegroundColor White
Write-Host "4. Collect Training Data (Interactive)" -ForegroundColor White
Write-Host "5. Retrain All Models" -ForegroundColor White
Write-Host "6. Run with Dashboard (Full System)" -ForegroundColor White
Write-Host "7. Run Performance Benchmark" -ForegroundColor White
Write-Host "8. Clean Reset (Fix stuck processes)" -ForegroundColor White
Write-Host "9. View Documentation" -ForegroundColor White
Write-Host "0. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (0-9)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Running setup script..." -ForegroundColor Cyan
        Write-Host "This may take 10-20 minutes..." -ForegroundColor Yellow
        Write-Host ""
        & "$projectPath\build.ps1"
    }
    
    "2" {
        Write-Host ""
        Write-Host "Starting Quick Test..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "INSTRUCTIONS:" -ForegroundColor Yellow
        Write-Host "1. Terminal 1 (this window) will start Mininet" -ForegroundColor White
        Write-Host "2. Open a NEW PowerShell window and run:" -ForegroundColor White
        Write-Host "   wsl -e bash -c 'cd $wslPath && sudo python3 src/controller/enhanced_traffic_classifier.py logistic'" -ForegroundColor Green
        Write-Host "3. Then in Mininet prompt, type: h1 ping h2" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to start Mininet"
        wsl -e bash -c "cd $wslPath && sudo mn -c && sudo mn --topo single,3 --mac --switch ovsk --controller remote"
    }
    
        Write-Host "Validating system..." -ForegroundColor Cyan
        Write-Host ""
        wsl -e bash -c "cd $wslPath && ./scripts/setup/verify_setup.sh"
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
    "4" {
        Write-Host ""
        Write-Host "Data Collection Workflow" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Available traffic types:" -ForegroundColor Yellow
        Write-Host "  voice, video, http, https, ssh, ftp, game, telnet, dns, ping" -ForegroundColor White
        Write-Host ""
        $trafficType = Read-Host "Enter traffic type to collect"
        
        Write-Host ""
        Write-Host "INSTRUCTIONS:" -ForegroundColor Yellow
        Write-Host "1. Terminal 1 (this window) will start Mininet with D-ITG receiver" -ForegroundColor White
        Write-Host "2. Open a NEW PowerShell window and run:" -ForegroundColor White
        Write-Host "   wsl -e bash -c 'cd $wslPath && python3 src/controller/enhanced_traffic_classifier.py train $trafficType'" -ForegroundColor Green
        Write-Host "3. Wait for collector to start, then in Mininet prompt, type:" -ForegroundColor White
        Write-Host "   h1 ITGSend D-IGT_scripts/${trafficType}_script_file -a h2" -ForegroundColor Green
        Write-Host "4. Wait 15 minutes for collection to complete" -ForegroundColor White
        Write-Host ""
        Read-Host "Press Enter to start Mininet"
        wsl -e bash -c "cd $wslPath && sudo mn -c && sudo mn --topo single,3 --mac --switch ovsk --controller remote"
    }
    
        Write-Host "Retraining all models..." -ForegroundColor Cyan
        Write-Host ""
        wsl -e bash -c "cd $wslPath && python3 scripts/utils/retrain_all_models.py"
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
    "6" {
        Write-Host ""
        Write-Host "Starting Full System with Dashboard..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "INSTRUCTIONS:" -ForegroundColor Yellow
        Write-Host "You need to open 3 PowerShell windows:" -ForegroundColor White
        Write-Host ""
        Write-Host "Terminal 1 - Dashboard:" -ForegroundColor Cyan
        Write-Host "  wsl -e bash -c 'cd $wslPath && python3 src/dashboard/app.py'" -ForegroundColor Green
        Write-Host ""
        Write-Host "Terminal 2 - AI Classifier:" -ForegroundColor Cyan
        Write-Host "  wsl -e bash -c 'cd $wslPath && sudo python3 src/controller/enhanced_traffic_classifier.py Randomforest'" -ForegroundColor Green
        Write-Host ""
        Write-Host "Terminal 3 - Network:" -ForegroundColor Cyan
        Write-Host "  wsl -e bash -c 'cd $wslPath && sudo mn -c && sudo mn --topo single,3 --mac --switch ovsk --controller remote,ip=127.0.0.1,port=6633'" -ForegroundColor Green
        Write-Host ""
        Write-Host "Then open browser: http://localhost:5000" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
    "7" {
        Write-Host ""
        Write-Host "Running performance benchmark..." -ForegroundColor Cyan
        Write-Host ""
        wsl -e bash -c "cd $wslPath && sudo python3 benchmark.py"
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
    "8" {
        Write-Host ""
        Write-Host "Cleaning up stuck processes..." -ForegroundColor Cyan
        Write-Host ""
        wsl -e bash -c "cd $wslPath && sudo mn -c && sudo pkill -f ryu-manager && sudo fuser -k 6633/tcp && sudo fuser -k 9000/tcp"
        Write-Host ""
        Write-Host "Cleanup complete!" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
    "9" {
        Write-Host ""
        Write-Host "Opening documentation..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Available documentation files:" -ForegroundColor Yellow
        Write-Host "  - README.md (Comprehensive project guide)" -ForegroundColor White
        Write-Host "  - docs/academic/COMPLETE_ACADEMIC_REPORT.md (Academic report)" -ForegroundColor White
        Write-Host ""
        
        # Open in default editor
        Start-Process "$projectPath\README.md"
        Start-Process "$projectPath\docs\academic\COMPLETE_ACADEMIC_REPORT.md"
        
        Write-Host "Documentation opened in default editor!" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    
    "0" {
        Write-Host ""
        Write-Host "Goodbye!" -ForegroundColor Green
        Write-Host ""
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "Invalid choice. Please run the script again." -ForegroundColor Red
        Write-Host ""
    }
}
