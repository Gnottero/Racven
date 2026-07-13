from datetime import datetime

from .database import get_db

_SELECT_WITH_USER = (
    'SELECT m.id, m.body, m.created_at, u.id AS user_id, u.first_name, u.last_name, u.user_tag '
    'FROM messages m JOIN users u ON u.id = m.user_id '
)


def create_message(user_id, body):
    conn = get_db()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.execute(
        'INSERT INTO messages (user_id, body, created_at) VALUES (?, ?, ?)',
        (user_id, body, created_at),
    )
    message_id = cur.lastrowid
    conn.commit()
    row = conn.execute(_SELECT_WITH_USER + 'WHERE m.id = ?', (message_id,)).fetchone()
    conn.close()
    return row


def get_today_messages():
    conn = get_db()
    query = _SELECT_WITH_USER + "WHERE date(m.created_at) = date('now', 'localtime') ORDER BY m.created_at ASC"
    rows = conn.execute(query).fetchall()
    conn.close()
    return rows


def get_recent_messages_for_user(user_id, limit=5):
    conn = get_db()
    rows = conn.execute(
        'SELECT id, body, created_at FROM messages WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
        (user_id, limit),
    ).fetchall()
    conn.close()
    return rows


def to_dict(row):
    return {
        'id': row['id'],
        'body': row['body'],
        'created_at': row['created_at'],
        'first_name': row['first_name'],
        'last_name': row['last_name'],
        'user_tag': f"@{row['user_tag']}",
    }
