#!/usr/bin/env node
/**
 * Super-Intelligence Agent Stack — Package Health Check
 * Validates all packages across three layers:
 *   1. Npm packages (root + skills/react-components)
 *   2. Skill modules (all dirs under skills/)
 *   3. Subsystems (CARL, Chorus, Hermes, Syncthing, wiki-ingest, karpathy, templates, scripts)
 *
 * Usage: node scripts/health-check.mjs [--json]
 */

import { existsSync, readFileSync, readdirSync, statSync, lstatSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

// ── Resolve project root ────────────────────────────────────────────────────
const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG = join(__dirname, "..");
const HOME = homedir();
const IS_WINDOWS = process.platform === "win32";

// ── CLI flags ────────────────────────────────────────────────────────────────
const jsonMode = process.argv.includes("--json");

// ── Color constants (suppressed in JSON mode) ───────────────────────────────
const C = jsonMode
  ? { green: "", red: "", yellow: "", cyan: "", bold: "", reset: "" }
  : { green: "\x1b[32m", red: "\x1b[31m", yellow: "\x1b[33m", cyan: "\x1b[36m", bold: "\x1b[1m", reset: "\x1b[0m" };

// ── Counters ─────────────────────────────────────────────────────────────────
let passed = 0, failed = 0, warnings = 0, infoItems = 0;

/** @type {Array<{id:string, tier:string, label:string, passed?:boolean, detail?:string}>} */
const allChecks = [];

// ── Helpers ──────────────────────────────────────────────────────────────────

function readText(filePath) {
  const raw = readFileSync(filePath, "utf-8");
  return raw.charCodeAt(0) === 0xFEFF ? raw.slice(1) : raw;
}

function safeJsonParse(filePath) {
  try {
    const text = readText(filePath);
    const data = JSON.parse(text);
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

/**
 * Minimal YAML frontmatter parser.
 * Extracts top-level `key: value` pairs from between `---` delimiters.
 * Handles quoted values and skips nested/indented blocks.
 * Returns null if no frontmatter block is found.
 */
function parseYamlFrontmatter(text) {
  const normalized = text.startsWith("---\r\n") ? "---\n" + text.slice(5) : text;
  if (!normalized.startsWith("---\n")) return null;

  const endIdx = normalized.indexOf("\n---\n", 4);
  if (endIdx === -1) {
    // Try end of file variant (no trailing newline after second ---)
    if (normalized.startsWith("---\n") && normalized.length > 4) {
      const rest = normalized.slice(4);
      const altEnd = rest.indexOf("\n---");
      if (altEnd === -1) return null;
      return parseBlock(rest.slice(0, altEnd));
    }
    return null;
  }

  const block = normalized.slice(4, endIdx);
  return parseBlock(block);
}

function parseBlock(block) {
  const result = {};
  const lines = block.split("\n");
  let pendingKey = null;
  let pendingIndent = 0;

  for (const line of lines) {
    const trimmed = line.trim();
    const indent = line.length - line.trimStart().length;

    if (!trimmed || trimmed.startsWith("#")) continue;

    if (indent === 0) {
      // Top-level key — clears any pending key
      pendingKey = null;
      pendingIndent = 0;

      const colonIdx = trimmed.indexOf(":");
      if (colonIdx === -1) continue;

      const key = trimmed.slice(0, colonIdx).trim();
      let value = trimmed.slice(colonIdx + 1).trim();

      // Strip surrounding quotes
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }

      // Only set if value is non-empty (skip keys that open nested blocks like `metadata:`)
      if (value.length > 0) {
        result[key] = value;
      } else {
        // Mark as pending — may have multi-line block scalar continuation
        pendingKey = key;
        pendingIndent = indent;
      }
    } else if (pendingKey && indent > pendingIndent) {
      // Indented continuation of a pending key — mark it present with placeholder
      result[pendingKey] = result[pendingKey] || "(multi-line)";
    } else {
      // Indented but no pending key, or same-level indentation — reset
      pendingKey = null;
    }
  }

  return result;
}

/**
 * Basic syntax check for .mjs files.
 * Uses `node --check --input-type=module` via stdin for accurate ESM validation.
 * Falls back to new Function() with ESM stripping if subprocess fails.
 */
function checkMjsSyntax(filePath) {
  // Use readText to strip BOM before checking
  let raw;
  try {
    raw = readText(filePath);
  } catch {
    return { ok: false, error: "Could not read file" };
  }
  // Strip shebang if present (#!/usr/bin/env node) — it breaks stdin-based checking.
  // Must do this AFTER BOM stripping (readText handles BOM).
  const code = raw.startsWith("#!") ? raw.slice(raw.indexOf("\n") + 1) : raw;

  // Primary: use node --check for accurate ESM syntax validation
  try {
    execFileSync(process.execPath, ["--check", "--input-type=module"], {
      input: code,
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 5000,
    });
    return { ok: true };
  } catch (e) {
    // node --check failed — extract the actual syntax error message
    const stderr = e.stderr ? e.stderr.toString().trim() : "";
    if (stderr) {
      // Only return the first line of the error for brevity
      const firstLine = stderr.split("\n")[0];
      return { ok: false, error: firstLine };
    }
    // Fallback: strip ESM constructs and try new Function()
    try {
      const adapted = code
        .replace(/^import\s+.+$/gm, "// import stripped")
        .replace(/^export\s+/gm, "// export ")
        .replace(/import\.meta\.url/g, '"file:///"')
        .replace(/await\s+import\s*\(/g, "Promise.resolve(");
      new Function(adapted);
      return { ok: true };
    } catch (e2) {
      return { ok: false, error: e2.message };
    }
  }
}

function fileSizeKB(filePath) {
  try {
    return (statSync(filePath).size / 1024).toFixed(1) + " KB";
  } catch {
    return "unknown";
  }
}

function fileSizeBytes(filePath) {
  try {
    return statSync(filePath).size;
  } catch {
    return 0;
  }
}

// ── Output helpers ──────────────────────────────────────────────────────────

function critical(ok, label, detail = "") {
  const id = `C${passed + failed + 1}`;
  if (ok) {
    if (!jsonMode) console.log(`${C.green}[ok]${C.reset} ${label}`);
    passed++;
    allChecks.push({ id, tier: "critical", label, passed: true });
  } else {
    if (!jsonMode) console.log(`${C.red}[XX]${C.reset} ${label}${detail ? C.red + " — " + detail : ""}${C.reset}`);
    failed++;
    allChecks.push({ id, tier: "critical", label, passed: false, detail });
  }
}

function warn(label, detail = "") {
  if (!jsonMode) console.log(`${C.yellow}[WARN]${C.reset} ${label}${detail ? " — " + detail : ""}`);
  warnings++;
  allChecks.push({ id: `W${warnings}`, tier: "warning", label, detail });
}

function info(label, value) {
  if (!jsonMode) console.log(`${C.cyan}[INFO]${C.reset} ${label}: ${value}`);
  infoItems++;
  allChecks.push({ id: `I${infoItems}`, tier: "info", label, detail: String(value) });
}

function section(title) {
  if (!jsonMode) console.log(`\n${C.bold}── ${title}${C.reset}`);
}

// ── Recursive file counter ──────────────────────────────────────────────────

function countFiles(dir, extFilter = null) {
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    let count = 0;
    for (const e of entries) {
      if (e.isDirectory()) {
        count += countFiles(join(dir, e.name), extFilter);
      } else if (e.isFile()) {
        if (!extFilter || e.name.endsWith(extFilter)) count++;
      }
    }
    return count;
  } catch {
    return 0;
  }
}

function listFilesByExt(dir) {
  /** @type {Record<string, number>} */
  const exts = {};
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
      if (e.isFile()) {
        const dot = e.name.lastIndexOf(".");
        const ext = dot >= 0 ? e.name.slice(dot) : "(none)";
        exts[ext] = (exts[ext] || 0) + 1;
      } else if (e.isDirectory()) {
        const sub = listFilesByExt(join(dir, e.name));
        for (const [k, v] of Object.entries(sub)) {
          exts[k] = (exts[k] || 0) + v;
        }
      }
    }
  } catch {}
  return exts;
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN
// ════════════════════════════════════════════════════════════════════════════

if (!jsonMode) {
  console.log(`${C.bold}Super-Intelligence Agent Stack — Health Check${C.reset}`);
  console.log("=".repeat(55));
}

// Read version
let pkgVersion = "unknown";
try {
  const pkg = JSON.parse(readText(join(PKG, "package.json")));
  pkgVersion = pkg.version || "unknown";
} catch {}
if (!jsonMode) console.log(`Version: ${pkgVersion}\n`);

// ════════════════════════════════════════════════════════════════════════════
// LAYER 1: Npm Packages
// ════════════════════════════════════════════════════════════════════════════
section("Npm Packages");

// 1.1 Root package.json valid JSON
const rootPkg = safeJsonParse(join(PKG, "package.json"));
critical(rootPkg.ok, "Root package.json valid JSON", rootPkg.ok ? "" : rootPkg.error);
const rootPkgData = rootPkg.ok ? rootPkg.data : null;

// 1.2 Version matches VERSION file
const versionFile = join(PKG, "VERSION");
const fileVersion = existsSync(versionFile) ? readFileSync(versionFile, "utf-8").trim() : null;
const rootVersion = rootPkgData ? rootPkgData.version : null;
critical(
  rootVersion && fileVersion && rootVersion === fileVersion,
  `Version ${rootVersion || "?"} matches VERSION file (${fileVersion || "missing"})`,
  rootVersion !== fileVersion ? `Mismatch: pkg=${rootVersion} file=${fileVersion}` : ""
);

// 1.3 Required scripts
if (rootPkgData) {
  const requiredScripts = ["install", "upgrade", "verify"];
  const scripts = rootPkgData.scripts || {};
  for (const s of requiredScripts) {
    const present = typeof scripts[s] === "string" && scripts[s].length > 0;
    critical(present, `Script "${s}" present`, present ? "" : `Missing from package.json scripts`);
  }
}

// 1.4 skills/react-components/package.json
const rcPkgPath = join(PKG, "skills", "react-components", "package.json");
const rcPkg = safeJsonParse(rcPkgPath);
critical(rcPkg.ok, "skills/react-components: package.json valid JSON", rcPkg.ok ? "" : rcPkg.error);
const rcPkgData = rcPkg.ok ? rcPkg.data : null;

// 1.5 react-components lockfile
const rcLock = join(PKG, "skills", "react-components", "package-lock.json");
if (!existsSync(rcLock)) {
  warn("skills/react-components: package-lock.json missing", "Run npm install in skills/react-components/");
}

// 1.6 react-components node_modules
const rcNm = join(PKG, "skills", "react-components", "node_modules");
if (existsSync(rcNm)) {
  // OK — dependencies installed
} else {
  warn("skills/react-components: node_modules missing", "Run npm install in skills/react-components/");
}

// 1.7 react-components scripts
if (rcPkgData) {
  const rcScripts = rcPkgData.scripts || {};
  for (const s of ["validate", "fetch"]) {
    if (!rcScripts[s]) {
      warn(`skills/react-components: script "${s}" missing`);
    }
  }
}

// 1.8 Info: Node engine
if (rootPkgData && rootPkgData.engines && rootPkgData.engines.node) {
  info("Node engine requirement", rootPkgData.engines.node);
}

// ════════════════════════════════════════════════════════════════════════════
// LAYER 2: Skills
// ════════════════════════════════════════════════════════════════════════════
const skillsDir = join(PKG, "skills");
let skillDirs = [];
let skillsWithMd = 0;
let skillsWithFrontmatter = 0;
let skillsWithName = 0;
let skillsNameMismatch = 0;
let skillsNoDescription = 0;
let skillsEmptyMd = 0;
let skillsWithExtraFiles = 0;
let totalSkillFiles = 0;

if (existsSync(skillsDir)) {
  skillDirs = readdirSync(skillsDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  section(`Skills (${skillDirs.length} modules)`);

  for (const name of skillDirs) {
    const dir = join(skillsDir, name);
    const mdPath = join(dir, "SKILL.md");

    // 2.1 Has SKILL.md
    const hasMd = existsSync(mdPath);
    if (hasMd) skillsWithMd++;

    // 2.2-2.6 Frontmatter checks
    if (hasMd) {
      const fileSize = fileSizeBytes(mdPath);

      // 2.5 Not empty
      if (fileSize === 0) {
        skillsEmptyMd++;
      }

      const content = readText(mdPath);
      const fm = parseYamlFrontmatter(content);

      if (fm) {
        skillsWithFrontmatter++;

        // 2.3 Has name field
        if (fm.name && fm.name.length > 0) {
          skillsWithName++;

          // 2.4 Name matches directory (accept colon→hyphen substitution for namespace syntax)
          const normalizedName = fm.name.replace(/:/g, "-");
          if (fm.name !== name && normalizedName !== name) {
            skillsNameMismatch++;
          }
        }

        // 2.6 Has description
        if (!fm.description || fm.description.length === 0) {
          skillsNoDescription++;
        }
      }
    }

    // 2.7 Extra files count
    let fileCount = 0;
    try {
      fileCount = countFiles(dir);
    } catch {}
    totalSkillFiles += fileCount;
    if (fileCount > 1) {
      skillsWithExtraFiles++;
    }
  }

  // Report aggregate results
  critical(
    skillsWithMd === skillDirs.length,
    `${skillsWithMd}/${skillDirs.length} have SKILL.md`,
    skillsWithMd < skillDirs.length
      ? `Missing in: ${skillDirs.filter((n) => !existsSync(join(skillsDir, n, "SKILL.md"))).join(", ")}`
      : ""
  );

  critical(
    skillsWithFrontmatter === skillDirs.length,
    `${skillsWithFrontmatter}/${skillDirs.length} have valid frontmatter`,
    ""
  );

  critical(
    skillsWithName === skillDirs.length,
    `${skillsWithName}/${skillDirs.length} have frontmatter "name" field`,
    ""
  );

  if (skillsNameMismatch > 0) {
    warn(
      `${skillsNameMismatch} skills have name/directory mismatch`,
      skillDirs
        .filter((n) => {
          const p = join(skillsDir, n, "SKILL.md");
          if (!existsSync(p)) return false;
          const fm = parseYamlFrontmatter(readText(p));
          return fm && fm.name && fm.name !== n;
        })
        .join(", ")
    );
  }

  if (skillsEmptyMd > 0) {
    warn(`${skillsEmptyMd} skills have empty SKILL.md`);
  }

  if (skillsNoDescription > 0) {
    warn(`${skillsNoDescription} skills missing "description" in frontmatter`);
  }

  info("Skills with extra supporting files", `${skillsWithExtraFiles}/${skillDirs.length}`);
  info("Total skill files", totalSkillFiles);
} else {
  section("Skills");
  critical(false, "Skills directory exists", skillsDir);
}

// ════════════════════════════════════════════════════════════════════════════
// LAYER 3: Subsystems
// ════════════════════════════════════════════════════════════════════════════
section("Subsystems");

// ── CARL ────────────────────────────────────────────────────────────────────
const carlJsonPath = join(PKG, "carl", "carl.json");
const carlJson = safeJsonParse(carlJsonPath);
critical(carlJson.ok, "CARL: carl.json valid JSON", carlJson.ok ? "" : carlJson.error);

if (carlJson.ok) {
  const d = carlJson.data;
  const hasVersion = typeof d.version === "number" || typeof d.version === "string";
  const hasConfig = typeof d.config === "object" && d.config !== null;
  const hasDomains = typeof d.domains === "object" && d.domains !== null;

  critical(
    hasVersion && hasConfig && hasDomains,
    "CARL: carl.json has required keys (version, config, domains)",
    [!hasVersion && "version", !hasConfig && "config", !hasDomains && "domains"].filter(Boolean).join(", ") || ""
  );

  if (hasDomains) {
    const domainCount = Object.keys(d.domains).length;
    info("CARL: domains", domainCount);
  }
}

const carlHookPath = join(PKG, "carl", "carl-hook.py");
if (existsSync(carlHookPath)) {
  // OK
} else {
  warn("CARL: carl-hook.py missing");
}
info("CARL: carl-hook.py size", existsSync(carlHookPath) ? fileSizeKB(carlHookPath) : "missing");

// ── Chorus ──────────────────────────────────────────────────────────────────
const relayPath = join(PKG, "chorus", "relay-config.json");
if (existsSync(relayPath)) {
  const relayJson = safeJsonParse(relayPath);
  critical(relayJson.ok, "Chorus: relay-config.json valid JSON", relayJson.ok ? "" : relayJson.error);
} else {
  warn("Chorus: relay-config.json missing");
}

const chorusProviders = join(PKG, "chorus", "providers");
if (existsSync(chorusProviders)) {
  let providerCount = 0;
  try {
    providerCount = readdirSync(chorusProviders, { withFileTypes: true }).filter((e) => e.isFile()).length;
  } catch {}
  if (providerCount > 0) {
    info("Chorus: providers", providerCount);
  } else {
    warn("Chorus: providers/ directory empty or missing");
  }
} else {
  warn("Chorus: providers/ directory missing");
}

const agentContextMd = join(PKG, "chorus", "AGENT_CONTEXT.md");
if (existsSync(agentContextMd)) {
  // OK
} else {
  warn("Chorus: AGENT_CONTEXT.md missing");
}

// ── Hermes ──────────────────────────────────────────────────────────────────
if (existsSync(join(PKG, "hermes", "README.md"))) {
  // OK
} else {
  warn("Hermes: README.md missing");
}

// ── Syncthing ───────────────────────────────────────────────────────────────
if (existsSync(join(PKG, "syncthing", "README.md"))) {
  // OK
} else {
  warn("Syncthing: README.md missing");
}

// ── Wiki-ingest ─────────────────────────────────────────────────────────────
if (existsSync(join(PKG, "wiki-ingest", "README.md"))) {
  // OK
} else {
  warn("Wiki-ingest: README.md missing");
}

// ── Karpathy ────────────────────────────────────────────────────────────────
if (existsSync(join(PKG, "karpathy", "wiki-setup.md"))) {
  // OK
} else {
  warn("Karpathy: wiki-setup.md missing");
}

// ── Templates ───────────────────────────────────────────────────────────────
const templatesDir = join(PKG, "templates");
if (existsSync(templatesDir)) {
  let templateCount = 0;
  try {
    templateCount = countFiles(templatesDir);
  } catch {}
  info("Templates: files", templateCount);

  // Check JSON/YAML templates parse
  try {
    const tmplEntries = readdirSync(templatesDir, { withFileTypes: true });
    for (const e of tmplEntries) {
      if (e.isFile()) {
        const name = e.name;
        if (name.endsWith(".json") || name.endsWith(".yaml") || name.endsWith(".yml")) {
          const tp = join(templatesDir, name);
          if (name.endsWith(".json")) {
            const parsed = safeJsonParse(tp);
            if (!parsed.ok) warn(`Template "${name}" is invalid JSON`, parsed.error);
          }
        }
      }
    }
  } catch {}
} else {
  warn("Templates: directory missing");
}

// ── Scripts ─────────────────────────────────────────────────────────────────
const scriptsPath = join(PKG, "scripts");
if (existsSync(scriptsPath)) {
  const exts = listFilesByExt(scriptsPath);
  const totalScripts = Object.values(exts).reduce((a, b) => a + b, 0);
  info("Scripts: total files", totalScripts);

  const extOrder = [".mjs", ".sh", ".ps1", ".cmd", ".py", ".js", ".json"];
  const parts = [];
  for (const ext of extOrder) {
    if (exts[ext]) parts.push(`${exts[ext]} ${ext}`);
    delete exts[ext];
  }
  for (const [ext, count] of Object.entries(exts).sort()) {
    parts.push(`${count} ${ext}`);
  }
  if (parts.length > 0) {
    info("Scripts: by type", parts.join(", "));
  }

  // Check .mjs files parse
  try {
    const scriptEntries = readdirSync(scriptsPath, { withFileTypes: true });
    for (const e of scriptEntries) {
      if (e.isFile() && e.name.endsWith(".mjs")) {
        const sp = join(scriptsPath, e.name);
        const syntax = checkMjsSyntax(sp);
        if (!syntax.ok) {
          warn(`Script "${e.name}" may have syntax errors`, syntax.error);
        }
      }
    }
  } catch {}

  // Check .sh files have shebangs
  try {
    const scriptEntries = readdirSync(scriptsPath, { withFileTypes: true });
    for (const e of scriptEntries) {
      if (e.isFile() && e.name.endsWith(".sh")) {
        const sp = join(scriptsPath, e.name);
        const firstLine = readFileSync(sp, "utf-8").split("\n")[0].trim();
        if (!firstLine.startsWith("#!/")) {
          warn(`Script "${e.name}" has no shebang`, `First line: "${firstLine.slice(0, 40)}"`);
        }
      }
    }
  } catch {}
} else {
  warn("Scripts: directory missing");
}

// ════════════════════════════════════════════════════════════════════════════
// LAYER 4: Installed System (only with --installed flag)
// ════════════════════════════════════════════════════════════════════════════
const INSTALLED = process.argv.includes("--installed");

if (INSTALLED) {
  section("Installed System");

  // ── MCP Servers ──────────────────────────────────────────────────────────
  const mcpJsonPath = join(HOME, ".mcp.json");
  if (existsSync(mcpJsonPath)) {
    const mcp = safeJsonParse(mcpJsonPath);
    if (mcp.ok && mcp.data.mcpServers) {
      const servers = Object.entries(mcp.data.mcpServers);
      let mcpOk = 0, mcpFail = 0;
      for (const [name, cfg] of servers) {
        if (!cfg || typeof cfg.command !== "string") {
          warn(`MCP "${name}": missing or invalid command`);
          mcpFail++;
          continue;
        }
        // Check command exists (simple which/where)
        const cmdName = cfg.command.split(/[\\/]/).pop().replace(/\.(exe|cmd|bat)$/i, "");
        let cmdFound = false;
        try {
          const whichCmd = IS_WINDOWS
            ? `powershell -Command "(Get-Command ${cmdName} -ErrorAction SilentlyContinue).Source"`
            : `command -v "${cfg.command}"`;
          const result = execFileSync(whichCmd.split(" ")[0], whichCmd.split(" ").slice(1), {
            stdio: ["ignore", "pipe", "ignore"], timeout: 5000,
          }).toString().trim();
          cmdFound = result.length > 0;
        } catch { cmdFound = false; }
        if (cmdFound) {
          mcpOk++;
        } else {
          warn(`MCP "${name}": command "${cfg.command}" not found in PATH`);
          mcpFail++;
        }
      }
      critical(mcpFail === 0, `MCP servers: ${mcpOk + mcpFail} configured, ${mcpOk} OK, ${mcpFail} missing`);
    } else {
      warn("MCP: ~/.mcp.json has no mcpServers entry");
    }
  } else {
    warn("MCP: ~/.mcp.json not found — no MCP servers configured");
  }

  // ── CARL Hook Wiring ─────────────────────────────────────────────────────
  const settingsPath = join(HOME, ".claude", "settings.json");
  if (existsSync(settingsPath)) {
    const settings = safeJsonParse(settingsPath);
    if (settings.ok) {
      const hooks = settings.data.hooks || {};
      const upsHooks = hooks.UserPromptSubmit || [];
      let carlWired = false;
      for (const h of upsHooks) {
        const cmds = h.hooks || [];
        for (const c of cmds) {
          if (c.command && c.command.includes("carl-hook.py")) {
            carlWired = true;
            break;
          }
        }
      }
      critical(carlWired, "CARL hook wired in ~/.claude/settings.json",
        carlWired ? "" : "carl-hook.py not found in UserPromptSubmit hooks");
    } else {
      warn(`~/.claude/settings.json invalid: ${settings.error}`);
    }
  } else {
    warn("~/.claude/settings.json not found — CARL hook may not be wired");
  }

  // ── CARL Hook Version ────────────────────────────────────────────────────
  const carlHookInstalled = join(HOME, ".claude", "hooks", "carl-hook.py");
  if (existsSync(carlHookInstalled)) {
    try {
      const hookContent = readText(carlHookInstalled);
      const hookVer = hookContent.match(/CARL_HOOK_VERSION=([\d.]+)/)?.[1];
      if (hookVer) {
        info("CARL: carl-hook.py version", hookVer);
      } else {
        warn("CARL: carl-hook.py has no CARL_HOOK_VERSION");
      }
    } catch { warn("CARL: cannot read carl-hook.py"); }
  } else {
    critical(false, "CARL: carl-hook.py", "Not installed at ~/.claude/hooks/carl-hook.py");
  }

  // ── Junctions ────────────────────────────────────────────────────────────
  const carlLink = join(HOME, ".carl");
  const agentsLink = join(HOME, ".agents");
  try {
    const carlStat = lstatSync(carlLink);
    const carlOk = carlStat.isDirectory() || carlStat.isSymbolicLink();
    critical(carlOk, "Junction ~/.carl exists", carlOk ? "" : "Exists but not a directory/junction");
  } catch {
    critical(false, "Junction ~/.carl exists", "Missing — run install.mjs");
  }
  try {
    const agentsStat = lstatSync(agentsLink);
    const agentsOk = agentsStat.isDirectory() || agentsStat.isSymbolicLink();
    critical(agentsOk, "Junction ~/.agents exists", agentsOk ? "" : "Exists but not a directory/junction");
  } catch {
    critical(false, "Junction ~/.agents exists", "Missing — run install.mjs");
  }

  // ── Git Repo Status ──────────────────────────────────────────────────────
  try {
    const repoStatus = execFileSync("git", ["-C", PKG, "status", "--porcelain"], {
      stdio: ["ignore", "pipe", "pipe"], timeout: 5000,
    }).toString().trim();
    if (repoStatus.length > 0) {
      warn("Repo has uncommitted changes", `git status: ${repoStatus.split("\n").length} files`);
    }
    const behindCount = execFileSync("git", ["-C", PKG, "rev-list", "--count", "HEAD..origin/main"], {
      stdio: ["ignore", "pipe", "pipe"], timeout: 5000,
    }).toString().trim();
    if (behindCount !== "0") {
      warn(`Repo is ${behindCount} commits behind origin/main`);
    }
    info("Repo git status", "clean");
  } catch {
    warn("Repo git status check failed");
  }
}

// ════════════════════════════════════════════════════════════════════════════
// SUMMARY
// ════════════════════════════════════════════════════════════════════════════

if (jsonMode) {
  const output = {
    version: pkgVersion,
    timestamp: new Date().toISOString(),
    summary: {
      critical: { passed, failed },
      warnings,
      info: infoItems,
    },
    checks: allChecks,
  };
  console.log(JSON.stringify(output, null, 2));
} else {
  console.log(`\n${C.bold}═══ Summary ═════════════════════════════════════${C.reset}`);
  const critLine =
    failed === 0
      ? `${C.green}Critical: ${passed} passed, 0 failed${C.reset}`
      : `${C.red}Critical: ${passed} passed, ${failed} failed${C.reset}`;
  console.log(critLine);
  if (warnings > 0) {
    console.log(`${C.yellow}Warnings: ${warnings}${C.reset}`);
  } else {
    console.log(`Warnings: 0`);
  }
  if (infoItems > 0) {
    console.log(`${C.cyan}Info: ${infoItems} items${C.reset}`);
  }
  console.log("");
  if (failed === 0) {
    console.log(`${C.green}${C.bold}✓ All critical checks passed${C.reset}`);
  } else {
    console.log(`${C.red}${C.bold}✗ ${failed} critical check(s) failed${C.reset}`);
  }
  console.log("");
}

// ── Exit code ───────────────────────────────────────────────────────────────
process.exit(failed > 0 ? 1 : 0);
