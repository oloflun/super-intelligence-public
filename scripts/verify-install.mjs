#!/usr/bin/env node
/**
 * Verify super-intelligence installation health.
 * Usage: node scripts/verify-install.mjs [--json]
 */

import { existsSync, readFileSync, lstatSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { execFileSync } from "node:child_process";

const HOME = homedir();
const JSON_MODE = process.argv.includes("--json");

const C = JSON_MODE
  ? { green: "", red: "", yellow: "", cyan: "", bold: "", reset: "" }
  : { green: "\x1b[32m", red: "\x1b[31m", yellow: "\x1b[33m", cyan: "\x1b[36m", bold: "\x1b[1m", reset: "\x1b[0m" };

let ok = 0, fail = 0, warnCount = 0;

/** @type {Array<{label:string, passed?:boolean, detail?:string}>} */
const results = [];

function check(label, path, type = "file") {
  let exists = false;
  try {
    if (type === "dir") {
      const st = lstatSync(path);
      exists = st.isDirectory() || st.isSymbolicLink();
    } else {
      exists = existsSync(path);
    }
  } catch { exists = false; }

  if (exists) {
    ok++;
    results.push({ label, passed: true, detail: path });
    if (!JSON_MODE) console.log(`${C.green}[ok]${C.reset} ${label}`);
  } else {
    fail++;
    results.push({ label, passed: false, detail: `missing: ${path}` });
    if (!JSON_MODE) console.log(`${C.red}[XX]${C.reset} ${label} (missing)`);
  }
}

function warn(label) {
  warnCount++;
  results.push({ label, passed: undefined, detail: label });
  if (!JSON_MODE) console.log(`${C.yellow}[WARN]${C.reset} ${label}`);
}

function info(label) {
  results.push({ label, detail: label });
  if (!JSON_MODE) console.log(`${C.cyan}[INFO]${C.reset} ${label}`);
}

// ── Header ──────────────────────────────────────────────────────────────────
if (!JSON_MODE) {
  console.log(`${C.bold}Super-Intelligence Installation Health Check${C.reset}\n`);
}

// ── Detect vault ────────────────────────────────────────────────────────────
let vault = null;
const carlLink = join(HOME, ".carl");
try {
  const st = lstatSync(carlLink);
  if (st.isSymbolicLink() || st.isDirectory()) {
    // Try reading the link target
    if (process.platform === "win32") {
      // Windows junction — resolve via known paths
      for (const c of [
        join(HOME, "Obsidian", "Knowledge Base"),
        join(HOME, "OneDrive", "Dokument", "Obsidian", "Knowledge Base"),
        join(HOME, "Documents", "Obsidian", "Knowledge Base"),
      ]) {
        if (existsSync(join(c, ".carl", "carl.json"))) { vault = c; break; }
      }
    } else {
      try {
        vault = require("fs").readlinkSync(carlLink);
        // If relative, resolve from parent
        if (vault && !vault.startsWith("/")) {
          vault = join(HOME, vault);
        }
      } catch { /* junction, not symlink */ }
    }
  }
} catch { /* doesn't exist */ }

// Fallback: detect from known paths
if (!vault) {
  for (const c of [
    join(HOME, "Obsidian", "Knowledge Base"),
    join(HOME, "OneDrive", "Dokument", "Obsidian", "Knowledge Base"),
    join(HOME, "Documents", "Obsidian", "Knowledge Base"),
  ]) {
    if (existsSync(join(c, ".carl", "carl.json"))) { vault = c; break; }
  }
}

if (!JSON_MODE) {
  console.log(`Home:  ${HOME}`);
  console.log(`Vault: ${vault || "not found"}\n`);
}

// ── Core files ──────────────────────────────────────────────────────────────
check("carl.json (~/.carl/)", join(HOME, ".carl", "carl.json"));
check("carl-hook.py (~/.claude/hooks/)", join(HOME, ".claude", "hooks", "carl-hook.py"));

// Agent configs
check("CLAUDE.md (~/)", join(HOME, "CLAUDE.md"));
check("AGENTS.md (~/)", join(HOME, "AGENTS.md"));
check("GEMINI.md (~/)", join(HOME, "GEMINI.md"));
check(".claude/settings.json", join(HOME, ".claude", "settings.json"));
check(".mcp.json", join(HOME, ".mcp.json"));

if (vault) {
  // Skills
  check("Skills directory", join(vault, ".agents", "skills"), "dir");

  // Memory
  check("MEMORY.md", join(vault, "memory", "MEMORY.md"));
  check("USER.md", join(vault, "memory", "USER.md"));
  check("sessions.db", join(vault, "memory", "sessions.db"));

  // STATUS
  check("STATUS.md", join(vault, "STATUS.md"));

  // Chorus
  check("Chorus messages", join(vault, ".agent-chorus", "messages"), "dir");
  check("Chorus providers", join(vault, ".agent-chorus", "providers"), "dir");

  // QMD
  check(".qmd.yaml", join(vault, ".qmd.yaml"));
}

// ── MCP Servers ─────────────────────────────────────────────────────────────
const mcpPath = join(HOME, ".mcp.json");
if (existsSync(mcpPath)) {
  try {
    const mcp = JSON.parse(readFileSync(mcpPath, "utf-8"));
    const servers = mcp.mcpServers || {};
    const serverNames = Object.keys(servers);
    if (serverNames.length > 0) {
      let mcpOk = 0;
      for (const [name, cfg] of Object.entries(servers)) {
        if (cfg && cfg.command) {
          // Check if command is resolvable
          const cmdName = cfg.command.split(/[\\/]/).pop().replace(/\.(exe|cmd|bat)$/i, "");
          try {
            const whichCmd = process.platform === "win32"
              ? `powershell -Command "(Get-Command ${cmdName} -ErrorAction SilentlyContinue).Source"`
              : `command -v "${cfg.command}"`;
            const args = whichCmd.split(" ");
            const result = execFileSync(args[0], args.slice(1), {
              stdio: ["ignore", "pipe", "ignore"], timeout: 5000,
            }).toString().trim();
            if (result.length > 0) {
              mcpOk++;
            } else {
              warn(`MCP "${name}": command "${cfg.command}" not found`);
            }
          } catch { warn(`MCP "${name}": cannot verify command "${cfg.command}"`); }
        } else {
          warn(`MCP "${name}": invalid config (no command)`);
        }
      }
      check(`MCP servers (${mcpOk}/${serverNames.length})`, mcpPath, "file");
    } else {
      warn("MCP: no servers configured in .mcp.json");
    }
  } catch (e) {
    warn(`MCP: .mcp.json parse error — ${e.message}`);
  }
} else {
  warn("MCP: .mcp.json not found");
}

// ── Git repo status ─────────────────────────────────────────────────────────
const SI_DIR = join(HOME, "super-intelligence");
if (existsSync(join(SI_DIR, ".git"))) {
  try {
    const status = execFileSync("git", ["-C", SI_DIR, "status", "--porcelain"], {
      stdio: ["ignore", "pipe", "pipe"], timeout: 5000,
    }).toString().trim();
    if (status.length > 0) {
      warn(`Repo super-intelligence: ${status.split("\n").length} dirty files`);
    } else {
      info("Repo super-intelligence: clean");
    }

    const behind = execFileSync("git", ["-C", SI_DIR, "rev-list", "--count", "HEAD..origin/main"], {
      stdio: ["ignore", "pipe", "pipe"], timeout: 5000,
    }).toString().trim();
    if (behind !== "0") {
      warn(`Repo super-intelligence: ${behind} commits behind origin/main`);
    }
  } catch { warn("Repo super-intelligence: git status failed"); }
} else {
  warn("Repo super-intelligence: not a git repo at ~/super-intelligence");
}

// ── Config check ────────────────────────────────────────────────────────────
const siConfig = join(HOME, ".super-intelligence", "config.json");
if (existsSync(siConfig)) {
  try {
    const cfg = JSON.parse(readFileSync(siConfig, "utf-8"));
    if (cfg.auto_update === false) {
      info("Auto-update: disabled");
    } else {
      info(`Auto-update: enabled (last: ${cfg.last_check || "never"})`);
    }
  } catch { warn("Config: ~/.super-intelligence/config.json parse error"); }
} else {
  info("Config: ~/.super-intelligence/config.json not found (auto-update not initialized)");
}

// ── Summary ─────────────────────────────────────────────────────────────────
if (JSON_MODE) {
  console.log(JSON.stringify({
    home: HOME,
    vault,
    ok,
    fail,
    warnings: warnCount,
    results,
  }, null, 2));
} else {
  console.log(`\n${C.bold}═══ Summary ═══${C.reset}`);
  console.log(`${fail === 0 ? C.green : C.red}${ok} OK, ${fail} issues${C.reset}`);
  if (warnCount > 0) console.log(`${C.yellow}${warnCount} warnings${C.reset}`);
  if (fail === 0) console.log(`${C.green}${C.bold}✓ Installation healthy${C.reset}\n`);
  else console.log(`${C.red}${C.bold}✗ ${fail} issues found${C.reset}\n`);
}

process.exit(fail > 0 ? 1 : 0);
