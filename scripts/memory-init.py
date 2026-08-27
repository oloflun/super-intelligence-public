#!/usr/bin/env python3
"""
Initialize memory files from templates.
Creates MEMORY.md, USER.md, MEMORY-FULL.md, USER-FULL.md, and sessions.db
in the vault memory directory.

Usage: python3 memory-init.py --vault <path> [--force]
"""
import argparse, sqlite3, sys
from datetime import date
from pathlib import Path

MEMORY_TEMPLATES = {
    "MEMORY.md": """# Agent Memory (Hot)
_Cap: 2 200 chars. Loaded every standup. Write only at /conclude._

## Active Constraints
_(no constraints yet — add via /conclude)_

## Environment Facts
- [{date}] System initialized via super-intelligence installer.

## Open Threads
_(none)_
""",
    "USER.md": """# User Profile (Hot)
_Cap: 1 375 chars. Loaded every standup. Write only at /conclude._

## Preferences
_(none yet — add via /conclude as preferences are discovered)_

## Active Projects
_(none yet)_
""",
    "MEMORY-FULL.md": """# Memory (Warm — Episodic)
_Unbounded. Loaded on demand via /recall._

## System Initialization — {date}
- Super-intelligence agent stack installed.
""",
    "USER-FULL.md": """# User Profile (Warm — Full History)
_Unbounded. Loaded on demand._
""",
}

SESSIONS_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    cwd TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    summary TEXT NOT NULL,
    log_path TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    id, agent, summary,
    content='sessions', content_rowid='rowid'
);
CREATE TRIGGER IF NOT EXISTS sessions_ai AFTER INSERT ON sessions BEGIN
    INSERT INTO sessions_fts(rowid, id, agent, summary)
    VALUES (new.rowid, new.id, new.agent, new.summary);
END;
CREATE TRIGGER IF NOT EXISTS sessions_ad AFTER DELETE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, id, agent, summary)
    VALUES ('delete', old.rowid, old.id, old.agent, old.summary);
END;
CREATE TRIGGER IF NOT EXISTS sessions_au AFTER UPDATE ON sessions BEGIN
    INSERT INTO sessions_fts(sessions_fts, rowid, id, agent, summary)
    VALUES ('delete', old.rowid, old.id, old.agent, old.summary);
    INSERT INTO sessions_fts(rowid, id, agent, summary)
    VALUES (new.rowid, new.id, new.agent, new.summary);
END;
"""

def main():
    parser = argparse.ArgumentParser(description="Initialize memory system")
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    vault = Path(args.vault)
    memdir = vault / "memory"
    memdir.mkdir(parents=True, exist_ok=True)
    (memdir / "archive").mkdir(exist_ok=True)

    today = date.today().isoformat()
    created = []
    skipped = []

    for filename, template in MEMORY_TEMPLATES.items():
        fpath = memdir / filename
        if fpath.exists() and not args.force:
            skipped.append(filename)
            continue
        content = template.format(date=today)
        fpath.write_text(content, encoding="utf-8")
        created.append(filename)

    # sessions.db
    dbpath = memdir / "sessions.db"
    if dbpath.exists() and not args.force:
        skipped.append("sessions.db")
    else:
        conn = sqlite3.connect(str(dbpath))
        conn.executescript(SESSIONS_SQL)
        conn.commit()
        conn.close()
        created.append("sessions.db")

    if created:
        print(f"Created: {', '.join(created)}")
    if skipped:
        print(f"Skipped (exists): {', '.join(skipped)}")

    print(f"\nMemory system initialized in {memdir}")

if __name__ == "__main__":
    main()
