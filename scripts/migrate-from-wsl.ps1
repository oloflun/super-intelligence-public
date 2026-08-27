<#
.SYNOPSIS
    Migrate Hermes agent data from Windows Subsystem for Linux (WSL) to Windows.

.DESCRIPTION
    Discovers WSL distros that have ~/.hermes/ data, migrates configuration,
    sessions, skills, memories, and other agent data to a Windows-native Hermes
    installation at $env:LOCALAPPDATA\hermes, with automatic path translation
    from WSL paths to Windows paths in configuration files.

    The script is non-destructive (never deletes source data), idempotent (safe
    to run repeatedly), and supports dry-run mode for previewing changes.

.PARAMETER DryRun
    Report what would happen without making any changes.

.PARAMETER Force
    Skip confirmation prompts and override warnings.

.PARAMETER SkipBackup
    Skip backing up the existing Windows Hermes installation before migration.

.PARAMETER IncludeCheckpoints
    Include checkpoints/ directory (potentially large).

.PARAMETER IncludeSnapshots
    Include state-snapshots/ directory.

.PARAMETER IncludeLogs
    Include logs/ directory (potentially very large).

.PARAMETER IncludeCache
    Include cache/ directory (potentially large, regeneratable).

.PARAMETER IncludeScripts
    Include scripts/ directory.

.EXAMPLE
    .\migrate-from-wsl.ps1 -DryRun
    Preview the migration without making changes.

.EXAMPLE
    .\migrate-from-wsl.ps1 -IncludeLogs -IncludeCache
    Migrate with logs and cache included.

.EXAMPLE
    .\migrate-from-wsl.ps1 -Force -SkipBackup
    Migrate without backup and skip all prompts.
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$SkipBackup,
    [switch]$IncludeCheckpoints,
    [switch]$IncludeSnapshots,
    [switch]$IncludeLogs,
    [switch]$IncludeCache,
    [switch]$IncludeScripts
)

$ErrorActionPreference = 'Stop'

# ============================================================
# SCRIPT STATE
# ============================================================

$script:Stats = @{
    FilesMigrated    = 0
    PathTranslations = 0
    SkippedItems     = 0
    Warnings         = [System.Collections.ArrayList]@()
    Errors           = [System.Collections.ArrayList]@()
    Tiers            = @{ '1' = @{}; '2' = @{}; '3' = @{} }
    BackupPath       = $null
    StartTime        = Get-Date
    SourceSize       = $null
    SourceFileCount  = $null
}

# ============================================================
# COLOR OUTPUT HELPERS
# ============================================================

function Write-Header {
    param([string]$Text)
    Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

function Write-SubHeader {
    param([string]$Text)
    Write-Host "  >> $Text" -ForegroundColor Cyan
}

function Write-OK {
    param([string]$Text)
    Write-Host "  [OK] $Text" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Text)
    Write-Host "  [WARN] $Text" -ForegroundColor Yellow
    $null = $script:Stats.Warnings.Add($Text)
}

function Write-Err {
    param([string]$Text)
    Write-Host "  [ERROR] $Text" -ForegroundColor Red
    $null = $script:Stats.Errors.Add($Text)
}

function Write-Info {
    param([string]$Text)
    Write-Host "  $Text" -ForegroundColor Gray
}

function Write-DryRun {
    param([string]$Text)
    Write-Host "  [DRY-RUN] $Text" -ForegroundColor Magenta
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

function Format-FileSize {
    param([long]$Bytes)
    if ($Bytes -ge 1TB) { return '{0:N2} TB' -f ($Bytes / 1TB) }
    if ($Bytes -ge 1GB) { return '{0:N2} GB' -f ($Bytes / 1GB) }
    if ($Bytes -ge 1MB) { return '{0:N2} MB' -f ($Bytes / 1MB) }
    if ($Bytes -ge 1KB) { return '{0:N2} KB' -f ($Bytes / 1KB) }
    return "$Bytes B"
}

function Test-WslPath {
    param(
        [string]$Distro,
        [string]$WslPath,
        [ValidateSet('File', 'Directory')][string]$Type = 'File'
    )
    $flag = if ($Type -eq 'Directory') { '-d' } else { '-f' }
    $result = wsl -d $Distro -- bash -c "[ $flag '$WslPath' ] && echo YES || echo NO" 2>$null
    return ($result.Trim() -eq 'YES')
}

function Read-WslTextFile {
    param([string]$Distro, [string]$WslPath)
    return wsl -d $Distro -- bash -c "cat '$WslPath'" 2>$null
}

function Test-IsJunction {
    param([string]$Path)
    if (-not (Test-Path $Path -PathType Container)) { return $false }
    try {
        $item = Get-Item $Path -Force -ErrorAction Stop
        return ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    } catch {
        return $false
    }
}

# ============================================================
# PATH TRANSLATION FUNCTION
# ============================================================

<#
.SYNOPSIS
    Translates WSL filesystem paths to Windows paths within file content.

.DESCRIPTION
    Applies these rules in order (first match wins):
    1. /mnt/<drive>/<rest> => <drive>:\<rest>
    2. $WslHome/.hermes/<rest> => $LocalAppData\hermes\<rest>
    3. $WslHome/vault-local/<rest> => $OneDriveVault\<rest>
    4. $WslHome/vault/<rest> => $OneDriveVault\<rest>
    5. $WslHome/<rest> => $WinUserProfile\<rest>
#>
function Convert-HermesPath {
    param(
        [string]$Content,
        [string]$WslHome,
        [string]$WinUserProfile,
        [string]$LocalAppData,
        [string]$OneDriveVault
    )

    $result = $Content
    if ([string]::IsNullOrEmpty($result)) { return $result }

    # Normalise WSL home — strip trailing slash
    $wh = $WslHome.TrimEnd('/')

    # Rule 1: /mnt/<drive>/<rest> => <drive>:\<rest>
    $result = [regex]::Replace($result, '/mnt/([a-zA-Z])/(.*)', {
        param($m)
        $drive = $m.Groups[1].Value.ToUpper()
        $rest = $m.Groups[2].Value
        "$drive`:$rest"
    })

    # Rule 2: $wh/.hermes/<rest> => LOCALAPPDATA\hermes\<rest>
    # Must be before the catch-all (rule 5).
    $pattern2 = "$wh/.hermes/"
    if ($result.Contains($pattern2)) {
        $result = $result.Replace($pattern2, "$LocalAppData\hermes\")
    }

    # Rule 3: $wh/vault-local/<rest> => OneDrive vault
    $pattern3 = "$wh/vault-local/"
    if ($result.Contains($pattern3)) {
        $result = $result.Replace($pattern3, "$OneDriveVault\")
    }

    # Rule 4: $wh/vault/<rest> => OneDrive vault
    $pattern4 = "$wh/vault/"
    if ($result.Contains($pattern4)) {
        $result = $result.Replace($pattern4, "$OneDriveVault\")
    }

    # Rule 5: $wh/<rest> => USERPROFILE\<rest>  (catch-all)
    $pattern5 = "$wh/"
    if ($result.Contains($pattern5)) {
        $result = $result.Replace($pattern5, "$WinUserProfile\")
    }

    return $result
}

# ============================================================
# BANNER
# ============================================================

Clear-Host
Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║           Hermes - WSL to Windows Migration Tool            ║
║           $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')                       ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "  DRY-RUN MODE — no changes will be made`n" -ForegroundColor Magenta
}

# ============================================================
# STEP 1: PRE-FLIGHT CHECKS
# ============================================================

Write-Header 'Step 1/8: Pre-flight checks'

# --- 1a. Check WSL availability ---
Write-SubHeader 'Checking WSL availability'
try {
    $null = Get-Command wsl -ErrorAction Stop
    Write-OK 'WSL is installed and available in PATH'
} catch {
    Write-Err 'WSL is not installed or not in PATH. Install WSL first.'
    exit 1
}

# --- 1b. Discover WSL distros ---
Write-SubHeader "Discovering WSL distros with Hermes data"
$allDistros = @(wsl -l -q 2>$null | ForEach-Object {
    ($_ -replace '\(Default\)', '').Trim()
} | Where-Object { $_ -ne '' })

if ($allDistros.Count -eq 0) {
    Write-Err 'No WSL distros found. Install a WSL distro first.'
    exit 1
}
Write-OK "Found $($allDistros.Count) WSL distro(s)"

# --- 1c. Find distros with ~/.hermes/ ---
$validDistros = @()
foreach ($d in $allDistros) {
    $exists = wsl -d $d -- bash -c '[ -d "$HOME/.hermes" ] && echo YES || echo NO' 2>$null
    if ($exists.Trim() -eq 'YES') {
        $validDistros += $d
    }
}

if ($validDistros.Count -eq 0) {
    Write-Err 'No WSL distros have ~/.hermes/ data. Nothing to migrate.'
    exit 1
}
Write-OK "Found $($validDistros.Count) distro(s) with Hermes data at ~/.hermes/"
foreach ($d in $validDistros) {
    Write-Info "    - $d"
}

# --- 1d. Select distro ---
$selectedDistro = $null
if ($validDistros.Count -eq 1) {
    $selectedDistro = $validDistros[0]
} elseif ($Force) {
    $selectedDistro = $validDistros[0]
    Write-Warn "Multiple distros found. Using first ($selectedDistro) because -Force is set."
} else {
    Write-Host "Multiple WSL distros have Hermes data. Please select one:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $validDistros.Count; $i++) {
        Write-Host "  [$i] $($validDistros[$i])" -ForegroundColor Gray
    }
    $selection = Read-Host "Enter number (0-$($validDistros.Count - 1))"
    $selectedDistro = $validDistros[[int]$selection]
}
Write-OK "Selected distro: $selectedDistro"

# --- 1e. Get WSL home and user ---
$wslHome = (wsl -d $selectedDistro -- bash -c 'echo "$HOME"' 2>$null).Trim()
if ([string]::IsNullOrEmpty($wslHome)) {
    Write-Err "Could not determine WSL home directory for distro '$selectedDistro'."
    exit 1
}
$wslUser = Split-Path -Leaf $wslHome
Write-OK "WSL home: $wslHome (user: $wslUser)"

# Ensure WSL distro is running (needed for UNC path access)
$null = wsl -d $selectedDistro -- bash -c 'exit' 2>$null

# --- 1f. Verify target directory ---
$hermesDest = if ($env:LOCALAPPDATA) {
    "$env:LOCALAPPDATA\hermes"
} else {
    "$env:USERPROFILE\AppData\Local\hermes"
}

if (-not (Test-Path $hermesDest)) {
    Write-Err "Target directory does not exist: $hermesDest"
    Write-Info 'Install Hermes for Windows first, or create the directory manually.'
    exit 1
}
Write-OK "Target: $hermesDest"

# --- 1g. Check disk space ---
Write-SubHeader 'Checking disk space'
try {
    $driveLetter = (Split-Path -Qualifier $hermesDest).TrimEnd(':')
    $freeBytes = (Get-PSDrive $driveLetter -ErrorAction Stop).Free
    $minFree = 500MB

    if ($freeBytes -lt $minFree) {
        $msg = "Low disk space on $driveLetter`: $(Format-FileSize $freeBytes) free, need $(Format-FileSize $minFree)"
        if ($Force) {
            Write-Warn "$msg (proceeding due to -Force)"
        } else {
            Write-Err "$msg"
            Write-Info 'Free up disk space or use -Force to proceed anyway.'
            exit 1
        }
    } else {
        Write-OK "Disk $driveLetter`: $(Format-FileSize $freeBytes) free (need $(Format-FileSize $minFree))"
    }
} catch {
    Write-Warn "Could not check disk space: $_"
}

# --- 1h. Check OneDrive environment variable ---
$oneDriveRoot = if ($env:OneDrive) {
    $env:OneDrive
} else {
    Write-Warn '$env:OneDrive is not set. Vault path translations may be incorrect.'
    "$env:USERPROFILE\OneDrive"
}
$oneDriveVault = Join-Path $oneDriveRoot "Dokument\Obsidian\Knowledge Base"

# --- 1i. Show Hermes data info from WSL ---
Write-SubHeader 'WSL Hermes data overview'
$sizeOutput = wsl -d $selectedDistro -- bash -c 'du -sh "$HOME/.hermes" 2>/dev/null || echo "unknown"' 2>$null
$countOutput = wsl -d $selectedDistro -- bash -c 'find "$HOME/.hermes" -type f 2>/dev/null | wc -l' 2>$null
$script:Stats.SourceSize = $sizeOutput.Trim()
$script:Stats.SourceFileCount = $countOutput.Trim()

Write-Info "Source size:  $($script:Stats.SourceSize)"
Write-Info "File count:   $($script:Stats.SourceFileCount)"

# Check which components exist
$componentsToCheck = @('config', 'sessions', 'skills', 'memory', 'auth', 'cron', 'profiles', 'plugins', 'inbox')
Write-Info 'Hermes components found:'
foreach ($c in $componentsToCheck) {
    if (Test-WslPath -Distro $selectedDistro -WslPath "~/.hermes/$c" -Type Directory) {
        Write-Host "    - $c" -ForegroundColor Green
    } else {
        Write-Host "    - $c (absent)" -ForegroundColor DarkGray
    }
}

# ============================================================
# STEP 2: BACKUP
# ============================================================

Write-Header 'Step 2/8: Backup existing installation'

if ($SkipBackup) {
    Write-Info 'Backup skipped (-SkipBackup)'
} elseif ($DryRun) {
    $backupName = "hermes-backup-DRYRUN-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-DryRun "Would create backup: $env:LOCALAPPDATA\$backupName"
    Write-DryRun 'Would use: robocopy "$hermesDest" "$env:LOCALAPPDATA\$backupName" /E /R:3 /W:2 /NP'
} else {
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupPath = "$env:LOCALAPPDATA\hermes-backup-$timestamp"

    Write-SubHeader "Creating backup at $backupPath"
    Write-Progress -Activity 'Backing up existing Hermes installation' -Status 'Running robocopy...' -PercentComplete -1

    try {
        $backupExitCode = & robocopy $hermesDest $backupPath /E /R:3 /W:2 /NP /NDL /NFL
        if ($LASTEXITCODE -ge 8) {
            throw "robocopy exited with code $LASTEXITCODE (error)"
        }
        Write-Progress -Activity 'Backing up' -Completed
        $script:Stats.BackupPath = $backupPath
        Write-OK "Backup created: $backupPath"

        # Show backup size
        $backupSize = (Get-ChildItem -Path $backupPath -Recurse | Measure-Object -Property Length -Sum).Sum
        Write-Info "Backup size: $(Format-FileSize $backupSize)"
    } catch {
        Write-Err "Backup failed: $_"
        if (-not $Force) {
            Write-Info 'Use -Force to continue without backup, or -SkipBackup to skip.'
            exit 1
        }
    }
}

# ============================================================
# BUILD SKIP LISTS & UNC PATHS
# ============================================================

# Directories to NEVER copy (skip list from specification)
$skipDirs = @(
    'hermes-agent', 'node', '.venv', 'bin', 'lsp', 'run',
    'backups', 'incident-backups', 'skill-backups',
    'tmp', 'sandboxes', 'plans', 'pastes',
    'gateway-turns', 'vault-safety', 'pairing', 'mcp-servers',
    'audio_cache', 'image_cache', 'bootstrap-cache'
)

# Files to NEVER copy
$skipFiles = @(
    'gateway.lock', 'gateway.pid', 'gateway-supervisor.heartbeat',
    'state.db-shm', 'state.db-wal',
    '.hermes_history', '.skills_prompt_snapshot.json', '.update_check',
    'context_length_cache.yaml', 'models_dev_cache.json',
    'ollama_cloud_models_cache.json', 'provider_models_cache.json',
    'interrupt_debug.log', 'auth.lock', 'hermes-setup.exe'
)

# Build UNC path for robocopy source
$wslRelHome = ($wslHome -replace '/', '\').TrimStart('\')
$uncBase = "\\wsl.localhost\$selectedDistro"
$uncHome = "$uncBase\$wslRelHome"
$sourceRoot = "$uncHome\.hermes"

# ============================================================
# STEP 3: TIER 1 — ESSENTIAL FILES (ROBOCOPY + TRANSLATION)
# ============================================================

Write-Header 'Step 3/8: Migrating essential files (Tier 1)'

if ($DryRun) {
    Write-DryRun "Would robocopy from: $sourceRoot"
    Write-DryRun "           to:   $hermesDest"
    Write-DryRun "Would then path-translate: .env, config.yaml, auth.json, SOUL.md, mcp.json, state.db, kanban.db"
} else {
    # --- 3a. Main robocopy (excludes skip list + Tier 3 dirs unless flagged) ---

    # Dynamically exclude Tier 3 dirs unless opted in
    $robocopyExcludeDirs = $skipDirs.Clone()
    if (-not $IncludeCheckpoints) { $robocopyExcludeDirs += 'checkpoints' }
    if (-not $IncludeSnapshots)   { $robocopyExcludeDirs += 'state-snapshots' }
    if (-not $IncludeLogs)        { $robocopyExcludeDirs += 'logs' }
    if (-not $IncludeCache)       { $robocopyExcludeDirs += 'cache' }
    if (-not $IncludeScripts)     { $robocopyExcludeDirs += 'scripts' }

    $robocopyArgs = @(
        $sourceRoot,
        $hermesDest,
        '/E',
        '/R:3',
        '/W:2',
        '/NP',
        '/NDL',
        '/NFL'
    )

    if ($robocopyExcludeDirs.Count -gt 0) {
        $robocopyArgs += '/XD'
        $robocopyArgs += $robocopyExcludeDirs
    }
    if ($skipFiles.Count -gt 0) {
        $robocopyArgs += '/XF'
        $robocopyArgs += $skipFiles
    }

    Write-SubHeader 'Running bulk copy (robocopy)'
    Write-Info "From: $sourceRoot"
    Write-Info "To:   $hermesDest"
    Write-Progress -Activity 'Bulk copying files from WSL' -Status 'Running robocopy...' -PercentComplete -1

    try {
        $robocopyExit = & robocopy @robocopyArgs
        if ($LASTEXITCODE -ge 8) {
            throw "robocopy failed with exit code $LASTEXITCODE"
        }
        Write-Progress -Activity 'Bulk copying files from WSL' -Completed
        $robocopyExitCode = $LASTEXITCODE
        Write-OK "Bulk copy complete (robocopy exit code: $robocopyExitCode)"
    } catch {
        Write-Err "Bulk copy failed: $_"
        Write-Info 'Continuing with individual file copies...'
    }

    # --- 3b. Tier 1 individual file copy with path translation ---

    $tier1Files = @(
        '.env', 'config.yaml', 'auth.json', 'SOUL.md', 'mcp.json', 'state.db', 'kanban.db'
    )

    Write-SubHeader 'Copying Tier 1 essential files with path translation'
    foreach ($file in $tier1Files) {
        $wslFilePath = "~/.hermes/$file"
        $destFilePath = Join-Path $hermesDest $file

        if (-not (Test-WslPath -Distro $selectedDistro -WslPath $wslFilePath -Type File)) {
            if ($file -eq 'kanban.db') {
                Write-Info "    kanban.db not found in source, skipping"
            } else {
                Write-Warn "Required file not found in WSL: $wslFilePath"
            }
            continue
        }

        $isText = $file -match '\.(env|yaml|yml|json|md)$'

        if ($isText) {
            # Read, translate, write
            $original = Read-WslTextFile -Distro $selectedDistro -WslPath $wslFilePath
            if ([string]::IsNullOrEmpty($original)) {
                Write-Warn "Empty or unreadable file: $wslFilePath"
                continue
            }
            $translated = Convert-HermesPath -Content $original -WslHome $wslHome `
                -WinUserProfile $env:USERPROFILE -LocalAppData $env:LOCALAPPDATA `
                -OneDriveVault $oneDriveVault

            [System.IO.File]::WriteAllText($destFilePath, $translated)

            if ($translated -ne $original) {
                $script:Stats.PathTranslations++
            }
            $script:Stats.FilesMigrated++
            Write-OK "$file — copied with path translation"
        } else {
            # Binary file (state.db, kanban.db) — copy via UNC if not copied by robocopy
            $uncFile = "$sourceRoot\$file"
            if (Test-Path $uncFile) {
                if (-not (Test-Path $destFilePath)) {
                    Copy-Item $uncFile $destFilePath -Force
                }
                $script:Stats.FilesMigrated++
                Write-OK "$file — copied (binary)"
            } else {
                Write-Warn "$file not found at UNC path: $uncFile"
            }
        }
    }
}

# ============================================================
# STEP 4: TIER 2 — PATH TRANSLATION IN IMPORTANT DIRECTORIES
# ============================================================

Write-Header 'Step 4/8: Path-translating config files (Tier 2)'

# Apply path translation to config files within standard directories
$tier2Dirs = @('sessions', 'memories', 'skills', 'hooks', 'cron', 'inbox', 'plugins')

# Include 'profiles' if it exists at the destination
if (Test-Path (Join-Path $hermesDest 'profiles')) { $tier2Dirs += 'profiles' }

# Scan for auth-related directories
$authDirs = Get-ChildItem -Path $hermesDest -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'auth|credential|secret|token|key' } |
    ForEach-Object { $_.Name }
if ($authDirs.Count -gt 0) {
    Write-Info "Found auth-related directories: $($authDirs -join ', ')"
    $tier2Dirs += $authDirs
}

# Translate root-level mcp.json
$mcpJsonPath = Join-Path $hermesDest 'mcp.json'
if (Test-Path $mcpJsonPath) {
    $tier2Files = @($mcpJsonPath)
} else {
    $tier2Files = @()
}

# Gather all config files from Tier 2 directories
foreach ($dir in $tier2Dirs) {
    $dirPath = Join-Path $hermesDest $dir
    if (Test-Path $dirPath) {
        $configs = Get-ChildItem -Path $dirPath -Recurse -Include '*.yaml', '*.yml', '*.json', '*.md' -ErrorAction SilentlyContinue
        $tier2Files += $configs.FullName
    }
}

if ($DryRun) {
    Write-DryRun "Would scan $($tier2Dirs.Count) directories for config files needing path translation"
    Write-DryRun "Would also process: mcp.json"

    # In dry-run, count files that would need translation
    $dryRunCount = 0
    foreach ($f in $tier2Files) {
        if (Test-Path $f) {
            $content = Get-Content -Path $f -Raw -ErrorAction SilentlyContinue
            if ($content) {
                $translated = Convert-HermesPath -Content $content -WslHome $wslHome `
                    -WinUserProfile $env:USERPROFILE -LocalAppData $env:LOCALAPPDATA `
                    -OneDriveVault $oneDriveVault
                if ($translated -ne $content) {
                    $dryRunCount++
                }
            }
        }
    }
    Write-DryRun "Would translate approximately $dryRunCount file(s)"
} else {
    $tier2TranslationCount = 0
    $tier2FileCount = $tier2Files.Count
    $tier2Idx = 0

    foreach ($f in $tier2Files) {
        $tier2Idx++
        $relPath = $f.Substring($hermesDest.Length).TrimStart('\')
        Write-Progress -Activity 'Translating paths in Tier 2 config files' `
            -Status $relPath `
            -PercentComplete (($tier2Idx / [math]::Max(1, $tier2FileCount)) * 100)

        try {
            $original = Get-Content -Path $f -Raw -ErrorAction Stop
            if ([string]::IsNullOrEmpty($original)) { continue }

            $translated = Convert-HermesPath -Content $original -WslHome $wslHome `
                -WinUserProfile $env:USERPROFILE -LocalAppData $env:LOCALAPPDATA `
                -OneDriveVault $oneDriveVault

            if ($translated -ne $original) {
                [System.IO.File]::WriteAllText($f, $translated)
                $tier2TranslationCount++
                $script:Stats.PathTranslations++
            }
        } catch {
            Write-Warn "Could not process $relPath : $_"
        }
    }
    Write-Progress -Activity 'Translating paths in Tier 2 config files' -Completed
    Write-OK "Path-translated $tier2TranslationCount config file(s) in Tier 2 directories"
}

# ============================================================
# STEP 5: JUNCTION
# ============================================================

Write-Header 'Step 5/8: Creating skills-shared junction'

$junctionPath = Join-Path $hermesDest 'skills-shared'
$junctionTarget = Join-Path $oneDriveVault '.agents\skills'

if ($DryRun) {
    Write-DryRun "Would create junction:"
    Write-DryRun "  $junctionPath => $junctionTarget"
} else {
    $existingIsJunction = Test-IsJunction $junctionPath

    if ($existingIsJunction) {
        Write-OK "skills-shared junction already exists, skipping"
    } else {
        # Remove whatever is there (file or dir) if anything
        if (Test-Path $junctionPath) {
            try {
                Remove-Item -Path $junctionPath -Force -Recurse -Confirm:$false -ErrorAction Stop
                Write-Info "Removed existing item at $junctionPath"
            } catch {
                Write-Err "Could not remove existing item at $junctionPath : $_"
                continue  # skip junction creation but continue script
            }
        }

        try {
            if (-not (Test-Path $junctionTarget)) {
                Write-Warn "Junction target does not exist: $junctionTarget"
                Write-Info 'The junction will be created anyway (pointing to a non-existent target).'
            }
            $null = New-Item -ItemType Junction -Path $junctionPath -Target $junctionTarget -Force -ErrorAction Stop
            Write-OK "skills-shared junction created: $junctionPath => $junctionTarget"
        } catch {
            Write-Err "Failed to create junction: $_"
        }
    }
}

# ============================================================
# STEP 6: TIER 3 — OPT-IN COMPONENTS
# ============================================================

Write-Header 'Step 6/8: Processing opt-in components (Tier 3)'

$tier3Flags = @(
    @{ Name = 'Checkpoints'; Flag = $IncludeCheckpoints; Dir = 'checkpoints' }
    @{ Name = 'Snapshots';   Flag = $IncludeSnapshots;   Dir = 'state-snapshots' }
    @{ Name = 'Logs';        Flag = $IncludeLogs;        Dir = 'logs' }
    @{ Name = 'Cache';       Flag = $IncludeCache;       Dir = 'cache' }
    @{ Name = 'Scripts';     Flag = $IncludeScripts;     Dir = 'scripts' }
)

$tier3AnyIncluded = $false
foreach ($t3 in $tier3Flags) {
    if (-not $t3.Flag) {
        Write-Info "    $($t3.Name) excluded (use -Include$($t3.Name) to include)"
        continue
    }
    $tier3AnyIncluded = $true
    $srcT3Dir = "$sourceRoot\$($t3.Dir)"
    $dstT3Dir = Join-Path $hermesDest $t3.Dir

    if ($DryRun) {
        $exists = Test-WslPath -Distro $selectedDistro -WslPath "~/.hermes/$($t3.Dir)" -Type Directory
        if ($exists) {
            Write-DryRun "Would copy: $($t3.Dir)/ from WSL to $dstT3Dir"
        } else {
            Write-DryRun "$($t3.Name) requested but directory not found in WSL source"
        }
        continue
    }

    # Check if directory exists in WSL source
    $wslT3Exists = Test-WslPath -Distro $selectedDistro -WslPath "~/.hermes/$($t3.Dir)" -Type Directory
    if (-not $wslT3Exists) {
        Write-Warn "$($t3.Name) flagged but directory does not exist in WSL source (skipping)"
        continue
    }

    Write-SubHeader "Copying $($t3.Name) ($($t3.Dir)/)"
    Write-Progress -Activity "Copying $($t3.Name)" -Status 'Running robocopy...' -PercentComplete -1

    try {
        $t3Exit = & robocopy "$srcT3Dir" $dstT3Dir /E /R:3 /W:2 /NP /NDL /NFL
        if ($LASTEXITCODE -ge 8) {
            throw "robocopy failed with exit code $LASTEXITCODE"
        }
        Write-Progress -Activity "Copying $($t3.Name)" -Completed
        Write-OK "$($t3.Name) copied successfully"

        # Apply path translation to config files within this Tier 3 directory
        $configFiles = Get-ChildItem -Path $dstT3Dir -Recurse -Include '*.yaml', '*.yml', '*.json', '*.md' -ErrorAction SilentlyContinue
        foreach ($cf in $configFiles) {
            $cfContent = Get-Content -Path $cf.FullName -Raw -ErrorAction SilentlyContinue
            if ($cfContent) {
                $cfTranslated = Convert-HermesPath -Content $cfContent -WslHome $wslHome `
                    -WinUserProfile $env:USERPROFILE -LocalAppData $env:LOCALAPPDATA `
                    -OneDriveVault $oneDriveVault
                if ($cfTranslated -ne $cfContent) {
                    [System.IO.File]::WriteAllText($cf.FullName, $cfTranslated)
                    $script:Stats.PathTranslations++
                }
            }
        }
    } catch {
        Write-Err "Failed to copy $($t3.Name): $_"
    }
}

if (-not $tier3AnyIncluded -and -not $DryRun) {
    Write-Info 'No opt-in components selected. Use -IncludeCheckpoints, -IncludeSnapshots, -IncludeLogs, -IncludeCache, or -IncludeScripts.'
}

# ============================================================
# STEP 7: VALIDATION
# ============================================================

Write-Header 'Step 7/8: Validation'

$validationErrors = 0
$validationWarnings = 0

if ($DryRun) {
    Write-DryRun 'Validation skipped in dry-run mode (no changes applied).'
} else {
    # --- 7a. Tier 1 file existence ---
    Write-SubHeader 'Verifying Tier 1 file existence'
    $essentialFiles = @('.env', 'config.yaml', 'auth.json', 'SOUL.md', 'mcp.json', 'state.db')
    foreach ($f in $essentialFiles) {
        $fp = Join-Path $hermesDest $f
        if (Test-Path $fp) {
            $size = (Get-Item $fp).Length
            Write-OK "$f exists ($(Format-FileSize $size))"
        } else {
            Write-Err "MISSING: $f"
            $validationErrors++
        }
    }

    # --- 7b. Size comparison for state.db ---
    Write-SubHeader 'Comparing state.db size'
    $wslStateDbSize = wsl -d $selectedDistro -- bash -c 'stat -c%s "$HOME/.hermes/state.db" 2>/dev/null || echo 0' 2>$null
    $winStateDbPath = Join-Path $hermesDest 'state.db'
    if (Test-Path $winStateDbPath) {
        $winStateDbSize = (Get-Item $winStateDbPath).Length
        $wslSizeNum = [int64]($wslStateDbSize.Trim())
        $sizeDiff = [math]::Abs($wslSizeNum - $winStateDbSize)
        $diffThreshold = 1MB

        if ($sizeDiff -le $diffThreshold) {
            Write-OK "state.db size match: WSL=$($wslStateDbSize.Trim()), Windows=$(Format-FileSize $winStateDbSize)"
        } else {
            Write-Warn "state.db size mismatch: WSL=$($wslStateDbSize.Trim()), Windows=$(Format-FileSize $winStateDbSize) (diff: $(Format-FileSize $sizeDiff))"
            $validationWarnings++
        }
    }

    # --- 7c. SQLite integrity check ---
    Write-SubHeader 'Running SQLite integrity check'
    $sqlitePath = (Get-Command sqlite3 -ErrorAction SilentlyContinue).Source
    if ($sqlitePath) {
        try {
            $dbPath = Join-Path $hermesDest 'state.db'
            if (Test-Path $dbPath) {
                $integrityResult = & sqlite3 $dbPath 'PRAGMA integrity_check;' 2>$null
                if ($integrityResult.Trim() -eq 'ok') {
                    Write-OK 'state.db integrity check passed'
                } else {
                    Write-Err "state.db integrity check failed: $integrityResult"
                    $validationErrors++
                }
            }
        } catch {
            Write-Warn "SQLite check failed: $_"
            $validationWarnings++
        }
    } else {
        Write-Warn 'sqlite3 not found in PATH — skipping database integrity check'
        $validationWarnings++
    }

    # --- 7d. Grep for remaining WSL paths ---
    Write-SubHeader 'Checking for stale WSL paths in config files'
    $configFilesToCheck = @('config.yaml', 'mcp.json') | ForEach-Object { Join-Path $hermesDest $_ }
    $stalePathsFound = 0
    $wslPathPatterns = @(
        "/mnt/[a-zA-Z]/",
        "$wslHome/"
    )

    foreach ($cf in $configFilesToCheck) {
        if (-not (Test-Path $cf)) { continue }
        $content = Get-Content -Path $cf -Raw -ErrorAction SilentlyContinue
        if (-not $content) { continue }

        foreach ($pattern in $wslPathPatterns) {
            if ($content -match $pattern) {
                $relName = Split-Path -Leaf $cf
                $matches = [regex]::Matches($content, $pattern)
                Write-Warn "$relName contains $($matches.Count) occurrence(s) of '$pattern'"
                $stalePathsFound++
                $validationWarnings++
            }
        }
    }

    if ($stalePathsFound -eq 0) {
        Write-OK 'No stale WSL paths found in config.yaml or mcp.json'
    }

    # --- 7e. Verify junction ---
    Write-SubHeader 'Verifying skills-shared junction'
    if (Test-IsJunction $junctionPath) {
        Write-OK "skills-shared junction is valid"
    } else {
        Write-Warn "skills-shared junction is missing or not a reparse point"
        $validationWarnings++
    }
}

# ============================================================
# STEP 8: REPORT
# ============================================================

Write-Header 'Step 8/8: Migration report'

$elapsed = (Get-Date) - $script:Stats.StartTime
$duration = '{0:mm}m {0:ss}s' -f $elapsed

@"
Migration Summary
─────────────────
Date:              $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Duration:          $duration
Source (WSL):      $selectedDistro:$wslHome/.hermes ($($script:Stats.SourceSize), $($script:Stats.SourceFileCount) files)
Destination:       $hermesDest
Dry-run:           $DryRun

── Files & Translations ──
Files migrated:        $($script:Stats.FilesMigrated)
Path translations:     $($script:Stats.PathTranslations)
Skipped items:         $($script:Stats.SkippedItems)

── Warnings ──
"@ -split "`n" | ForEach-Object { Write-Host $_ -ForegroundColor Gray }

if ($script:Stats.Warnings.Count -eq 0) {
    Write-OK 'No warnings'
} else {
    foreach ($w in $script:Stats.Warnings) {
        Write-Warn $w
    }
}

Write-Host "`n── Errors ──" -ForegroundColor Gray
if ($script:Stats.Errors.Count -eq 0) {
    Write-OK 'No errors'
} else {
    foreach ($e in $script:Stats.Errors) {
        Write-Err $e
    }
}

if ($script:Stats.BackupPath) {
    Write-Host "`n── Backup ──" -ForegroundColor Gray
    Write-Info "Previous installation backed up to: $($script:Stats.BackupPath)"
}

Write-Host "`n── Next Steps ──" -ForegroundColor Gray
if (-not $DryRun) {
    Write-Info '1. Start Hermes for Windows and verify it loads correctly'
    Write-Info '2. Check that sessions, skills, and memories are accessible'
    Write-Info '3. If everything works, the WSL Hermes data can be archived:'
    Write-Info "   wsl -d $selectedDistro -- mv ~/.hermes ~/.hermes.migrated-$(Get-Date -Format 'yyyyMMdd')"
    Write-Info '4. To roll back: restore from the backup directory'
} else {
    Write-Info 'No changes were made (dry-run mode). Re-run without -DryRun to apply.'
}

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║  Migration $((if ($DryRun) {'PREVIEW COMPLETE'} else {'COMPLETE'}))$(if ($DryRun) {', no changes made'} else {''})            ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Exit with appropriate code
if ($script:Stats.Errors.Count -gt 0) { exit 1 }
exit 0
