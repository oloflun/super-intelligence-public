# Super-Intelligence — Remove Daily Auto-Update Scheduler (Windows)
$taskName = "SuperIntelligenceUpdate"
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
    Write-Output "✓ Task Scheduler removed: $taskName"
} catch {
    Write-Output "No Task Scheduler entry found: $taskName"
}
Write-Output ""
Write-Output "Note: ~/.super-intelligence/ and update logs remain on disk."
Write-Output "Delete manually if you want to remove all traces."
