import os
import sqlite3
import tempfile

from database import database as db_module


def test_init_db_is_idempotent_and_adds_duty_order(temp_db):
    db_module.init_db()  # temp_db fixture already called it once; call again

    conn = db_module.get_db()
    columns = {row['name'] for row in conn.execute('PRAGMA table_info(users)')}
    conn.close()

    assert 'duty_order' in columns


def test_init_db_migrates_pre_existing_users_table_without_duty_order(monkeypatch):
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        conn = sqlite3.connect(path)
        conn.execute(
            'CREATE TABLE users ('
            'id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL, '
            'last_name TEXT NOT NULL, user_tag TEXT NOT NULL UNIQUE, '
            'password_hash TEXT NOT NULL, '
            "role TEXT NOT NULL DEFAULT 'participant', "
            'contributor INTEGER NOT NULL DEFAULT 1, '
            "created_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        conn.execute(
            "INSERT INTO users (first_name, last_name, user_tag, password_hash) "
            "VALUES ('Mario', 'Rossi', 'mario', 'hash')"
        )
        conn.commit()
        conn.close()

        monkeypatch.setattr(db_module, 'DATABASE', path)
        db_module.init_db()

        conn = db_module.get_db()
        columns = {row['name'] for row in conn.execute('PRAGMA table_info(users)')}
        row = conn.execute("SELECT * FROM users WHERE user_tag = 'mario'").fetchone()
        conn.close()

        assert 'duty_order' in columns
        assert row['first_name'] == 'Mario'
        assert row['duty_order'] is None
    finally:
        os.remove(path)
