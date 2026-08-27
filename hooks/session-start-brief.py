#!/usr/bin/env python
"""SessionStart -- snabb auto-standup + sessionsregister. Fas 2.3.

Ersatter det GAMLA hindret mot auto-standup: /standup-skillen ar langsam for att
den ar LLM-arbete (las+syntes i modellen). Det har ar noll LLM -- rena filreads
(~<200 ms oavsett modell), injicerat som kontext. Fulla /standup finns kvar
manuellt for djupdykningar.

Innehall (~800 tokens-budget): projektets senaste session-fokus, globala
STATUS.md Open-rader, olastda wake-gate-notiser, MEMORY-halsa.

Registrerar ocksa varje session i ~/.agents/session-registry.jsonl --
auto-conclude-sweeper.py anvander raderna med telegram=1 (env TELEGRAM_SPAWNED
satt av telegram-inbound.py vid spawn).
"""

import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
VAULT = HOME / "OneDrive/Dokument/Obsidian/Knowledge Base"
REGISTRY = HOME / ".agents/session-registry.jsonl"
NOTIFY_QUEUE = HOME / ".agents/inbox/pending-notify.jsonl"
GLOBAL_STATUS = HOME / "STATUS.md"


def register(event):
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if not sid:
        return
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_id": sid,
            "cwd": event.get("cwd", "") or os.getcwd(),
            "telegram": os.environ.get("TELEGRAM_SPAWNED", "") == "1",
        }, ensure_ascii=False) + "\n")


def latest_session_focus(cwd):
    """next_session_focus ur senaste session-loggens session-state-block."""
    for base in (Path(cwd), Path(cwd) / ".."):
        logs = sorted((base / "session-logs").glob("*-session-log*.md"),
                       reverse=True) if (base / "session-logs").is_dir() else []
        if logs:
            try:
                text = logs[0].read_text(encoding="utf-8")
                m = re.search(r'next_session_focus:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
                if m:
                    return logs[0].name, m.group(1)[:300]
                return logs[0].name, None
            except Exception:
                return None, None
    return None, None


def open_elsewhere():
    try:
        text = GLOBAL_STATUS.read_text(encoding="utf-8")
    except Exception:
        return []
    out = []
    for line in text.splitlines():
        m = re.search(r"\[(\d{4}-\d{2}-\d{2})\]\s+(\S+)\s+—.*?Open:\s*(.+?)\s*(?:→|$)", line)
        if m:
            out.append(f"{m.group(2)} — {m.group(3)[:160]}")
    return out[:6]


def unread_notifies():
    try:
        lines = NOTIFY_QUEUE.read_text(encoding="utf-8").strip().splitlines()
    except Exception:
        return []
    cutoff = time.time() - 86400
    out = []
    for line in lines[-5:]:
        try:
            rec = json.loads(line)
            ts = time.mktime(time.strptime(rec["ts"][:19], "%Y-%m-%dT%H:%M:%S"))
            if ts >= cutoff:
                details = "; ".join(f["detail"] for f in rec.get("findings", [])[:3])
                line = f"score {rec.get('score')}: {details[:180]}"
                if line not in out:
                    out.append(line)
        except Exception:
            continue
    return out[-2:]


def memory_health():
    mem = VAULT / "memory/MEMORY.md"
    usr = VAULT / "memory/USER.md"
    try:
        m, u = mem.stat().st_size, usr.stat().st_size
        flags = []
        if m > 1760:
            flags.append(f"MEMORY.md {int(m/22)}% av cap")
        if u > 1100:
            flags.append(f"USER.md {int(u/13.75)}% av cap")
        return "; ".join(flags) if flags else None
    except Exception:
        return None


def main():
    if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
        return  # Fas 6 arm B

    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    register(event)

    cwd = event.get("cwd", "") or os.getcwd()
    lines = []
    log_name, focus = latest_session_focus(cwd)
    if focus:
        lines.append(f"SENASTE FOKUS ({log_name}): {focus}")
    elif log_name:
        lines.append(f"SENASTE SESSIONSLOGG: {log_name}")
    oe = open_elsewhere()
    if oe:
        lines.append("OPEN ELSEWHERE:")
        lines.extend(f"  {x}" for x in oe)
    nn = unread_notifies()
    if nn:
        lines.append("WAKE-GATE (senaste 24h):")
        lines.extend(f"  {x}" for x in nn)
    mh = memory_health()
    if mh:
        lines.append(f"MEMORY: {mh}")
    if not lines:
        return

    lines.append("(Snabb-standup, auto. Fulla /standup finns for djupladdning.)")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n".join(["<standup-brief>", *lines, "</standup-brief>"]),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
