#!/usr/bin/env node
/**
 * Super-Intelligence Agent Stack — Upgrade Script
 *
 * Non-destructive upgrade. Diffs current configs against package templates
 * and applies updates without touching personal data.
 *
 * Usage: node upgrade.mjs [--dry-run]
 */

import { execSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync, statSync, copyFileSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const HOME = homedir();
const PKG = __dirname;
const DRY = process.argv.includes("--dry-run");

const C = { green: "\x1b[32m", yellow: "\x1b[33m", red: "\x1b[31m", cyan: "\x1b[36m", reset: "\x1b[0m" };

function sh(cmd, opts = {}) {
  if (DRY) { console.log(`DRY: ${cmd}`); return ""; }
  try { return execSync(cmd, { encoding: "utf-8", stdio: opts.quiet ? "pipe" : "inherit", ...opts }); }
  catch (e) { if (!opts.ok) throw e; return ""; }
}

function getVersion() {
  try { return readFileSync(join(PKG, "VERSION"), "utf-8").trim(); } catch { return "unknown"; }
}

function getCurrentVault() {
  // Read from existing carl.json or CLAUDE.md to find vault path
  const carlLink = join(HOME, ".carl", "carl.json");
  if (existsSync(carlLink)) {
    try {
      const c = JSON.parse(readFileSync(carlLink, "utf-8"));
      // Vault path can be inferred — for now, ask
    } catch {}
  }
  // Fall back to common locations
  const candidates = [
    join(HOME, "Obsidian", "Knowledge Base"),
    join(HOME, "OneDrive", "Dokument", "Obsidian", "Knowledge Base"),
    join(HOME, "Documents", "Obsidian", "Knowledge Base"),
  ];
  for (const c of candidates) {
    if (existsSync(join(c, ".carl", "carl.json"))) return c;
  }
  return null;
}

function backupFile(path) {
  if (!existsSync(path)) return;
  const bak = path + ".bak-" + Date.now();
  if (!DRY) writeFileSync(bak, readFileSync(path));
  console.log(`${C.yellow}[bak]${C.reset} ${path} -> ${bak}`);
}

// The 8 design-hook registrations. Mirrors install.mjs's copy of the same
// data — duplicated rather than shared, matching this package's existing
// convention of self-contained scripts with no cross-file imports.
function designHookRegistrations(homeF) {
  const py = script => `python "${homeF}/.claude/hooks/${script}"`;
  return [
    { event: "UserPromptSubmit", matcher: null, script: "design-intent.py", timeout: 10 },
    { event: "PreToolUse", matcher: "Write|Edit|MultiEdit|NotebookEdit", script: "design-gate.py", timeout: 30 },
    // Widened 0.4.5: the verify gate has to fire on the Chrome extension too,
    // not only the built-in browser pane.
    { event: "PreToolUse", matcher: "(mcp__Claude_Browser__|mcp__claude-in-chrome__).*", script: "design-verify-gate.py", timeout: 8 },
    { event: "PostToolUse", matcher: "Write|Edit|MultiEdit|NotebookEdit", script: "design-route.py", timeout: 35 },
    { event: "PostToolUse", matcher: "Skill", script: "design-telemetry.py", timeout: 8 },
    // New in 0.4.5. Vision tracking records when a rendered image actually
    // enters context; design-stop.py blocks the session end when UI edits exist
    // that nothing looked at afterwards, and it needs this to know.
    { event: "PostToolUse", matcher: "Read", script: "design-vision-track.py", timeout: 8 },
    // New in 0.4.5. Without it, .once-* / .design-verb / .stop-signature never
    // clear, so "once per session" silently means "once per project, forever".
    { event: "SessionStart", matcher: null, script: "design-session-start.py", timeout: 10 },
    { event: "Stop", matcher: null, script: "design-stop.py", timeout: 120 },
  ].map(r => ({ ...r, command: py(r.script) }));
}

// Additively wires the design hooks into an existing settings.json. Never
// touches a hook block the user already has (carl-hook.py, deepclaude-
// pretool.py, third-party MCP hooks, ...) — each design hook is checked by
// command substring across the WHOLE event array before being appended, so
// running this repeatedly across versions is a no-op once wired.
function mergeDesignHooksIntoSettings(settingsPath) {
  if (!existsSync(settingsPath)) return { changed: 0, present: false };
  let settings;
  try { settings = JSON.parse(readFileSync(settingsPath, "utf-8")); }
  catch (e) { console.log(`${C.yellow}[!]${C.reset} settings.json unreadable, skipping hook merge: ${e.message}`); return { changed: 0, present: true, error: true }; }

  const homeF = HOME.replace(/\\/g, "/");
  const hooks = settings.hooks || (settings.hooks = {});
  let changed = 0;

  for (const reg of designHookRegistrations(homeF)) {
    const arr = hooks[reg.event] || (hooks[reg.event] = []);
    const existing = arr.find(block => (block.hooks || []).some(h => (h.command || "").includes(reg.script)));
    if (existing) {
      // Already wired — but a matcher can WIDEN between versions, and a plain
      // presence check would leave the old one in place forever. 0.4.5 widened
      // design-verify-gate to cover the Chrome extension; without this an
      // upgrade from 0.4.4 keeps firing on the pane only. Only ever touch a
      // block we recognise as ours.
      if (reg.matcher && existing.matcher && existing.matcher !== reg.matcher) {
        existing.matcher = reg.matcher;
        changed++;
      }
      continue;
    }
    const block = { hooks: [{ type: "command", command: reg.command, timeout: reg.timeout }] };
    if (reg.matcher) block.matcher = reg.matcher;
    arr.push(block);
    changed++;
  }

  if (changed > 0) {
    backupFile(settingsPath);
    if (!DRY) writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n", "utf-8");
  }
  return { changed, present: true };
}

const SYNC_SKIP = new Set(["node_modules", ".git"]);

/**
 * Content-aware one-way sync: copy files missing at dst (added) and files whose
 * bytes differ (updated). Never deletes dst-only files. DRY mode walks + counts
 * without writing. Returns {added, updated, same} or null if src doesn't exist.
 */
function syncDirContentAware(src, dst) {
  if (!existsSync(src)) return null;
  const stats = { added: 0, updated: 0, same: 0 };
  const walk = (s, d) => {
    for (const name of readdirSync(s)) {
      if (SYNC_SKIP.has(name)) continue;
      const sp = join(s, name), dp = join(d, name);
      if (statSync(sp).isDirectory()) { walk(sp, dp); continue; }
      if (!existsSync(dp)) {
        if (!DRY) { mkdirSync(dirname(dp), { recursive: true }); copyFileSync(sp, dp); }
        stats.added++;
      } else if (!readFileSync(sp).equals(readFileSync(dp))) {
        if (!DRY) copyFileSync(sp, dp);
        stats.updated++;
      } else {
        stats.same++;
      }
    }
  };
  walk(src, dst);
  return stats;
}

async function main() {
  const newVer = getVersion();
  console.log(`\nSuper-Intelligence Upgrade — to v${newVer}\n`);

  const vault = getCurrentVault();
  if (!vault) {
    console.error("Could not find vault. Set SI_VAULT environment variable.");
    process.exit(1);
  }
  console.log(`Vault: ${vault}\n`);

  let changes = 0;

  // 1. Update carl.json — merge new domains/rules, preserve existing
  const srcCarl = join(PKG, "carl", "carl.json");
  const dstCarl = join(vault, ".carl", "carl.json");
  if (existsSync(srcCarl) && existsSync(dstCarl)) {
    try {
      const src = JSON.parse(readFileSync(srcCarl, "utf-8"));
      const dst = JSON.parse(readFileSync(dstCarl, "utf-8"));

      // Merge new domains (don't overwrite existing)
      for (const [name, domain] of Object.entries(src.domains || {})) {
        if (!dst.domains[name]) {
          dst.domains[name] = domain;
          console.log(`${C.green}[+]${C.reset} CARL domain: ${name}`);
          changes++;
        }
      }

      // Update existing domains: append missing rules (matched by TEXT — ids are
      // per-install sequential and collide) and missing decisions (string ids).
      const norm = t => String(t || "").trim().toLowerCase();
      for (const [name, domain] of Object.entries(src.domains || {})) {
        if (!dst.domains[name]) continue;
        const d = dst.domains[name];
        d.rules = d.rules || [];
        const haveRule = new Set(d.rules.map(r => norm(r.text ?? r)));
        for (const rule of (domain.rules || [])) {
          if (haveRule.has(norm(rule.text ?? rule))) continue;
          const nextId = d.rules.reduce((m, r) => Math.max(m, (r.id ?? -1) + 1), 0);
          d.rules.push(typeof rule === "object" ? { ...rule, id: nextId } : { id: nextId, text: rule });
          console.log(`${C.green}[+]${C.reset} CARL rule: ${name}#${nextId} ${String(rule.text ?? rule).slice(0, 60)}…`);
          changes++;
        }
        d.decisions = d.decisions || [];
        const haveDec = new Set(d.decisions.map(x => x.id));
        for (const dec of (domain.decisions || [])) {
          if (dec.id && !haveDec.has(dec.id)) {
            d.decisions.push(dec);
            console.log(`${C.green}[+]${C.reset} CARL decision: ${name}/${dec.id}`);
            changes++;
          }
        }
      }

      dst.last_modified = new Date().toISOString();
      backupFile(dstCarl);
      if (!DRY) writeFileSync(dstCarl, JSON.stringify(dst, null, 2));
    } catch (e) {
      console.error(`CARL merge failed: ${e.message}`);
    }
  }

  // 2. Update carl-hook.py if version changed
  const srcHook = join(PKG, "carl", "carl-hook.py");
  const dstHook = join(HOME, ".claude", "hooks", "carl-hook.py");
  if (existsSync(srcHook)) {
    const srcVer = readFileSync(srcHook, "utf-8").match(/CARL_HOOK_VERSION=([\d.]+)/)?.[1];
    const dstContent = existsSync(dstHook) ? readFileSync(dstHook, "utf-8") : "";
    const dstVer = dstContent.match(/CARL_HOOK_VERSION=([\d.]+)/)?.[1];
    if (srcVer && srcVer !== dstVer) {
      backupFile(dstHook);
      if (!DRY) writeFileSync(dstHook, readFileSync(srcHook));
      console.log(`${C.green}[+]${C.reset} carl-hook.py: ${dstVer || 'none'} -> ${srcVer}`);
      changes++;
    }
  }

  // 3. Update skills — content-aware: copy new files, overwrite CHANGED files
  // (byte compare), never delete destination-only files (user-local skills survive).
  const skillStats = syncDirContentAware(join(PKG, "skills"), join(vault, ".agents", "skills"));
  if (skillStats) {
    console.log(`${C.green}[+]${C.reset} Skills: +${skillStats.added} added, ~${skillStats.updated} updated, ${skillStats.same} unchanged${DRY ? " (dry-run)" : ""}`);
    changes += skillStats.added + skillStats.updated;
  }

  // 4. Update scripts — same content-aware sync
  const scriptStats = syncDirContentAware(join(PKG, "scripts"), join(vault, ".agents", "scripts"));
  if (scriptStats && (scriptStats.added + scriptStats.updated > 0)) {
    console.log(`${C.green}[+]${C.reset} Scripts: +${scriptStats.added} added, ~${scriptStats.updated} updated${DRY ? " (dry-run)" : ""}`);
    changes += scriptStats.added + scriptStats.updated;
  }

  // 5. Update design hooks — content-aware sync of the hook files, then an
  // additive merge into the user's existing settings.json. Templates step
  // (6, below) is intentionally skipped for everything else because a user's
  // settings.json is theirs to customize; the design hooks are the one
  // exception, because a hook file sitting on disk but never wired into
  // settings.json is a silent no-op, not a benign skip.
  const hookStats = syncDirContentAware(join(PKG, "hooks"), join(HOME, ".claude", "hooks"));
  if (hookStats && (hookStats.added + hookStats.updated > 0)) {
    console.log(`${C.green}[+]${C.reset} Design hooks: +${hookStats.added} added, ~${hookStats.updated} updated${DRY ? " (dry-run)" : ""}`);
    changes += hookStats.added + hookStats.updated;
  }
  const settingsPath = join(HOME, ".claude", "settings.json");
  if (existsSync(settingsPath)) {
    const wired = mergeDesignHooksIntoSettings(settingsPath);
    if (wired.changed > 0) {
      console.log(`${C.green}[+]${C.reset} settings.json: wired ${wired.changed} design hook registration(s)${DRY ? " (dry-run)" : ""}`);
      changes += wired.changed;
    } else if (wired.error) {
      console.log(`${C.yellow}[!]${C.reset} settings.json: could not parse — design hooks not wired, fix manually or re-run --dry-run for detail`);
    }
  } else {
    console.log(`${C.yellow}[!]${C.reset} ~/.claude/settings.json not found — design hooks copied but not wired. Run install.mjs, or add them manually (see docs/design-workflow.md).`);
  }

  // 6. Update templates (only if user hasn't customized)
  // Skip — templates are reference, user has their own configs

  if (changes === 0) {
    console.log(`${C.cyan}[ok]${C.reset} Already up to date.`);
  } else {
    console.log(`\n${C.green}Upgrade complete — ${changes} components updated to v${newVer}${C.reset}`);
    console.log("Review backups (*.bak-*) and remove when satisfied.");
  }
}

main().catch(e => { console.error(e); process.exit(1); });
