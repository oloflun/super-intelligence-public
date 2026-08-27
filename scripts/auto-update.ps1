# Super-Intelligence Stack — Daily Auto-Update + Health Check (Windows)
# Called by Task Scheduler.
# Idempotent. Read-only health checks run even when no update is pulled.
param()

$ErrorActionPreference = "Continue"
$configDir = Join-Path $HOME ".super-intelligence"
$configFile = Join-Path $configDir "config.json"

if (-not (Test-Path $configFile)) { exit 0 }

# ── Read config ───────────────────────────────────────────────────────────────
try {
    $config = Get-Content $configFile -Raw | ConvertFrom-Json
} catch {
    Write-Output "[$(Get-Date -Format o)] ERROR: cannot parse config.json"
    exit 1
}

$autoUpdate = if ($config.auto_update) { $config.auto_update } else { $false }
$repoPath = $config.repo_path
$vaultPath = $config.vault_path
$logFile = if ($config.update_log) { $config.update_log } else { Join-Path $configDir "update.log" }

New-Item -ItemType Directory -Force -Path $configDir | Out-Null
if (-not (Test-Path $logFile)) { New-Item -ItemType File -Path $logFile -Force | Out-Null }

function log($msg) { "[$(Get-Date -Format o)] $msg" | Out-File $logFile -Append }

# ── Validate repo path ────────────────────────────────────────────────────────
if (-not $repoPath -or -not (Test-Path (Join-Path $repoPath ".git"))) {
    $err = "ERROR: repo_path missing or not a git repo: $repoPath"
    Write-Output $err; log $err
    exit 1
}

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1: UPDATE CHECK
# ══════════════════════════════════════════════════════════════════════════════
$didUpdate = $false

if ($autoUpdate) {
    Write-Output "`n── Fetching updates ──"
    Push-Location $repoPath
    try {
        git fetch origin 2>&1 | Out-File $logFile -Append

        $local = (git rev-parse HEAD 2>$null).Trim()
        $remote = (git rev-parse origin/main 2>$null).Trim()

        if (-not $local -or -not $remote) {
            Write-Output "[WARN] Could not determine git SHAs"
        } elseif ($local -eq $remote) {
            $short = (git log -1 --format=%h 2>$null).Trim()
            Write-Output "[ok] Already up to date ($short)"
            log "INFO: up to date"
        } else {
            Write-Output "Pulling $($local.Substring(0,7)) -> $($remote.Substring(0,7))"
            log "UPDATE: $local -> $remote"

            $pullResult = git pull --ff-only origin main 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Output "[ok] git pull succeeded"
                $didUpdate = $true
            } else {
                Write-Output "[XX] git pull failed — local diverged. Manual intervention needed."
                log "ERROR: git pull --ff-only failed"
            }

            if ($didUpdate -and (Test-Path "upgrade.mjs")) {
                Write-Output "`n── Running upgrade.mjs ──"
                try {
                    node upgrade.mjs 2>&1 | Out-File $logFile -Append
                    Write-Output "[ok] upgrade.mjs completed"
                    log "upgrade.mjs executed"
                } catch {
                    Write-Output "[WARN] upgrade.mjs had issues (check log)"
                }
            }
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Output "[INFO] auto_update disabled — skipping git fetch/pull"
}

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2: HEALTH CHECKS
# ══════════════════════════════════════════════════════════════════════════════

# ── 2.1 Package Health ───────────────────────────────────────────────────────
Write-Output "`n── Package Health ──"
$pkgPass = 0; $pkgFail = 0
$healthMjs = Join-Path $repoPath "scripts\health-check.mjs"
if (Test-Path $healthMjs) {
    try {
        $out = node $healthMjs 2>&1
        $pkgPass = ($out | Select-String "\[ok\]" | Measure-Object).Count
        $pkgFail = ($out | Select-String "\[XX\]" | Measure-Object).Count
        if ($pkgFail -eq 0) {
            Write-Output "[ok] health-check.mjs: $pkgPass/$pkgPass passed"
        } else {
            Write-Output "[XX] health-check.mjs: $pkgPass passed, $pkgFail failed"
        }
    } catch {
        Write-Output "[WARN] health-check.mjs failed"
    }
}

# ── 2.2 Installation Health ──────────────────────────────────────────────────
Write-Output "`n── Installation Health ──"
$instPass = 0; $instFail = 0
$verifyMjs = Join-Path $repoPath "scripts\verify-install.mjs"
if (Test-Path $verifyMjs) {
    try {
        $out = node $verifyMjs 2>&1
        $instPass = ($out | Select-String "\[ok\]" | Measure-Object).Count
        $instFail = ($out | Select-String "\[XX\]" | Measure-Object).Count
        if ($instFail -eq 0) {
            Write-Output "[ok] verify-install.mjs: $instPass/$instPass passed"
        } else {
            Write-Output "[XX] verify-install.mjs: $instPass passed, $instFail failed"
        }
    } catch {
        Write-Output "[WARN] verify-install.mjs failed"
    }
}

# ── 2.3 MCP Health ───────────────────────────────────────────────────────────
Write-Output "`n── MCP Servers ──"
$mcpJsonPath = Join-Path $HOME ".mcp.json"
$mcpOk = 0; $mcpFail = 0; $mcpTotal = 0
if (Test-Path $mcpJsonPath) {
    try {
        $mcp = Get-Content $mcpJsonPath -Raw | ConvertFrom-Json
        $servers = $mcp.mcpServers | Get-Member -MemberType NoteProperty
        foreach ($srv in $servers) {
            $name = $srv.Name
            $cmd = $mcp.mcpServers.$name.command
            $mcpTotal++
            if (-not $cmd) {
                Write-Output "[WARN] $name : no command configured"
            } elseif (Get-Command $cmd -ErrorAction SilentlyContinue) {
                Write-Output "[ok] $name : $cmd"
                $mcpOk++
            } else {
                # Try basename
                $baseName = Split-Path $cmd -Leaf
                if (Get-Command $baseName -ErrorAction SilentlyContinue) {
                    Write-Output "[ok] $name : $baseName"
                    $mcpOk++
                } else {
                    Write-Output "[XX] $name : command not found — $cmd"
                    $mcpFail++
                }
            }
        }
    } catch {
        Write-Output "[WARN] Cannot parse .mcp.json"
    }
}
if ($mcpTotal -eq 0) {
    Write-Output "[WARN] No MCP servers configured in ~/.mcp.json"
} else {
    Write-Output "  $mcpOk OK, $mcpFail failed out of $mcpTotal total"
}

# ── 2.4 CARL Health ──────────────────────────────────────────────────────────
Write-Output "`n── CARL ──"
$carlJsonPath = $null
foreach ($cand in @((Join-Path $HOME ".carl\carl.json"), (Join-Path $vaultPath ".carl\carl.json"))) {
    if (Test-Path $cand) { $carlJsonPath = $cand; break }
}

if ($carlJsonPath) {
    try {
        $carl = Get-Content $carlJsonPath -Raw | ConvertFrom-Json
        $domainCount = ($carl.domains | Get-Member -MemberType NoteProperty | Measure-Object).Count
        $ruleCount = 0; $decCount = 0; $activeCount = 0
        foreach ($dom in ($carl.domains | Get-Member -MemberType NoteProperty)) {
            $d = $carl.domains.$($dom.Name)
            if ($d.rules) { $ruleCount += $d.rules.Count }
            if ($d.decisions) { $decCount += $d.decisions.Count }
            if ($d.state -eq "active") { $activeCount++ }
        }
        Write-Output "[ok] carl.json: $domainCount domains, $ruleCount rules, $decCount decisions ($activeCount active)"

        foreach ($dom in ($carl.domains | Get-Member -MemberType NoteProperty | Sort-Object Name)) {
            $d = $carl.domains.$($dom.Name)
            $rCount = if ($d.rules) { $d.rules.Count } else { 0 }
            Write-Output "  ${_C}$($dom.Name): $rCount rules, state=$($d.state)${_R}"
        }
    } catch {
        Write-Output "[WARN] carl.json parse error"
    }
} else {
    Write-Output "[XX] carl.json not found"
}

# Hook
$carlHook = Join-Path $HOME ".claude\hooks\carl-hook.py"
if (Test-Path $carlHook) {
    try {
        $hookContent = Get-Content $carlHook -Raw
        $hookVer = if ($hookContent -match 'CARL_HOOK_VERSION=([\d.]+)') { $Matches[1] } else { "unknown" }
        Write-Output "[ok] carl-hook.py v$hookVer"
    } catch {
        Write-Output "[ok] carl-hook.py present"
    }
} else {
    Write-Output "[XX] carl-hook.py missing"
}

# Hook wiring
$settingsPath = Join-Path $HOME ".claude\settings.json"
if (Test-Path $settingsPath) {
    $settingsContent = Get-Content $settingsPath -Raw
    if ($settingsContent -match "carl-hook\.py") {
        Write-Output "[ok] carl-hook.py wired in settings.json"
    } else {
        Write-Output "[XX] carl-hook.py NOT wired in settings.json"
    }
} else {
    Write-Output "[WARN] ~/.claude/settings.json not found"
}

# ── 2.5 Repos Health ─────────────────────────────────────────────────────────
Write-Output "`n── Repos ──"
Push-Location $repoPath
try {
    $dirty = (git status --porcelain 2>$null | Measure-Object -Line).Lines
    $behind = try { [int](git rev-list --count HEAD..origin/main 2>$null) } catch { 0 }
    $ahead = try { [int](git rev-list --count origin/main..HEAD 2>$null) } catch { 0 }
    $branch = (git branch --show-current 2>$null).Trim()
    $commit = (git log -1 --format=%h 2>$null).Trim()

    $statusStr = ""
    if ($dirty -gt 0) { $statusStr += "[WARN] $dirty dirty files " }
    if ($behind -gt 0) { $statusStr += "[WARN] $behind behind " }
    if ($ahead -gt 0) { $statusStr += "[WARN] $ahead ahead " }
    if (-not $statusStr) { $statusStr = "[ok] clean" }
    Write-Output "  super-intelligence $commit ($branch): $statusStr"
} finally {
    Pop-Location
}

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
Write-Output ""
Write-Output "═══ Summary ═══"

$totalFail = 0
if ($pkgFail -gt 0) { $totalFail++ }
if ($instFail -gt 0) { $totalFail++ }
if ($mcpFail -gt 0) { $totalFail++ }

if ($totalFail -eq 0) {
    Write-Output "ALL CLEAN"
} else {
    Write-Output "$totalFail component(s) failed"
    Write-Output "Run: node install.mjs --force"
}

# Update last_check
try {
    $config.last_check = (Get-Date -Format o)
    $config | ConvertTo-Json | Set-Content $configFile
} catch { }
log "auto-update complete: $totalFail failures"
