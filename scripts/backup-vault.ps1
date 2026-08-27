#Requires -Version 5.1
param(
    [string]$Reason = "manual"
)

$Vault       = "{{VAULT_PATH}}"
$Mirror      = "{{USER_HOME}}\OneDrive\Dokument\Backup\Knowledge-Base-Mirror"
$LocalMirror = "{{USER_HOME}}\Backup\Knowledge-Base-Mirror"
$BackupLog   = "{{USER_HOME}}\OneDrive\Dokument\Backup\backup.log"

# Pre-flight checks
if (-not (Test-Path $Vault)) {
    Write-Error "[backup] ERROR: vault not found at $Vault"
    exit 1
}

$backupParent = Split-Path $Mirror -Parent
if (-not (Test-Path $backupParent)) {
    Write-Error "[backup] ERROR: backup parent directory not found at $backupParent"
    exit 1
}

# Ensure local backup parent exists (create silently if not)
$localParent = Split-Path $LocalMirror -Parent
if (-not (Test-Path $localParent)) {
    New-Item -ItemType Directory -Force -Path $localParent | Out-Null
}

# Init git repo on first run
$gitDir = Join-Path $Mirror ".git"
if (-not (Test-Path $gitDir)) {
    Write-Host "[backup] First run - initialising git mirror repo..."
    New-Item -ItemType Directory -Force -Path $Mirror | Out-Null
    Push-Location $Mirror
    git init --initial-branch=main 2>&1 | Out-Null
    git config user.email "{{USER_EMAIL}}" 2>&1 | Out-Null
    git config user.name "{{USER_NAME}}" 2>&1 | Out-Null
    $gitignoreLines = @(
        ".obsidian/workspace.json",
        ".obsidian/workspace-mobile.json",
        ".obsidian/cache/",
        "node_modules/",
        ".cache/",
        "*.tmp"
    )
    ($gitignoreLines -join "`n") | Set-Content (Join-Path $Mirror ".gitignore") -Encoding UTF8
    git add .gitignore 2>&1 | Out-Null
    git commit -m "chore: init backup mirror" --allow-empty 2>&1 | Out-Null
    Pop-Location
    Write-Host "[backup] Git repo initialised."
}

# --- OneDrive mirror (git-tracked) ---
# Safety note after the 2026-05-21 deletion incident: never use mirror-delete flags here.
# Backups must be append/update-only so a partial or damaged live vault cannot erase the mirror.
robocopy $Vault $Mirror `
    /E /XJ /R:1 /W:1 /FFT /NFL /NDL /NP `
    /XD "node_modules" ".cache" ".git" ".next" "dist" "build" "out" `
    /LOG+:$BackupLog

$roboExit = $LASTEXITCODE
if ($roboExit -ge 8) {
    Write-Error "[backup] ERROR: OneDrive mirror robocopy failed (exit $roboExit). Check $BackupLog."
    exit $roboExit
}

# Ensure git identity is set before committing (idempotent — fixes repos initialised without it)
git -C $Mirror config user.email "{{USER_EMAIL}}" 2>&1 | Out-Null
git -C $Mirror config user.name "{{USER_NAME}}" 2>&1 | Out-Null

# Commit changes in mirror repo
Push-Location $Mirror
git add -A 2>&1 | Out-Null
$timestamp = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"
$commitMsg = "backup: $timestamp - $Reason"
git commit -m $commitMsg --allow-empty 2>&1 | Out-Null
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Error "[backup] ERROR: git commit failed (exit $exitCode)"
    Pop-Location
    exit $exitCode
}

$commitHash   = git rev-parse --short HEAD
$changedCount = (git diff-tree --no-commit-id -r --name-only HEAD 2>$null | Measure-Object -Line).Lines
Pop-Location

# --- Local mirror (non-OneDrive, robocopy only, no git) ---
# Second safety net: not on OneDrive, so survives cloud sync incidents.
if (-not (Test-Path $LocalMirror)) {
    New-Item -ItemType Directory -Force -Path $LocalMirror | Out-Null
    Write-Host "[backup] Local mirror directory created at $LocalMirror"
}

robocopy $Vault $LocalMirror `
    /E /XJ /R:1 /W:1 /FFT /NFL /NDL /NP `
    /XD "node_modules" ".cache" ".git" ".next" "dist" "build" "out"

$localRoboExit = $LASTEXITCODE
if ($localRoboExit -ge 8) {
    Write-Warning "[backup] WARNING: local mirror robocopy failed (exit $localRoboExit) - OneDrive mirror succeeded."
}

$summary = "[backup] $timestamp -> commit $commitHash ($changedCount files changed in OneDrive mirror; local mirror updated)"
Write-Host $summary

# Append terse summary line to backup.log for easy grepping
"$summary - $Reason" | Add-Content $BackupLog
exit 0
