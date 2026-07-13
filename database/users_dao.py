from .database import get_db


def get_user_by_tag(user_tag):
    conn = get_db()
    query = 'SELECT * FROM users WHERE user_tag = ?'
    row = conn.execute(query, (user_tag,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_db()
    query = 'SELECT * FROM users WHERE id = ?'
    row = conn.execute(query, (user_id,)).fetchone()
    conn.close()
    return row


def user_tag_exists(user_tag):
    return get_user_by_tag(user_tag) is not None


def create_user(first_name, last_name, user_tag, password_hash, role='participant', contributor=True):
    conn = get_db()
    query = (
        'INSERT INTO users (first_name, last_name, user_tag, password_hash, role, contributor) '
        'VALUES (?, ?, ?, ?, ?, ?)'
    )
    cur = conn.execute(
        query, (first_name, last_name, user_tag, password_hash, role, int(contributor))
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_all_users():
    conn = get_db()
    rows = conn.execute('SELECT * FROM users ORDER BY id').fetchall()
    conn.close()
    return rows


def set_contributor(user_id, contributor):
    conn = get_db()
    conn.execute(
        'UPDATE users SET contributor = ? WHERE id = ?', (int(contributor), user_id)
    )
    conn.commit()
    conn.close()


def get_contributor_ids():
    conn = get_db()
    rows = conn.execute(
        'SELECT id FROM users WHERE contributor = 1 ORDER BY id'
    ).fetchall()
    conn.close()
    return [row['id'] for row in rows]


def delete_user(user_id):
    conn = get_db()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
