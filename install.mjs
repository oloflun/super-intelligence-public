#!/usr/bin/env node
/**
 * Super-Intelligence Agent Stack — One-Shot Installer v1.0
 *
 * Complete multi-agent AI infrastructure installer.
 * Supports interactive and non-interactive modes.
 *
 * Usage:
 *   node install.mjs                           # Interactive mode
 *   node install.mjs --preset claude-windows   # Preset
 *   node install.mjs --agent claude --vault ~/vault --no-hermes --no-chorus
 *
 * Presets: claude-windows, codex-windows, hermes-wsl, claude-mac, claude-linux, minimal, full
 */

import { execSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, symlinkSync, copyFileSync, readdirSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { homedir, platform, tmpdir, EOL } from "node:os";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";

const __dirname = dirname(fileURLToPath(import.meta.url));
const IS_WINDOWS = platform() === "win32";
const IS_MAC = platform() === "darwin";
const IS_LINUX = platform() === "linux";
const HOME = homedir();
const PKG = __dirname;

// ─── CLI ────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const FLAGS = {
  agent: args.includes("--agent") ? args[args.indexOf("--agent") + 1] : "",
  vault: args.includes("--vault") ? args[args.indexOf("--vault") + 1] : "",
  preset: args.includes("--preset") ? args[args.indexOf("--preset") + 1] : "",
  user: args.includes("--user") ? args[args.indexOf("--user") + 1] : "",
  email: args.includes("--email") ? args[args.indexOf("--email") + 1] : "",
  dryRun: args.includes("--dry-run"),
  force: args.includes("--force"),
  yes: args.includes("--yes"),
  // Components (default: all on)
  withHermes: !args.includes("--no-hermes"),
  withChorus: !args.includes("--no-chorus"),
  withSyncthing: !args.includes("--no-syncthing"),
  withAutoExport: !args.includes("--no-auto-export"),
  withKarpathy: !args.includes("--no-karpathy"),
  withQMD: !args.includes("--no-qmd"),
  withBackup: !args.includes("--no-backup"),
  withClaudeep: !args.includes("--no-claudeep"),
  withClipboardVision: !args.includes("--no-clipboard-vision"),
  withDesignHooks: !args.includes("--no-design-hooks"),
  wikiNew: args.includes("--new-vault"),
  wikiExisting: args.includes("--existing-vault"),
  owner: args.includes("--owner"),
  autoUpdate: !args.includes("--no-auto-update"), // default: on
};

const VALID_AGENTS = ["claude", "codex", "gemini", "hermes"];
const VERSION = (() => { try { return readFileSync(join(PKG, "VERSION"), "utf-8").trim(); } catch { return "0.1.0"; } })();

// ─── LOGGING ────────────────────────────────────────────────────────────────
const C = { g: "\x1b[32m", y: "\x1b[33m", r: "\x1b[31m", c: "\x1b[36m", b: "\x1b[1m", x: "\x1b[0m" };
const L = {
  info: m => console.log(`${C.c}[si]${C.x} ${m}`),
  ok: m => console.log(`${C.g}  ok ${C.x} ${m}`),
  warn: m => console.log(`${C.y}  !! ${C.x} ${m}`),
  err: m => console.log(`${C.r}  XX ${C.x} ${m}`),
  hdr: m => console.log(`\n${C.b}${C.c}═══ ${m} ═══${C.x}`),
};

// ─── HELPERS ────────────────────────────────────────────────────────────────
function sh(cmd, opts = {}) {
  if (FLAGS.dryRun) { L.info(`DRY: ${cmd}`); return ""; }
  try { return execSync(cmd, { encoding: "utf-8", stdio: opts.quiet ? "pipe" : "inherit", ...opts }); }
  catch (e) { if (!opts.ok) throw e; L.warn(`cmd failed: ${cmd.split(" ")[0]}`); return ""; }
}

function ensureDir(d) { if (!existsSync(d)) { if (!FLAGS.dryRun) mkdirSync(d, { recursive: true }); L.ok(`dir ${d}`); } }

function wf(p, content) {
  if (existsSync(p) && !FLAGS.force) { L.warn(`skip (exists, --force to overwrite): ${basename(p)}`); return false; }
  if (!FLAGS.dryRun) { ensureDir(dirname(p)); writeFileSync(p, content, "utf-8"); }
  L.ok(`file ${basename(p)}`);
  return true;
}

function copyDir(src, dst) {
  if (!existsSync(src)) { L.warn(`missing ${src}`); return; }
  ensureDir(dst);
  if (FLAGS.dryRun) return;
  if (IS_WINDOWS) sh(`robocopy "${src}" "${dst}" /E /NFL /NDL /NP /R:0 /W:0`, { ok: true, quiet: true });
  else sh(`cp -r "${src}/." "${dst}/"`, { ok: true, quiet: true });
  L.ok(`copy ${basename(src)} -> ${dst}`);
}

// Which files are worth opening and substituting after a bulk copy. Binaries and
// lockfiles are skipped: they never carry a placeholder and rewriting them would
// only risk corrupting them.
const TEMPLATABLE = new Set([
  ".md", ".py", ".json", ".txt", ".yml", ".yaml", ".toml", ".sh",
  ".cmd", ".ps1", ".mjs", ".js", ".ts", ".jsonl", ".env", ".cfg", ".ini",
]);
const TEMPLATE_SKIP_DIRS = new Set([".git", "node_modules", "__pycache__", ".venv"]);

// A placeholder is only a placeholder if something substitutes it. copyDir does a
// raw filesystem copy, so everything it moved -- skills/, scripts/, hooks/ -- used
// to land in the installed tree with `{{VAULT_PATH}}` still spelled out, or worse,
// with the author's own absolute paths baked in. Both fail the same way: the file
// looks right and silently does not work on anyone else's machine.
//
// This walks what was just copied and runs the same rpl() the templated files get,
// so "copied" and "configured" stop being two different things.
function templateTree(root, cfg) {
  if (!existsSync(root) || FLAGS.dryRun) return 0;
  let touched = 0;
  const walk = (dir) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      const p = join(dir, e.name);
      if (e.isDirectory()) {
        if (!TEMPLATE_SKIP_DIRS.has(e.name)) walk(p);
        continue;
      }
      const dot = e.name.lastIndexOf(".");
      const ext = dot < 0 ? "" : e.name.slice(dot).toLowerCase();
      // Extensionless files (e.g. the `qmd` wrapper script) are text here too.
      if (ext && !TEMPLATABLE.has(ext)) continue;
      let raw;
      try { raw = readFileSync(p, "utf-8"); } catch { continue; }
      if (!raw.includes("{{")) continue;
      const out = rpl(raw, cfg);
      if (out !== raw) { writeFileSync(p, out, "utf-8"); touched++; }
    }
  };
  walk(root);
  return touched;
}

// Copy, then configure. Use this wherever a tree of text files is deployed.
function copyDirTemplated(src, dst, cfg) {
  copyDir(src, dst);
  const n = templateTree(dst, cfg);
  if (n) L.ok(`configured ${n} file(s) in ${basename(dst)}`);
}

function createLink(target, linkPath) {
  if (existsSync(linkPath)) {
    if (FLAGS.force) {
      if (!FLAGS.dryRun) { if (IS_WINDOWS) sh(`cmd /c rmdir "${linkPath}"`, { ok: true, quiet: true }); else sh(`rm -rf "${linkPath}"`, { ok: true, quiet: true }); }
    } else { L.warn(`link exists: ${linkPath} (use --force)`); return; }
  }
  if (FLAGS.dryRun) { L.info(`DRY: link ${linkPath} -> ${target}`); return; }
  if (IS_WINDOWS) {
    const r = sh(`cmd /c mklink /J "${linkPath}" "${target}"`, { ok: true, quiet: true });
    if (r.includes("not have sufficient") || r.includes("denied")) {
      L.warn(`Junction failed (permissions?), trying directory copy instead`);
      copyDir(target, linkPath);
    }
  } else {
    try { symlinkSync(target, linkPath, "dir"); } catch { L.warn(`Symlink failed, copying instead`); if (!FLAGS.dryRun) copyDir(target, linkPath); }
  }
  L.ok(`link ${basename(linkPath)} -> ${target}`);
}

// ─── REPLACE ────────────────────────────────────────────────────────────────
function rpl(content, cfg) {
  const fwd = p => p.replace(/\\/g, "/");
  const esc = p => p.replace(/\\/g, "\\\\");
  return content
    .replaceAll("{{VAULT_PATH_ESC}}", esc(cfg.vault))
    .replaceAll("{{VAULT_PATH_FWD}}", fwd(cfg.vault))
    .replaceAll("{{VAULT_PATH}}", cfg.vault)
    .replaceAll("{{USER_HOME_ESC}}", esc(HOME))
    .replaceAll("{{USER_HOME_FWD}}", fwd(HOME))
    .replaceAll("{{USER_HOME_UNC}}", `\\\\?\\${HOME}`)
    .replaceAll("{{USER_HOME}}", HOME)
    .replaceAll("{{USER_EMAIL}}", cfg.email)
    .replaceAll("{{USER_NAME}}", cfg.user)
    .replaceAll("{{WSL_VAULT_PATH}}", "/mnt/" + fwd(cfg.vault).replace(":", "").toLowerCase())
    .replaceAll("{{INSTALL_DATE}}", new Date().toISOString().split("T")[0])
    .replaceAll("{{PYTHON_PATH_ESC}}", IS_WINDOWS ? "python" : "python3")
    .replaceAll("{{PYTHON_PATH}}", IS_WINDOWS ? "python" : "python3")
    .replaceAll("{{HERMES_VAULT}}", "~/vault-local")
    // WSL/Linux-hemkatalogen ar inte samma sak som Windows-hemkatalogen och inte
    // heller samma som git-namnet: Hermes kor under sitt eget konto. Utan ett
    // eget token blev de sokvagarna kvar bokstavligt i dokumentationen.
    .replaceAll("{{WSL_HOME}}", `/home/${(cfg.user || "user").toLowerCase().replace(/[^a-z0-9_-]/g, "_")}`)
    .replaceAll("{{PLATFORM}}", IS_WINDOWS ? "Windows" : IS_MAC ? "macOS" : "Linux");
}

function deployTemplate(src, dst, cfg) {
  if (!existsSync(src)) { L.warn(`no template: ${basename(src)}`); return; }
  const raw = readFileSync(src, "utf-8");
  wf(dst, rpl(raw, cfg));
}

// ─── PROMPTS ────────────────────────────────────────────────────────────────
async function ask(q, def = "") {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  const s = def ? ` [${def}]` : "";
  return new Promise(res => rl.question(`${q}${s}: `, a => { rl.close(); resolve(a.trim() || def); }));
}

async function askYN(q, def = true) {
  const d = def ? "Y/n" : "y/N";
  const a = (await ask(`${q} (${d})`, def ? "y" : "n")).toLowerCase();
  return a === "y" || a === "yes";
}

// ─── PRESETS ────────────────────────────────────────────────────────────────
const PRESETS = {
  "claude-windows": { agent: "claude", hermes: false },
  "codex-windows": { agent: "codex", hermes: false },
  "claude-mac": { agent: "claude", hermes: false },
  "claude-linux": { agent: "claude", hermes: true },
  "hermes-wsl": { agent: "hermes", hermes: true },
  "minimal": { agent: "claude", hermes: false, chorus: false, syncthing: false, autoExport: false, karpathy: false, qmd: true, backup: false },
  "full": { agent: "claude", hermes: true, chorus: true, syncthing: true, autoExport: true, karpathy: true, qmd: true, backup: true, claudeep: true, clipboardVision: true },
};

// ─── GATHER CONFIG ──────────────────────────────────────────────────────────
async function gatherConfig() {
  // Apply preset first
  if (FLAGS.preset && PRESETS[FLAGS.preset]) {
    const p = PRESETS[FLAGS.preset];
    if (!FLAGS.agent) FLAGS.agent = p.agent;
    if (p.hermes !== undefined && !args.includes("--no-hermes") && !args.includes("--with-hermes")) FLAGS.withHermes = p.hermes;
    if (p.chorus !== undefined) FLAGS.withChorus = p.chorus;
    if (p.syncthing !== undefined) FLAGS.withSyncthing = p.syncthing;
    if (p.autoExport !== undefined) FLAGS.withAutoExport = p.autoExport;
    if (p.karpathy !== undefined) FLAGS.withKarpathy = p.karpathy;
    if (p.qmd !== undefined) FLAGS.withQMD = p.qmd;
    if (p.backup !== undefined) FLAGS.withBackup = p.backup;
    if (p.claudeep !== undefined) FLAGS.withClaudeep = p.claudeep;
    if (p.clipboardVision !== undefined) FLAGS.withClipboardVision = p.clipboardVision;
  }

  // Banner
  console.log(`\n${C.c}╔══════════════════════════════════════════════════╗
║${C.x}  Super-Intelligence Agent Stack ${C.b}v${VERSION.padEnd(20)}${C.c}║
║${C.x}  One-shot installer                             ${C.c}║
╚══════════════════════════════════════════════════╝${C.x}\n`);

  console.log(`Platform: ${C.b}${IS_WINDOWS ? "Windows" : IS_MAC ? "macOS" : "Linux"}${C.x}`);
  console.log(`Home:     ${HOME}`);
  console.log(`Package:  ${PKG}\n`);

  if (FLAGS.preset) console.log(`Preset:   ${C.y}${FLAGS.preset}${C.x}\n`);

  // Interactive or CLI
  const interactive = !FLAGS.yes && !FLAGS.agent;

  // Agent
  if (!FLAGS.agent) {
    const opts = IS_WINDOWS ? "claude / codex / gemini / hermes" : "claude / gemini / hermes";
    FLAGS.agent = await ask(`Agent (${opts})`, IS_WINDOWS ? "claude" : "claude");
  }
  if (!VALID_AGENTS.includes(FLAGS.agent)) { console.error(`Invalid agent: ${FLAGS.agent}`); process.exit(1); }
  console.log(`Agent:    ${C.b}${FLAGS.agent}${C.x}`);

  // Vault path
  if (!FLAGS.vault) {
    const defaults = {
      win32: join(HOME, "OneDrive", "Obsidian", "Knowledge Base"),
      darwin: join(HOME, "Documents", "Obsidian", "Knowledge Base"),
      linux: join(HOME, "vault-local"),
    };
    const def = defaults[platform()] || join(HOME, "vault");
    FLAGS.vault = await ask("Obsidian vault path", def);
  }
  console.log(`Vault:    ${C.b}${FLAGS.vault}${C.x}`);

  // Wiki structure
  if (!FLAGS.wikiNew && !FLAGS.wikiExisting && interactive) {
    FLAGS.wikiNew = await askYN("Create new wiki directory structure?", !existsSync(join(FLAGS.vault, "wiki")));
    if (!FLAGS.wikiNew) FLAGS.wikiExisting = true;
  }
  if (FLAGS.wikiNew) console.log(`Wiki:     ${C.b}new structure${C.x}`);
  else if (FLAGS.wikiExisting) console.log(`Wiki:     ${C.b}existing structure${C.x}`);
  else console.log(`Wiki:     ${C.b}auto-detect${C.x}`);

  // Components
  if (interactive) {
    console.log(`\n${C.b}Components (toggle with y/n):${C.x}`);
    FLAGS.withHermes = await askYN("  Hermes/WSL agent?", FLAGS.withHermes && (IS_WINDOWS || IS_LINUX));
    FLAGS.withChorus = await askYN("  Agent Chorus (cross-agent)?", FLAGS.withChorus);
    FLAGS.withSyncthing = await askYN("  Syncthing bridge?", FLAGS.withSyncthing);
    FLAGS.withAutoExport = await askYN("  Auto-export pipeline?", FLAGS.withAutoExport);
    FLAGS.withKarpathy = await askYN("  Karpathy wiki system?", FLAGS.withKarpathy);
    FLAGS.withQMD = await askYN("  QMD search?", FLAGS.withQMD);
    FLAGS.withBackup = await askYN("  Vault backup?", FLAGS.withBackup);
    FLAGS.withClaudeep = await askYN("  Claudeep (DeepSeek backend)?", FLAGS.withClaudeep);
    FLAGS.withClipboardVision = await askYN("  Clipboard Vision MCP?", FLAGS.withClipboardVision);
    FLAGS.owner = await askYN("  Owner mode (sync changes to repo)?", false);
    FLAGS.autoUpdate = await askYN("  Enable daily auto-update?", true);
  }

  // User info
  if (!FLAGS.user) FLAGS.user = process.env.SI_USER || await ask("Git username", "");
  if (!FLAGS.email) FLAGS.email = process.env.SI_EMAIL || await ask("Git email", "");

  // Confirm
  console.log(`\n${C.b}Installation plan:${C.x}`);
  console.log(`  Agent:     ${FLAGS.agent}`);
  console.log(`  Vault:     ${FLAGS.vault}`);
  console.log(`  Hermes:    ${FLAGS.withHermes ? "yes" : "no"}`);
  console.log(`  Chorus:    ${FLAGS.withChorus ? "yes" : "no"}`);
  console.log(`  Syncthing: ${FLAGS.withSyncthing ? "yes" : "no"}`);
  console.log(`  Export:    ${FLAGS.withAutoExport ? "yes" : "no"}`);
  console.log(`  Karpathy:  ${FLAGS.withKarpathy ? "yes" : "no"}`);
  console.log(`  QMD:       ${FLAGS.withQMD ? "yes" : "no"}`);
  console.log(`  Backup:    ${FLAGS.withBackup ? "yes" : "no"}`);
  console.log(`  Claudeep:  ${FLAGS.withClaudeep ? "yes" : "no"}`);
  console.log(`  ClipViz:   ${FLAGS.withClipboardVision ? "yes" : "no"}`);
  console.log(`  DesignHooks:${FLAGS.withDesignHooks ? "yes (advisory gate)" : "no"}`);
  console.log(`  Owner:     ${FLAGS.owner ? "yes" : "no"}`);
  console.log(`  AutoUpdate:${FLAGS.autoUpdate ? "yes" : "no"}\n`);

  if (!FLAGS.yes) {
    const ok = await ask("Proceed with installation? (y/N)", "n");
    if (ok.toLowerCase() !== "y") { console.log("Aborted."); process.exit(0); }
  }

  return {
    agent: FLAGS.agent,
    vault: FLAGS.vault,
    email: FLAGS.email,
    user: FLAGS.user,
    version: VERSION,
    interactive,
  };
}

// ─── INSTALL STEPS ──────────────────────────────────────────────────────────

async function step_dirs(cfg) {
  L.hdr("Step 1: Directories");
  const dirs = [
    join(cfg.vault, "memory", "archive"),
    join(cfg.vault, "scripts"),
    join(HOME, ".claude", "hooks"),
    join(HOME, "session-logs"),
  ];
  if (cfg.wikiNew || !existsSync(join(cfg.vault, "wiki"))) {
    dirs.push(join(cfg.vault, "wiki", "concepts"));
    dirs.push(join(cfg.vault, "wiki", "entities"));
    dirs.push(join(cfg.vault, "wiki", "projects"));
    dirs.push(join(cfg.vault, "wiki", "sources"));
    dirs.push(join(cfg.vault, "raw", "conversations"));
    L.info("Creating wiki directory structure...");
  }
  if (FLAGS.withChorus) {
    dirs.push(join(cfg.vault, ".agent-chorus", "messages"));
    dirs.push(join(cfg.vault, ".agent-chorus", "providers"));
  }
  dirs.forEach(ensureDir);
}

async function step_deps(cfg) {
  L.hdr("Step 2: Dependencies");
  L.info("Checking Node.js...");
  try { sh("node --version", { quiet: true }); L.ok("Node.js available"); }
  catch { L.err("Node.js 18+ required"); process.exit(1); }

  L.info("Checking Python...");
  const py = IS_WINDOWS ? "python" : "python3";
  try { sh(`${py} --version`, { quiet: true }); L.ok(`${py} available`); }
  catch { L.warn(`Python not found as '${py}' — CARL hook may need adjustment`); }

  if (FLAGS.withQMD) {
    L.info("Installing QMD...");
    sh("npm install -g @tobilu/qmd", { ok: true });
    L.ok("QMD installed");
  }
}

async function step_carl(cfg) {
  L.hdr("Step 3: CARL (Context Injection)");
  deployTemplate(join(PKG, "carl", "carl.json"), join(cfg.vault, ".carl", "carl.json"), cfg);
  deployTemplate(join(PKG, "carl", "carl-hook.py"), join(HOME, ".claude", "hooks", "carl-hook.py"), cfg);

  // Junction ~/.carl -> vault/.carl
  createLink(join(cfg.vault, ".carl"), join(HOME, ".carl"));
  // Junction ~/.agents -> vault/.agents
  createLink(join(cfg.vault, ".agents"), join(HOME, ".agents"));
}

// The 8 design-hook registrations. Each is a standalone block (own matcher,
// own command) appended to its event's array — never merged into an existing
// block, so a re-run or an upgrade never disturbs a hook the user already has
// (carl-hook.py, deepclaude-pretool.py, third-party MCP hooks, etc.).
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

// Additively wires the design hooks into an EXISTING settings.json. Fresh
// installs get them via step_configs' templated write instead; this is what
// makes them land for a user who already has a settings.json (a repeat run,
// or a prior version of this installer) — deployTemplate silently skips an
// existing file, so without this the hook *files* would be on disk but never
// wired, which is a worse failure mode than not installing them at all.
function mergeDesignHooksIntoSettings(settingsPath) {
  if (!existsSync(settingsPath)) return { changed: 0, present: false };
  let settings;
  try { settings = JSON.parse(readFileSync(settingsPath, "utf-8")); }
  catch (e) { L.warn(`settings.json unreadable, skipping hook merge: ${e.message}`); return { changed: 0, present: true, error: true }; }

  const homeF = HOME.replace(/\\/g, "/");
  const hooks = settings.hooks || (settings.hooks = {});
  let changed = 0;

  for (const reg of designHookRegistrations(homeF)) {
    const arr = hooks[reg.event] || (hooks[reg.event] = []);
    const existing = arr.find(block => (block.hooks || []).some(h => (h.command || "").includes(reg.script)));
    if (existing) {
      // Already wired — but a matcher can WIDEN between versions, and the
      // presence check above would happily leave the old one in place forever.
      // 0.4.5 widened design-verify-gate to cover the Chrome extension; a user
      // upgrading from 0.4.4 would otherwise keep firing on the pane only.
      // Only ever touch a block we recognise as ours.
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

  if (changed > 0 && !FLAGS.dryRun) {
    const bak = settingsPath + ".bak-" + Date.now();
    copyFileSync(settingsPath, bak);
    writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n", "utf-8");
    L.ok(`settings.json: wired ${changed} design hook(s) (backup: ${basename(bak)})`);
  } else if (changed > 0) {
    L.info(`DRY: would wire ${changed} design hook(s) into settings.json`);
  }
  return { changed, present: true };
}

async function step_design_hooks(cfg) {
  if (!FLAGS.withDesignHooks) { L.hdr("Step 3c: Design Hooks — SKIPPED (--no-design-hooks)"); return; }
  L.hdr("Step 3c: Design Hooks (Brand-Derivation Gate)");
  copyDirTemplated(join(PKG, "hooks"), join(HOME, ".claude", "hooks"), cfg);

  // If settings.json already exists (repeat run, prior install), wire the
  // hooks in additively. A brand-new settings.json is handled by step_configs
  // below, whose template already carries these entries.
  mergeDesignHooksIntoSettings(join(HOME, ".claude", "settings.json"));

  L.info("Advisory by default — the contract gate warns but never blocks a write.");
  L.info("Promote to hard denial per-shell with: DESIGN_GATE_BLOCKING=1");
  L.info("Disable entirely with: DESIGN_HOOKS_DISABLED=1");
  L.info("See docs/design-workflow.md for the full gate + hook chain.");
}

async function step_upstream_gate(cfg) {
  if (!FLAGS.owner) { L.hdr("Step 3b: Upstream Sync Gate — SKIPPED (--owner not set)"); return; }
  L.hdr("Step 3b: Upstream Sync Gate");
  const upstreamPath = join(cfg.vault, ".carl", "upstream.json");
  wf(upstreamPath, JSON.stringify({
    created: new Date().toISOString(),
    version: VERSION,
    agent: cfg.agent,
    note: "Presence of this file enables conclude Step 3c — upstream sync to super-intelligence repo",
  }, null, 2));
  L.ok("Owner mode: .carl/upstream.json created — conclude will sync changes to repo");
}

async function step_skills(cfg) {
  L.hdr("Step 4: Skills (211 modules)");
  copyDirTemplated(join(PKG, "skills"), join(cfg.vault, ".agents", "skills"), cfg);
  // Also copy .skill-lock.json
  deployTemplate(join(PKG, "templates", ".skill-lock.json"), join(cfg.vault, ".agents", ".skill-lock.json"), cfg);
}

async function step_scripts(cfg) {
  L.hdr("Step 5: Scripts");
  copyDirTemplated(join(PKG, "scripts"), join(cfg.vault, ".agents", "scripts"), cfg);
  if (!IS_WINDOWS) {
    sh(`chmod +x "${join(cfg.vault, '.agents', 'scripts')}"/*.sh "${join(cfg.vault, '.agents', 'scripts')}"/*.py "${join(cfg.vault, '.agents', 'scripts')}"/qmd`, { ok: true, quiet: true });
  }
}

async function step_configs(cfg) {
  L.hdr("Step 6: Agent Configurations");
  deployTemplate(join(PKG, "templates", "CLAUDE.md"), join(HOME, "CLAUDE.md"), cfg);
  deployTemplate(join(PKG, "templates", "AGENTS.md"), join(HOME, "AGENTS.md"), cfg);
  deployTemplate(join(PKG, "templates", "GEMINI.md"), join(HOME, "GEMINI.md"), cfg);
  deployTemplate(join(PKG, "templates", ".claude-settings.json"), join(HOME, ".claude", "settings.json"), cfg);
  deployTemplate(join(PKG, "templates", ".mcp.json"), join(HOME, ".mcp.json"), cfg);

  // .claude/CLAUDE.md (internal reference)
  wf(join(HOME, ".claude", "CLAUDE.md"),
    "# Claude Code Configuration\n\n<!-- CARL-MANAGED -->\n## CARL Integration\n\n" +
    "Follow all rules in <carl-rules> blocks from system-reminders.\n" +
    "These are dynamically injected based on context and MUST be obeyed.\n<!-- END CARL-MANAGED -->\n");

  // Vault .gitignore
  deployTemplate(join(PKG, "templates", "vault-.gitignore"), join(cfg.vault, ".gitignore"), cfg);

  // Obsidian config (if new vault)
  if (cfg.wikiNew || !existsSync(join(cfg.vault, ".obsidian"))) {
    ensureDir(join(cfg.vault, ".obsidian"));
    deployTemplate(join(PKG, "templates", ".obsidian-app.json"), join(cfg.vault, ".obsidian", "app.json"), cfg);
    deployTemplate(join(PKG, "templates", ".obsidian-graph.json"), join(cfg.vault, ".obsidian", "graph.json"), cfg);
    L.ok("Obsidian config initialized");
  }
}

async function step_memory(cfg) {
  L.hdr("Step 7: Memory System");
  ensureDir(join(cfg.vault, "memory", "archive"));

  // Initialize memory using the memory-init script
  const py = IS_WINDOWS ? "python" : "python3";
  const initScript = join(PKG, "scripts", "memory-init.py");
  if (existsSync(initScript)) {
    const ff = FLAGS.force ? " --force" : "";
    sh(`${py} "${initScript}" --vault "${cfg.vault}"${ff}`, { ok: true });
  } else {
    // Fallback: create files directly
    const t = new Date().toISOString().split("T")[0];
    wf(join(cfg.vault, "memory", "MEMORY.md"),
      `# Agent Memory (Hot)\n_Cap: 2 200 chars. Loaded every standup. Write only at /conclude._\n\n` +
      `## Active Constraints\n_(none yet)_\n\n` +
      `## Environment Facts\n- [${t}] System initialized via super-intelligence v${VERSION}\n\n## Open Threads\n_(none)_\n`);
    wf(join(cfg.vault, "memory", "USER.md"),
      `# User Profile (Hot)\n_Cap: 1 375 chars._\n\n## Preferences\n_(none yet)_\n\n## Active Projects\n_(none yet)_\n`);
    wf(join(cfg.vault, "memory", "MEMORY-FULL.md"),
      `# Memory (Warm — Episodic)\n_Unbounded._\n\n## System Init — ${t}\n- Stack installed v${VERSION}\n`);
    wf(join(cfg.vault, "memory", "USER-FULL.md"),
      `# User Profile (Warm — Full History)\n_Unbounded._\n`);

    // sessions.db
    const db = join(cfg.vault, "memory", "sessions.db");
    if (!existsSync(db) || FLAGS.force) {
      const sql = readFileSync(join(PKG, "templates", "memory", "schema.sql"), "utf-8");
      const tmp = join(tmpdir(), "si-sessions.sql");
      writeFileSync(tmp, sql);
      sh(`sqlite3 "${db}" < "${tmp}"`, { ok: true, quiet: true });
      L.ok("sessions.db created");
    }
  }
}

async function step_status(cfg) {
  L.hdr("Step 8: STATUS.md");
  const status = `# Global Agent Status\n_Updated: ${new Date().toISOString().split("T")[0]} by installer_\n\n## Claude\n(no recent sessions)\n\n## Codex\n(no recent sessions)\n\n## Gemini\n(no recent sessions)\n\n## Hermes\n(no recent sessions)\n`;
  wf(join(cfg.vault, "STATUS.md"), status);

  // Hardlink ~/STATUS.md -> vault/STATUS.md
  const hs = join(HOME, "STATUS.md");
  if (!existsSync(hs) || FLAGS.force) {
    if (IS_WINDOWS) {
      if (existsSync(hs) && !FLAGS.dryRun) sh(`cmd /c del "${hs}"`, { ok: true, quiet: true });
      if (!FLAGS.dryRun) sh(`cmd /c mklink /H "${hs}" "${join(cfg.vault, 'STATUS.md')}"`, { ok: true });
    } else {
      if (existsSync(hs) && !FLAGS.dryRun) sh(`rm -f "${hs}"`, { ok: true, quiet: true });
      if (!FLAGS.dryRun) sh(`ln "${join(cfg.vault, 'STATUS.md')}" "${hs}"`, { ok: true });
    }
    L.ok("STATUS.md linked");
  }
}

// Pinned rather than "latest" on purpose: the vault-side config this step writes
// (relay-config.json, the provider snippets, the per-agent inboxes) is a contract
// with a specific chorus version. Floating the dependency means a future release
// can change that contract silently, and the failure would show up as agents
// quietly not receiving handoffs -- the hardest kind of breakage to notice.
// Bump this deliberately, together with the config it talks to.
const CHORUS_VERSION = "0.16.0";

async function step_chorus(cfg) {
  if (!FLAGS.withChorus) { L.hdr("Step 9: Agent Chorus — SKIPPED"); return; }
  L.hdr("Step 9: Agent Chorus");

  // Install the CLI itself. Without this the step wrote a complete configuration
  // for a program that was never on the machine -- everything looked installed
  // and no message could actually be sent.
  let have = "";
  try { have = sh("chorus --version", { quiet: true, ok: true }).trim(); } catch { have = ""; }
  if (have === CHORUS_VERSION) {
    L.ok(`agent-chorus ${have} already installed`);
  } else {
    L.info(`Installing agent-chorus@${CHORUS_VERSION}${have ? ` (replacing ${have})` : ""}...`);
    sh(`npm install -g agent-chorus@${CHORUS_VERSION}`, { ok: true });
    let now = "";
    try { now = sh("chorus --version", { quiet: true, ok: true }).trim(); } catch { now = ""; }
    if (now) L.ok(`agent-chorus ${now} installed`);
    else L.warn("agent-chorus did not install — cross-agent handoffs will be unavailable until 'npm install -g agent-chorus' succeeds");
  }

  // De tre hook-scripten maste ligga dar settings.json pekar, annars ar
  // registreringen en pekare till ingenting -- och en hook som inte finns
  // failar tyst, vilket ar precis hur handoffs slutar komma fram utan att
  // nagon marker det.
  copyDirTemplated(join(PKG, "chorus", "hooks"), join(HOME, ".claude", "hooks", "chorus"), cfg);

  deployTemplate(join(PKG, "chorus", "relay-config.json"), join(cfg.vault, ".agent-chorus", "relay-config.json"), cfg);
  copyDirTemplated(join(PKG, "chorus", "providers"), join(cfg.vault, ".agent-chorus", "providers"), cfg);
  deployTemplate(join(PKG, "chorus", "CHECKPOINT.md"), join(cfg.vault, ".agent-chorus", "CHECKPOINT.md"),
    { ...cfg, agent: cfg.agent, timestamp: new Date().toISOString(), branch: "main", uncommitted_count: "0", task_description: "System installation", files: "N/A" });

  // Init empty inboxes
  for (const a of ["claude", "codex", "gemini", "hermes"]) {
    const ib = join(cfg.vault, ".agent-chorus", "messages", `${a}.jsonl`);
    if (!existsSync(ib) && !FLAGS.dryRun) writeFileSync(ib, "", "utf-8");
  }
  L.ok("Chorus configured");
}

async function step_qmd(cfg) {
  if (!FLAGS.withQMD) { L.hdr("Step 10: QMD Search — SKIPPED"); return; }
  L.hdr("Step 10: QMD Search");
  deployTemplate(join(PKG, "templates", ".qmd.yaml"), join(cfg.vault, ".qmd.yaml"), cfg);
  try { sh("qmd update", { quiet: true, cwd: cfg.vault }); L.ok("qmd update"); }
  catch { L.warn("qmd update failed — run manually after populating vault"); }
}

async function step_backup(cfg) {
  if (!FLAGS.withBackup) { L.hdr("Step 11: Backup — SKIPPED"); return; }
  L.hdr("Step 11: Vault Backup");
  ensureDir(join(cfg.vault, "scripts"));
  deployTemplate(join(PKG, "scripts", "backup-vault.ps1"), join(cfg.vault, "scripts", "backup-vault.ps1"), cfg);
  L.ok("Backup script deployed (runs at /conclude)");
}

async function step_syncthing(cfg) {
  if (!FLAGS.withSyncthing) { L.hdr("Step 12: Syncthing — SKIPPED"); return; }
  L.hdr("Step 12: Syncthing Bridge");
  deployTemplate(join(PKG, "templates", ".stignore"), join(cfg.vault, ".stignore"), cfg);
  L.ok(".stignore deployed");
  L.info("Configure Syncthing folder in the web UI (http://localhost:8384)");
  L.info("  Windows vault <-> WSL ~/vault-local with folder ID: knowledge-base");
}

async function step_hermes(cfg) {
  if (!FLAGS.withHermes) { L.hdr("Step 13: Hermes — SKIPPED"); return; }
  L.hdr("Step 13: Hermes Agent");
  L.info("Hermes runs in WSL2 (Windows) or natively (Linux).");

  if (IS_WINDOWS) {
    L.info("After installation, run in WSL:");
    L.info(`  node "${PKG.replace(/\\/g, '/')}/install.mjs" --agent hermes --vault ~/vault-local --yes --no-hermes`);
  }

  if (IS_LINUX && cfg.agent === "hermes") {
    // Hermes-specific: vault is ~/vault-local
    const hermesVault = join(HOME, "vault-local");
    ensureDir(hermesVault);
    L.ok(`Hermes vault: ${hermesVault}`);
    L.info("Ensure Syncthing syncs vault <-> ~/vault-local");
  }

  // Deploy Hermes docs
  copyDir(join(PKG, "hermes"), join(PKG, "hermes")); // already in package
  L.ok("Hermes guide available in docs/");
}

async function step_autoexport(cfg) {
  if (!FLAGS.withAutoExport) { L.hdr("Step 14: Auto-Export — SKIPPED"); return; }
  L.hdr("Step 14: Auto-Export Pipeline");
  L.info("Files available in wiki-ingest/:");
  L.info("  auto-wiki-ingest-v2.user.js — Tampermonkey script");
  L.info("  watch-and-route-v2.sh — File watcher");
  L.info("  See wiki-ingest/README.md for setup instructions");
}

async function step_karpathy(cfg) {
  if (!FLAGS.withKarpathy) { L.hdr("Step 15: Karpathy Wiki — SKIPPED"); return; }
  L.hdr("Step 15: Karpathy Wiki");
  L.info("See karpathy/wiki-setup.md for the full methodology guide");
  L.info("Key concepts: treat conversations as wiki pages, link organically, /ingest regularly");
}

async function step_claudeep(cfg) {
  if (!FLAGS.withClaudeep) { L.hdr("Step 16: Claudeep — SKIPPED"); return; }
  L.hdr("Step 16: Claudeep (DeepSeek Backend)");
  L.info("Claudeep proxies Claude Code Anthropic API calls to DeepSeek.");
  L.info("Install: npm install -g claudeep && npx claudeep setup");
  L.info("This creates ~/.deepseek-claude/env with your API key and model mappings.");
  L.info("Get a DeepSeek API key: https://platform.deepseek.com/api_keys");
  L.info("See docs/DEEPSEEK.md for full configuration and model mapping.");
  L.info("Pair with clipboard-vision-mcp for vision support (text-only models).");
}

async function step_clipboardVision(cfg) {
  if (!FLAGS.withClipboardVision) { L.hdr("Step 17: Clipboard Vision — SKIPPED"); return; }
  L.hdr("Step 17: Clipboard Vision MCP");
  L.info("Let text-only models see images directly from your clipboard.");
  L.info("git clone https://github.com/Capetlevrai/clipboard-vision-mcp.git");
  L.info("cd clipboard-vision-mcp && python -m venv .venv && pip install -e .");
  L.info("Get free Groq API key: https://console.groq.com/keys");
  L.info("See docs/CLIPBOARD-VISION.md for MCP client configuration.");
  L.info("Tools: analyze_clipboard, extract_text_from_clipboard, diagnose_error_from_clipboard, etc.");
}

async function step_auto_update(cfg) {
  L.hdr("Step 18: Auto-Update System");

  const SI_CONFIG_DIR = join(HOME, ".super-intelligence");
  ensureDir(SI_CONFIG_DIR);
  const updateLog = join(SI_CONFIG_DIR, "update.log");

  // Write config
  const config = {
    version: 1,
    repo_path: PKG,
    vault_path: cfg.vault,
    owner_mode: FLAGS.owner,
    auto_update: FLAGS.autoUpdate,
    last_check: null,
    update_log: updateLog,
  };
  if (!FLAGS.dryRun) {
    writeFileSync(join(SI_CONFIG_DIR, "config.json"), JSON.stringify(config, null, 2), "utf-8");
  }
  L.ok(`Config: ~/.super-intelligence/config.json`);

  if (!FLAGS.autoUpdate) {
    L.info("Auto-update disabled by --no-auto-update flag");
    L.info("Enable later: edit ~/.super-intelligence/config.json → auto_update: true");
    return;
  }

  // Schedule the daily check
  if (IS_WINDOWS) {
    const scheduleScript = join(PKG, "scripts", "schedule-auto-update.ps1");
    const updateScript = join(PKG, "scripts", "auto-update.ps1");
    if (existsSync(scheduleScript)) {
      sh(`powershell -NoProfile -NonInteractive -File "${scheduleScript}" -UpdateScriptPath "${updateScript}"`, { ok: true });
      L.ok("Windows Task Scheduler installed (daily 09:00 + rand 1h)");
    } else {
      L.warn("schedule-auto-update.ps1 not found — cannot register Task Scheduler");
    }
  } else {
    const scheduleScript = join(PKG, "scripts", "schedule-auto-update.sh");
    const updateScript = join(PKG, "scripts", "auto-update.sh");
    if (existsSync(scheduleScript)) {
      sh(`chmod +x "${updateScript}"`, { ok: true, quiet: true });
      sh(`bash "${scheduleScript}" "${updateScript}"`, { ok: true });
    } else {
      L.warn("schedule-auto-update.sh not found — cannot set up scheduler");
      L.info("Manual: add auto-update.sh to your system scheduler (cron, launchd, etc.)");
    }
  }

  L.ok("Daily auto-update + health check configured");
  L.info(`Logs: ${updateLog}`);
  L.info(`Config: ${join(SI_CONFIG_DIR, "config.json")}`);
  L.info("To disable: edit config → auto_update: false");
  L.info("To remove: node scripts/remove-auto-update.js (and Windows Task Scheduler)");
}

// ─── SUMMARY ────────────────────────────────────────────────────────────────
function summary(cfg) {
  const comps = [];
  if (FLAGS.withHermes) comps.push("Hermes");
  if (FLAGS.withChorus) comps.push("Chorus");
  if (FLAGS.withSyncthing) comps.push("Syncthing");
  if (FLAGS.withQMD) comps.push("QMD");
  if (FLAGS.withBackup) comps.push("Backup");
  if (FLAGS.withAutoExport) comps.push("Auto-Export");
  if (FLAGS.withKarpathy) comps.push("Karpathy");
  if (FLAGS.withClaudeep) comps.push("Claudeep");
  if (FLAGS.withClipboardVision) comps.push("ClipboardVision");
  if (FLAGS.withDesignHooks) comps.push("DesignHooks");
  if (FLAGS.owner) comps.push("Owner");
  if (FLAGS.autoUpdate) comps.push("AutoUpdate");

  console.log(`\n${C.g}╔══════════════════════════════════════════════════╗
║  Installation Complete!                          ║
║                                                  ║
║  Agent:     ${cfg.agent.padEnd(36)}║
║  Vault:     ${cfg.vault.padEnd(36)}║
║  Platform:  ${(IS_WINDOWS ? "Windows" : IS_MAC ? "macOS" : "Linux").padEnd(36)}║
║  Components:${comps.join(", ").padEnd(36)}║
║                                                  ║
║  Next:                                           ║
║  1. Start your agent session                     ║
║  2. Run /standup to load context                 ║
║  3. CARL auto-injects on fresh sessions          ║
║  4. Daily auto-update runs at 09:00             ║
║  5. See docs/ for guides                         ║
╚══════════════════════════════════════════════════╝${C.x}\n`);

  console.log(`Super-Intelligence v${VERSION} installed.`);
}

// ─── MAIN ───────────────────────────────────────────────────────────────────
async function main() {
  const cfg = await gatherConfig();

  const steps = [
    () => step_dirs(cfg),
    () => step_deps(cfg),
    () => step_carl(cfg),
    () => step_design_hooks(cfg),
    () => step_upstream_gate(cfg),
    () => step_skills(cfg),
    () => step_scripts(cfg),
    () => step_configs(cfg),
    () => step_memory(cfg),
    () => step_status(cfg),
    () => step_chorus(cfg),
    () => step_qmd(cfg),
    () => step_backup(cfg),
    () => step_syncthing(cfg),
    () => step_hermes(cfg),
    () => step_autoexport(cfg),
    () => step_karpathy(cfg),
    () => step_claudeep(cfg),
    () => step_clipboardVision(cfg),
    () => step_auto_update(cfg),
  ];

  for (const step of steps) {
    try { await step(); }
    catch (e) {
      L.err(`Step failed: ${e.message}`);
      if (!FLAGS.yes) {
        const c = await ask("Continue? (y/N)", "n");
        if (c.toLowerCase() !== "y") { L.err("Aborted."); process.exit(1); }
      }
    }
  }

  summary(cfg);
}

main().catch(e => { console.error(e); process.exit(1); });
