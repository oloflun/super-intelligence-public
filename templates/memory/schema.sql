-- Super-Intelligence Agent Stack — sessions.db schema
-- SQLite FTS5 full-text search for session history

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,          -- YYYYMMDD-<project-slug>
    agent TEXT NOT NULL,          -- claude | codex | gemini | hermes
    cwd TEXT NOT NULL,            -- absolute project path
    timestamp TEXT NOT NULL,      -- ISO 8601
    summary TEXT NOT NULL,        -- 2-3 sentence session summary
    log_path TEXT NOT NULL        -- absolute path to session log
);

CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    id,
    agent,
    summary,
    content='sessions',
    content_rowid='rowid'
);

-- Triggers to keep FTS index in sync
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

-- Example query:
-- SELECT * FROM sessions_fts WHERE sessions_fts MATCH 'claude api integration' ORDER BY rank;
