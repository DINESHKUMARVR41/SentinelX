# SentinelX Safe Detection Demo
# This demo generates simulated security events.
# It does NOT execute malware, network connections, encoded commands,
# PowerShell bypasses, WMI commands, or system binaries.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SentinelX Safe Detection Demo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generating simulated security telemetry..." -ForegroundColor Yellow
Write-Host ""

$events = @(
    @{
        Process = "powershell.exe"
        Behavior = "Suspicious command-line activity"
        Severity = "HIGH"
    },
    @{
        Process = "unknown_process.exe"
        Behavior = "Unexpected child-process creation"
        Severity = "MEDIUM"
    },
    @{
        Process = "browser.exe"
        Behavior = "Unusual outbound network activity"
        Severity = "MEDIUM"
    },
    @{
        Process = "unknown_process.exe"
        Behavior = "Multiple suspicious indicators detected"
        Severity = "CRITICAL"
    }
)

foreach ($event in $events) {
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host "Process : $($event.Process)" -ForegroundColor White
    Write-Host "Behavior: $($event.Behavior)" -ForegroundColor Yellow
    Write-Host "Severity: $($event.Severity)" -ForegroundColor Red
    Write-Host "Status  : SIMULATED EVENT" -ForegroundColor Green
    Write-Host ""
    Start-Sleep -Milliseconds 700
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Simulation Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "No processes were executed."
Write-Host "No network connections were made."
Write-Host "No files were modified."
Write-Host ""
Write-Host "Use the SentinelX dashboard to demonstrate:" -ForegroundColor Yellow
Write-Host "  Detection -> AI Explanation -> Human Approval -> Response"
