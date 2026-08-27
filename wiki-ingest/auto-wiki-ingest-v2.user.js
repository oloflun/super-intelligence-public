// ==UserScript==
// @name         Auto Wiki Ingest v2 — Auto-Export + Sweep + Overwrite
// @namespace    https://github.com/anton-wiki
// @version      2.1.0
// @description  Companion to RevivalStack AI Chat Exporter. Auto-exports on navigation, overwrites when continued, sweeps sidebar with early-stop for mobile/desktop chats.
// @author       Anton (built with Claude)
// @license      MIT
// @match        https://chatgpt.com/*
// @match        https://chat.openai.com/*
// @match        https://claude.ai/*
// @match        https://gemini.google.com/*
// @match        https://copilot.microsoft.com/*
// @match        https://grok.com/*
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_notification
// @grant        GM_deleteValue
// @grant        GM_registerMenuCommand
// @noframes
// @run-at       document-idle
// ==/UserScript==

(function () {
  "use strict";

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  CONFIGURATION                                                  ║
  // ╚══════════════════════════════════════════════════════════════════╝

  const CONFIG = {
    // Minimum user messages before auto-export triggers
    MIN_USER_MESSAGES: 1,

    // How often (ms) to poll for message count changes
    POLL_INTERVAL_MS: 4000,

    // Show desktop notification on export?
    SHOW_NOTIFICATIONS: true,

    // Enable auto-export on navigation (toggle via 📚 indicator)
    ENABLED: true,

    // Debug logging to console
    DEBUG: false,

    // ── Sweep mode ──
    // Delay between opening each conversation during sweep (ms).
    // Must be long enough for DOM to load + export to trigger.
    SWEEP_NAV_DELAY_MS: 5000,

    // How many consecutive "already up to date" conversations
    // to encounter before stopping the sweep. Sidebars are sorted
    // newest-first, so hitting a run of unchanged chats means
    // we've reached the boundary of the previous sweep.
    SWEEP_CONSECUTIVE_UNCHANGED_LIMIT: 3,
  };

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  STATE                                                          ║
  // ╚══════════════════════════════════════════════════════════════════╝

  let currentUrl = location.href;
  let lastMessageCount = 0;
  let pollIntervalId = null;
  let sweepInProgress = false;

  function log(...args) {
    if (CONFIG.DEBUG) console.log("[AutoWiki]", ...args);
  }

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  EXPORT LEDGER                                                  ║
  // ║                                                                 ║
  // ║  Maps: conversationURL → { filename, messageCount, timestamp }  ║
  // ║  This replaces the simple set. Allows detecting when a          ║
  // ║  conversation has grown (was continued) and needs re-export.    ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function getLedger() {
    try {
      return JSON.parse(GM_getValue("exportLedger", "{}"));
    } catch {
      return {};
    }
  }

  function saveLedger(ledger) {
    // Prune to 2000 entries max (oldest first by timestamp)
    const entries = Object.entries(ledger);
    if (entries.length > 2000) {
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      const pruned = Object.fromEntries(entries.slice(entries.length - 2000));
      GM_setValue("exportLedger", JSON.stringify(pruned));
    } else {
      GM_setValue("exportLedger", JSON.stringify(ledger));
    }
  }

  function getLedgerEntry(url) {
    const key = normalizeConversationUrl(url);
    return getLedger()[key] || null;
  }

  function setLedgerEntry(url, messageCount, filename) {
    const ledger = getLedger();
    const key = normalizeConversationUrl(url);
    ledger[key] = {
      filename,
      messageCount,
      timestamp: Date.now(),
    };
    saveLedger(ledger);
  }

  /**
   * Strip query params and fragments to get a stable conversation URL key.
   * e.g. https://claude.ai/chat/abc-123?foo=bar → https://claude.ai/chat/abc-123
   */
  function normalizeConversationUrl(url) {
    try {
      const u = new URL(url);
      return u.origin + u.pathname;
    } catch {
      return url;
    }
  }

  // ── Sweep timestamp ──────────────────────────────────────────────
  // Stored per-platform so sweeps on claude.ai don't affect chatgpt.

  function getLastSweepTime() {
    return GM_getValue(`lastSweepTime_${detectPlatform()}`, 0);
  }

  function setLastSweepTime(ts) {
    GM_setValue(`lastSweepTime_${detectPlatform()}`, ts);
  }

  /**
   * Returns true if a conversation was already exported at or after
   * `sinceTimestamp` and has not gained any new messages since.
   * This is the signal that we've reached "old territory" in the
   * sidebar and can stop sweeping.
   */
  function wasExportedAndUnchangedSince(url, currentTotalMessages, sinceTimestamp) {
    const entry = getLedgerEntry(url);
    if (!entry) return false; // Never exported → not unchanged
    if (entry.timestamp < sinceTimestamp) return false; // Exported before the cutoff
    if (currentTotalMessages > entry.messageCount) return false; // Grew since export
    return true; // Exported after cutoff and same size → unchanged
  }

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  PLATFORM DETECTION                                             ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function detectPlatform() {
    const host = location.hostname;
    if (host.includes("chatgpt.com") || host.includes("chat.openai.com")) return "chatgpt";
    if (host.includes("claude.ai")) return "claude";
    if (host.includes("gemini.google.com")) return "gemini";
    if (host.includes("copilot.microsoft.com")) return "copilot";
    if (host.includes("grok.com")) return "grok";
    return "unknown";
  }

  const PLATFORM = detectPlatform();

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  MESSAGE COUNTING                                               ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function countUserMessages() {
    switch (PLATFORM) {
      case "chatgpt": {
        const articles = document.querySelectorAll("article");
        let count = 0;
        articles.forEach((a) => {
          const h5 = a.querySelector("h5");
          if (h5 && h5.textContent.toLowerCase().includes("you said")) count++;
        });
        return count;
      }
      case "claude":
        return document.querySelectorAll(".font-user-message").length;
      case "gemini":
        return document.querySelectorAll("user-query").length;
      case "copilot":
        return document.querySelectorAll('[data-content="user-message"]').length;
      case "grok":
        return document.querySelectorAll('[data-testid="user-message"]').length;
      default:
        return 0;
    }
  }

  function countTotalMessages() {
    switch (PLATFORM) {
      case "chatgpt":
        return document.querySelectorAll("article").length;
      case "claude":
        return document.querySelectorAll(
          ".font-claude-message:not(#markdown-artifact), .font-user-message"
        ).length;
      case "gemini":
        return document.querySelectorAll("user-query, model-response").length;
      case "copilot":
        return document.querySelectorAll(
          '[data-content="user-message"], [data-content="ai-message"]'
        ).length;
      default:
        return 0;
    }
  }

  function isOnConversationPage() {
    switch (PLATFORM) {
      case "chatgpt":
        return /\/c\//.test(location.pathname) || countUserMessages() > 0;
      case "claude":
        return /\/chat\//.test(location.pathname);
      case "gemini":
        return /\/app\//.test(location.pathname) && countUserMessages() > 0;
      case "copilot":
      case "grok":
        return countUserMessages() > 0;
      default:
        return false;
    }
  }

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  EXPORT TRIGGER                                                 ║
  // ║                                                                 ║
  // ║  Core logic: compare current message count with ledger.         ║
  // ║  If count grew → conversation was continued → re-export.        ║
  // ║  The watcher script handles file overwrite via matching URL.    ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function shouldExport() {
    if (!CONFIG.ENABLED) return { should: false, reason: "disabled" };
    if (!isOnConversationPage()) return { should: false, reason: "not on conversation page" };

    const userMsgCount = countUserMessages();
    if (userMsgCount < CONFIG.MIN_USER_MESSAGES) {
      return { should: false, reason: `only ${userMsgCount} user messages` };
    }

    const totalCount = countTotalMessages();
    const url = location.href;
    const existing = getLedgerEntry(url);

    if (!existing) {
      // Never exported → export
      return { should: true, reason: "new conversation" };
    }

    if (totalCount > existing.messageCount) {
      // Conversation has grown → re-export (overwrite)
      return {
        should: true,
        reason: `conversation continued (${existing.messageCount} → ${totalCount} messages)`,
        previousFilename: existing.filename,
      };
    }

    // Same message count → skip
    return { should: false, reason: "no new messages since last export" };
  }

  function triggerExport(force = false) {
    const check = force
      ? { should: true, reason: "forced" }
      : shouldExport();

    if (!check.should) {
      log(`Skip export: ${check.reason}`);
      return false;
    }

    // Ensure all messages are selected in the RevivalStack outline
    const selectAll = document.querySelector("#outline-select-all");
    if (selectAll && !selectAll.checked) {
      selectAll.click();
    }

    const exportBtn = document.querySelector("#export-markdown-btn");
    if (!exportBtn) {
      log("RevivalStack export button not found. Is the exporter installed?");
      return false;
    }

    log(`Exporting: ${check.reason}`);

    // Intercept the download to capture the filename
    const origCreateElement = document.createElement.bind(document);
    let capturedFilename = null;

    // Monkey-patch URL.createObjectURL temporarily to intercept the download
    const origClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function () {
      if (this.download && this.href && this.href.startsWith("blob:")) {
        capturedFilename = this.download;
        log(`Captured filename: ${capturedFilename}`);
      }
      return origClick.apply(this, arguments);
    };

    // Small delay to let select-all propagate
    setTimeout(() => {
      exportBtn.click();

      // Restore after a tick
      setTimeout(() => {
        HTMLAnchorElement.prototype.click = origClick;

        const totalCount = countTotalMessages();
        const url = location.href;
        const fname = capturedFilename || `${PLATFORM}_${Date.now()}.md`;

        // Record in ledger
        setLedgerEntry(url, totalCount, fname);

        log(`Exported: ${fname} (${totalCount} total messages)`);

        if (CONFIG.SHOW_NOTIFICATIONS && !sweepInProgress) {
          try {
            const verb = check.previousFilename ? "Updated" : "Exported";
            GM_notification({
              title: `Wiki: ${verb}`,
              text: `${PLATFORM} conversation (${totalCount} msgs)`,
              timeout: 2500,
            });
          } catch {}
        }
      }, 200);
    }, selectAll && !selectAll.checked ? 300 : 50);

    return true;
  }

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  NAVIGATION DETECTION                                           ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function onNavigateAway() {
    if (sweepInProgress) return; // Sweep handles its own exports
    triggerExport();
  }

  function hookHistoryMethods() {
    const origPush = history.pushState;
    const origReplace = history.replaceState;

    history.pushState = function (...args) {
      const newUrl = args[2];
      if (newUrl && currentUrl !== String(newUrl)) {
        log("pushState →", newUrl);
        onNavigateAway();
      }
      const result = origPush.apply(this, args);
      currentUrl = location.href;
      lastMessageCount = 0;
      return result;
    };

    history.replaceState = function (...args) {
      const newUrl = args[2];
      if (newUrl && currentUrl !== String(newUrl)) {
        log("replaceState →", newUrl);
        onNavigateAway();
      }
      const result = origReplace.apply(this, args);
      currentUrl = location.href;
      return result;
    };
  }

  window.addEventListener("popstate", () => {
    if (currentUrl !== location.href) {
      log("popstate →", location.href);
      onNavigateAway();
      currentUrl = location.href;
      lastMessageCount = 0;
    }
  });

  window.addEventListener("beforeunload", () => {
    onNavigateAway();
  });

  // URL polling fallback for SPAs
  setInterval(() => {
    if (location.href !== currentUrl) {
      log("URL poll →", location.href);
      onNavigateAway();
      currentUrl = location.href;
      lastMessageCount = 0;
    }
  }, 1500);

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  ACTIVITY TRACKING                                              ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function startActivityPoll() {
    pollIntervalId = setInterval(() => {
      if (!isOnConversationPage()) return;
      const count = countTotalMessages();
      if (count !== lastMessageCount) {
        lastMessageCount = count;
        log(`Message count: ${count}`);
      }
    }, CONFIG.POLL_INTERVAL_MS);
  }

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  SWEEP MODE                                                     ║
  // ║                                                                 ║
  // ║  Cycles through sidebar conversations to export ones that       ║
  // ║  were started on mobile/desktop and haven't been exported,      ║
  // ║  or that have been continued since last export.                 ║
  // ║                                                                 ║
  // ║  Trigger: Alt+Shift+S or via Tampermonkey menu.                 ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function getSidebarConversationLinks() {
    let links = [];

    switch (PLATFORM) {
      case "claude": {
        // Claude.ai sidebar: <a> tags with href matching /chat/{uuid}
        const allLinks = document.querySelectorAll('a[href*="/chat/"]');
        allLinks.forEach((a) => {
          const href = a.getAttribute("href");
          // Filter to actual conversation links (not settings, projects, etc.)
          if (href && /\/chat\/[a-f0-9-]{8,}/.test(href)) {
            const fullUrl = new URL(href, location.origin).href;
            links.push({
              url: fullUrl,
              title: a.textContent.trim().slice(0, 60),
              element: a,
            });
          }
        });
        break;
      }

      case "chatgpt": {
        // ChatGPT sidebar: <a> tags with href matching /c/{id}
        const allLinks = document.querySelectorAll('a[href*="/c/"]');
        allLinks.forEach((a) => {
          const href = a.getAttribute("href");
          if (href && /\/c\/[a-f0-9-]{8,}/.test(href)) {
            const fullUrl = new URL(href, location.origin).href;
            links.push({
              url: fullUrl,
              title: a.textContent.trim().slice(0, 60),
              element: a,
            });
          }
        });
        break;
      }

      case "gemini": {
        // Gemini: sidebar items with data-test-id="conversation"
        const items = document.querySelectorAll('[data-test-id="conversation"]');
        items.forEach((item) => {
          const a = item.closest("a") || item.querySelector("a");
          if (a && a.href) {
            links.push({
              url: a.href,
              title: item.textContent.trim().slice(0, 60),
              element: a,
            });
          }
        });
        break;
      }

      default:
        log(`Sweep not supported for platform: ${PLATFORM}`);
    }

    // Deduplicate by normalized URL
    const seen = new Set();
    links = links.filter((link) => {
      const key = normalizeConversationUrl(link.url);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    return links;
  }

  async function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  async function waitForMessages(timeoutMs = 8000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      if (countTotalMessages() > 0) return true;
      await sleep(500);
    }
    return false;
  }

  async function runSweep() {
    if (sweepInProgress) {
      alert("Sweep already in progress.");
      return;
    }

    const links = getSidebarConversationLinks();
    if (links.length === 0) {
      alert("No conversations found in sidebar. Make sure the sidebar is open/visible.");
      return;
    }

    const lastSweep = getLastSweepTime();
    const lastSweepDate = lastSweep
      ? new Date(lastSweep).toLocaleString()
      : "never";

    const proceed = confirm(
      `Wiki Sweep: ${links.length} conversations in sidebar.\n` +
      `Last sweep: ${lastSweepDate}\n\n` +
      `Will stop early once it hits ${CONFIG.SWEEP_CONSECUTIVE_UNCHANGED_LIMIT} ` +
      `consecutive conversations unchanged since last sweep.\n\n` +
      `Don't interact until it finishes. Continue?`
    );

    if (!proceed) return;

    sweepInProgress = true;
    const sweepStartTime = Date.now();
    let exported = 0;
    let skipped = 0;
    let errors = 0;
    let consecutiveUnchanged = 0;
    let stoppedEarly = false;

    // Show progress indicator
    const progressEl = document.createElement("div");
    Object.assign(progressEl.style, {
      position: "fixed",
      top: "10px",
      left: "50%",
      transform: "translateX(-50%)",
      zIndex: "99999",
      background: "rgba(91, 63, 135, 0.95)",
      color: "white",
      padding: "12px 24px",
      borderRadius: "8px",
      fontSize: "14px",
      fontFamily: "system-ui, sans-serif",
      boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
    });
    document.body.appendChild(progressEl);

    const originalUrl = location.href;

    for (let i = 0; i < links.length; i++) {
      const conv = links[i];
      progressEl.textContent =
        `Sweep: ${i + 1}/${links.length} — ${conv.title || "..."} ` +
        `(${exported} exported, ${skipped} skipped)`;

      try {
        // Navigate to the conversation
        conv.element.click();
        await sleep(1500);

        // Wait for messages to appear in DOM
        const loaded = await waitForMessages(8000);
        if (!loaded) {
          log(`Sweep: No messages loaded for ${conv.url}`);
          skipped++;
          // A conversation with zero messages is not "unchanged since last sweep",
          // so don't count it toward the early-stop streak.
          continue;
        }

        // Wait for RevivalStack to rebuild its outline
        await sleep(1500);

        const totalMessages = countTotalMessages();

        // ── Early termination check ──
        // If this conversation was already exported during/after the last sweep
        // AND has not grown, count it toward the consecutive-unchanged streak.
        if (lastSweep > 0 && wasExportedAndUnchangedSince(location.href, totalMessages, lastSweep)) {
          consecutiveUnchanged++;
          skipped++;
          log(
            `Sweep: Unchanged since last sweep: ${conv.title} ` +
            `(${consecutiveUnchanged}/${CONFIG.SWEEP_CONSECUTIVE_UNCHANGED_LIMIT})`
          );

          if (consecutiveUnchanged >= CONFIG.SWEEP_CONSECUTIVE_UNCHANGED_LIMIT) {
            stoppedEarly = true;
            log(
              `Sweep: Hit ${CONFIG.SWEEP_CONSECUTIVE_UNCHANGED_LIMIT} consecutive ` +
              `unchanged conversations. Stopping — everything below this point ` +
              `was already covered by the last sweep.`
            );
            break;
          }

          await sleep(CONFIG.SWEEP_NAV_DELAY_MS);
          continue;
        }

        // Reset streak — this conversation is new or has changed
        consecutiveUnchanged = 0;

        // Check if export is needed
        const check = shouldExport();
        if (check.should) {
          triggerExport();
          exported++;
          log(`Sweep: Exported ${conv.url} (${check.reason})`);
        } else {
          skipped++;
          log(`Sweep: Skipped ${conv.url} (${check.reason})`);
        }

        await sleep(CONFIG.SWEEP_NAV_DELAY_MS);
      } catch (err) {
        log(`Sweep error on ${conv.url}:`, err);
        errors++;
        // Errors don't count as "unchanged" — don't let a glitch stop the sweep
        consecutiveUnchanged = 0;
      }
    }

    // Record this sweep's start time so the next sweep knows where to stop
    setLastSweepTime(sweepStartTime);

    // Return to original conversation
    try {
      window.location.href = originalUrl;
    } catch {}

    const earlyNote = stoppedEarly
      ? ` (stopped early — reached previous sweep boundary)`
      : "";
    progressEl.textContent =
      `Sweep done: ${exported} exported, ${skipped} unchanged, ${errors} errors${earlyNote}`;
    setTimeout(() => progressEl.remove(), 6000);

    sweepInProgress = false;

    if (CONFIG.SHOW_NOTIFICATIONS) {
      try {
        GM_notification({
          title: "Wiki Sweep Complete",
          text: `${exported} exported, ${skipped} unchanged${earlyNote}`,
          timeout: 5000,
        });
      } catch {}
    }
  }

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  KEYBOARD SHORTCUTS                                             ║
  // ╚══════════════════════════════════════════════════════════════════╝

  document.addEventListener("keydown", (e) => {
    const tag = document.activeElement?.tagName;
    const inInput = tag === "INPUT" || tag === "TEXTAREA" || document.activeElement?.isContentEditable;
    if (inInput) return;

    // Alt+Shift+E → Force export current conversation
    if (e.altKey && e.shiftKey && e.key === "E") {
      e.preventDefault();
      log("Force export via Alt+Shift+E");
      triggerExport(true);
    }

    // Alt+Shift+S → Run sweep mode
    if (e.altKey && e.shiftKey && e.key === "S") {
      e.preventDefault();
      log("Sweep mode via Alt+Shift+S");
      runSweep();
    }
  });

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  TAMPERMONKEY MENU COMMANDS                                     ║
  // ╚══════════════════════════════════════════════════════════════════╝

  try {
    GM_registerMenuCommand("📚 Sweep sidebar conversations", runSweep);
    GM_registerMenuCommand("🔄 Force re-export current chat", () => triggerExport(true));
    GM_registerMenuCommand("📊 Show export ledger stats", () => {
      const ledger = getLedger();
      const count = Object.keys(ledger).length;
      const platforms = {};
      Object.values(ledger).forEach((entry) => {
        const match = entry.filename?.match(/^(\w+)[_-]/);
        const p = match ? match[1] : "unknown";
        platforms[p] = (platforms[p] || 0) + 1;
      });
      alert(
        `Export Ledger: ${count} conversations tracked\n\n` +
        Object.entries(platforms)
          .map(([p, n]) => `  ${p}: ${n}`)
          .join("\n")
      );
    });
    GM_registerMenuCommand("🗑️ Clear export ledger", () => {
      if (confirm("Clear all export history? This will cause all conversations to be re-exported on next navigation.")) {
        GM_setValue("exportLedger", "{}");
        alert("Ledger cleared.");
      }
    });
    GM_registerMenuCommand("🐛 Toggle debug logging", () => {
      CONFIG.DEBUG = !CONFIG.DEBUG;
      alert(`Debug logging: ${CONFIG.DEBUG ? "ON" : "OFF"}`);
    });
    GM_registerMenuCommand("⏱️ Show/reset last sweep time", () => {
      const ts = getLastSweepTime();
      const display = ts ? new Date(ts).toLocaleString() : "never";
      if (confirm(`Last sweep on ${PLATFORM}: ${display}\n\nClick OK to reset (next sweep will be full).`)) {
        setLastSweepTime(0);
        alert("Sweep timestamp cleared. Next sweep will visit all conversations.");
      }
    });
  } catch {}

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  STATUS INDICATOR                                               ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function addStatusIndicator() {
    if (document.querySelector("#auto-wiki-indicator")) return;

    const el = document.createElement("div");
    el.id = "auto-wiki-indicator";
    el.textContent = "📚";
    el.title =
      "Auto Wiki Ingest v2\n" +
      "─────────────────\n" +
      "Click: toggle auto-export\n" +
      "Alt+Shift+E: force export\n" +
      "Alt+Shift+S: sweep sidebar";
    Object.assign(el.style, {
      position: "fixed",
      bottom: "70px",
      right: "330px",
      zIndex: "9997",
      fontSize: "18px",
      cursor: "pointer",
      opacity: CONFIG.ENABLED ? "1" : "0.3",
      transition: "opacity 0.3s",
      userSelect: "none",
      filter: CONFIG.ENABLED ? "none" : "grayscale(1)",
    });

    el.addEventListener("click", () => {
      CONFIG.ENABLED = !CONFIG.ENABLED;
      el.style.opacity = CONFIG.ENABLED ? "1" : "0.3";
      el.style.filter = CONFIG.ENABLED ? "none" : "grayscale(1)";
      log(`Auto-export ${CONFIG.ENABLED ? "ON" : "OFF"}`);
    });

    document.body.appendChild(el);
  }

  // ╔══════════════════════════════════════════════════════════════════╗
  // ║  INIT                                                           ║
  // ╚══════════════════════════════════════════════════════════════════╝

  function init() {
    log(`Platform: ${PLATFORM}, URL: ${currentUrl}`);
    hookHistoryMethods();
    startActivityPoll();
    setTimeout(addStatusIndicator, 3000);
    log("Auto Wiki Ingest v2 ready.");
  }

  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(init, 2000);
  } else {
    window.addEventListener("DOMContentLoaded", () => setTimeout(init, 2000));
  }
})();
