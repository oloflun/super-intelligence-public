# Super-Intelligence — Schedule Daily Auto-Update (Windows)
# Usage: powershell -File schedule-auto-update.ps1 -UpdateScriptPath <path>
param(
    [Parameter(Mandatory=$true)]
    [string]$UpdateScriptPath
)

if (-not (Test-Path $UpdateScriptPath)) {
    Write-Error "Update script not found: $UpdateScriptPath"
    exit 1
}

$taskName = "SuperIntelligenceUpdate"

# Remove existing task if present
try { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue } catch { }

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -File `"$UpdateScriptPath`""

$trigger = New-ScheduledTaskTrigger -Daily -At 09:00 `
    -RandomDelay (New-TimeSpan -Hours 1)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Try S4U first (runs when user not logged in), fall back to Interactive
try {
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U -RunLevel Limited
} catch {
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive -RunLevel Limited
}

Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Daily health check and auto-update for super-intelligence agent stack" `
    -Force

Write-Output "✓ Task Scheduler registered: $taskName (daily at 09:00 + rand 1h)"
Write-Output "  Check: Get-ScheduledTask -TaskName $taskName"
Write-Output "  Logs: ~\.super-intelligence\update.log"
Write-Output "  To disable: set auto_update: false in ~\.super-intelligence\config.json"
Write-Output "  To remove: powershell -File remove-auto-update.ps1"
