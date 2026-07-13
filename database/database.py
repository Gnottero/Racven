import os
import sqlite3

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_PACKAGE_DIR)
SCHEMA_PATH = os.path.join(_PACKAGE_DIR, 'schema.sql')
DATABASE = os.environ.get('DATABASE_PATH') or os.path.join(_REPO_ROOT, 'database.db')


def get_db():
    conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db()
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    try:
        conn.execute('ALTER TABLE users ADD COLUMN duty_order INTEGER')
        conn.commit()
    except sqlite3.OperationalError as exc:
        if 'duplicate column' not in str(exc):
            raise
    conn.close()