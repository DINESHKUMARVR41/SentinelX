# Behavior-Based Detection Demo
# This script demonstrates that SentinelX detects suspicious BEHAVIOR
# regardless of WHERE the process runs from

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SentinelX Behavior-Based Detection Demo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This demo shows that SentinelX detects suspicious behavior" -ForegroundColor Yellow
Write-Host "from ANY location, not just TEMP directories." -ForegroundColor Yellow
Write-Host ""

$currentLocation = Get-Location
Write-Host "Running from: $currentLocation" -ForegroundColor Green
Write-Host ""

# Demo 1: Suspicious Command Line Patterns
Write-Host "[Demo 1] Suspicious PowerShell Command Patterns" -ForegroundColor Cyan
Write-Host "  Trigger: Command line analysis (behavior-based)" -ForegroundColor Gray
Write-Host ""

# Simulate encoded command (safe - just echoes text)
$encodedCmd = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes("Write-Host 'Safe Test'"))
Write-Host "  Executing: powershell -NoProfile -EncodedCommand [base64]" -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-EncodedCommand", $encodedCmd -Wait
Write-Host "  ✓ Should trigger: 'Encoded PowerShell command'" -ForegroundColor Green
Start-Sleep -Seconds 2

# Demo 2: Download Pattern (safe - no actual download)
Write-Host ""
Write-Host "[Demo 2] Web Download Pattern" -ForegroundColor Cyan
Write-Host "  Trigger: Suspicious command pattern detection" -ForegroundColor Gray
Write-Host ""

$downloadScript = @'
Write-Host "Simulating download pattern..."
# Safe test - just creates WebClient object, doesn't download
try {
    $wc = New-Object System.Net.WebClient
    $wc.Dispose()
    Write-Host "WebClient pattern detected"
} catch {}
'@

$scriptPath = Join-Path $env:TEMP "test_download.ps1"
Set-Content -Path $scriptPath -Value $downloadScript
Write-Host "  Executing: Script with WebClient pattern" -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath -Wait
Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
Write-Host "  ✓ Should trigger: 'Web client usage'" -ForegroundColor Green
Start-Sleep -Seconds 2

# Demo 3: WMI Execution Pattern
Write-Host ""
Write-Host "[Demo 3] WMI Query Pattern" -ForegroundColor Cyan
Write-Host "  Trigger: System manipulation detection" -ForegroundColor Gray
Write-Host ""

$wmiScript = @'
Write-Host "Executing WMI query..."
Get-WmiObject -Class Win32_Process | Select-Object -First 1 | Out-Null
Write-Host "WMI query completed"
'@

$wmiPath = Join-Path $env:TEMP "test_wmi.ps1"
Set-Content -Path $wmiPath -Value $wmiScript
Write-Host "  Executing: Script with WMI queries" -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoProfile", "-File", $wmiPath -Wait
Remove-Item $wmiPath -Force -ErrorAction SilentlyContinue
Write-Host "  ✓ Should trigger: 'WMI object query'" -ForegroundColor Green
Start-Sleep -Seconds 2

# Demo 4: High Network Activity
Write-Host ""
Write-Host "[Demo 4] Network Activity Pattern" -ForegroundColor Cyan
Write-Host "  Trigger: Rapid network connections" -ForegroundColor Gray
Write-Host ""

Write-Host "  Making multiple network connections..." -ForegroundColor Yellow
$targets = @('google.com', 'microsoft.com', 'github.com', 'stackoverflow.com', 'reddit.com', 'wikipedia.org')
foreach ($target in $targets) {
    try {
        Test-Connection -ComputerName $target -Count 1 -Quiet | Out-Null
    } catch {}
}
Write-Host "  ✓ Should trigger: 'High network activity'" -ForegroundColor Green
Start-Sleep -Seconds 2

# Demo 5: Suspicious Process Spawn (LOLBin)
Write-Host ""
Write-Host "[Demo 5] LOLBin Execution" -ForegroundColor Cyan
Write-Host "  Trigger: Suspicious process name detection" -ForegroundColor Gray
Write-Host ""

Write-Host "  Spawning: certutil.exe (Living Off the Land Binary)" -ForegroundColor Yellow
Start-Process certutil.exe -ArgumentList "-?" -WindowStyle Hidden -Wait
Write-Host "  ✓ Should trigger: 'LOLBin execution: certutil.exe'" -ForegroundColor Green
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Demo Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Key Points:" -ForegroundColor Yellow
Write-Host "  • All demos ran from: $currentLocation" -ForegroundColor White
Write-Host "  • Detection based on BEHAVIOR, not location" -ForegroundColor White
Write-Host "  • System-wide monitoring active" -ForegroundColor White
Write-Host ""
Write-Host "Check SentinelX dashboard for investigations!" -ForegroundColor Green
Write-Host "You should see multiple investigations triggered by different behaviors." -ForegroundColor Yellow
Write-Host ""
