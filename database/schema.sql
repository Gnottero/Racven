CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    user_tag      TEXT NOT NULL UNIQUE,      -- salvato SENZA '@' iniziale
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'participant' CHECK (role IN ('participant', 'admin')),
    contributor   INTEGER NOT NULL DEFAULT 1 CHECK (contributor IN (0, 1)),
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- una riga per ogni "versione" della partizione in coppie/terne generata per un dato mese
CREATE TABLE IF NOT EXISTS duty_groups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_month TEXT NOT NULL,   -- 'YYYY-MM'
    version     INTEGER NOT NULL,
    ordinal     INTEGER NOT NULL -- posizione nella rotazione, 0-based
);
CREATE INDEX IF NOT EXISTS idx_duty_groups_month ON duty_groups(cycle_month);

CREATE TABLE IF NOT EXISTS duty_group_members (
    duty_group_id INTEGER NOT NULL REFERENCES duty_groups(id) ON DELETE CASCADE,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (duty_group_id, user_id)
);

CREATE TABLE IF NOT EXISTS duty_assignments (
    duty_date     TEXT PRIMARY KEY,   -- 'YYYY-MM-DD'
    duty_group_id INTEGER NOT NULL REFERENCES duty_groups(id) ON DELETE CASCADE
);
