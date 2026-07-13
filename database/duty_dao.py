from .database import get_db

_SELECT_ASSIGNMENTS = (
    'SELECT a.duty_date, g.id AS duty_group_id, u.id AS user_id, u.first_name, u.last_name, u.user_tag '
    'FROM duty_assignments a '
    'JOIN duty_groups g ON g.id = a.duty_group_id '
    'JOIN duty_group_members m ON m.duty_group_id = g.id '
    'JOIN users u ON u.id = m.user_id '
)


def get_latest_version(cycle_month):
    conn = get_db()
    row = conn.execute(
        'SELECT MAX(version) AS max_version FROM duty_groups WHERE cycle_month = ?',
        (cycle_month,),
    ).fetchone()
    conn.close()
    return row['max_version'] or 0


def has_schedule(cycle_month):
    return get_latest_version(cycle_month) > 0


def get_groups_with_members(cycle_month, version):
    conn = get_db()
    query = (
        'SELECT g.id AS group_id, g.ordinal, u.id AS user_id, u.first_name, u.last_name, u.user_tag '
        'FROM duty_groups g '
        'JOIN duty_group_members m ON m.duty_group_id = g.id '
        'JOIN users u ON u.id = m.user_id '
        'WHERE g.cycle_month = ? AND g.version = ? '
        'ORDER BY g.ordinal ASC, u.id ASC'
    )
    rows = conn.execute(query, (cycle_month, version)).fetchall()
    conn.close()
    return rows


def update_group_ordinals(ordinal_by_group_id):
    conn = get_db()
    conn.executemany(
        'UPDATE duty_groups SET ordinal = ? WHERE id = ?',
        [(ordinal, group_id) for group_id, ordinal in ordinal_by_group_id.items()],
    )
    conn.commit()
    conn.close()


def insert_group(cycle_month, version, ordinal, member_ids):
    conn = get_db()
    cur = conn.execute(
        'INSERT INTO duty_groups (cycle_month, version, ordinal) VALUES (?, ?, ?)',
        (cycle_month, version, ordinal),
    )
    group_id = cur.lastrowid
    conn.executemany(
        'INSERT INTO duty_group_members (duty_group_id, user_id) VALUES (?, ?)',
        [(group_id, user_id) for user_id in member_ids],
    )
    conn.commit()
    conn.close()
    return group_id


def delete_assignments_from(cycle_month, from_date):
    conn = get_db()
    conn.execute(
        "DELETE FROM duty_assignments WHERE duty_date >= ? AND strftime('%Y-%m', duty_date) = ?",
        (from_date, cycle_month),
    )
    conn.commit()
    conn.close()


def insert_assignment(duty_date, duty_group_id):
    conn = get_db()
    conn.execute(
        'INSERT OR REPLACE INTO duty_assignments (duty_date, duty_group_id) VALUES (?, ?)',
        (duty_date, duty_group_id),
    )
    conn.commit()
    conn.close()


def get_month_assignments(cycle_month):
    conn = get_db()
    query = _SELECT_ASSIGNMENTS + "WHERE strftime('%Y-%m', a.duty_date) = ? ORDER BY a.duty_date ASC, u.id ASC"
    rows = conn.execute(query, (cycle_month,)).fetchall()
    conn.close()
    return rows


def get_assignment_for_date(duty_date):
    conn = get_db()
    query = _SELECT_ASSIGNMENTS + 'WHERE a.duty_date = ? ORDER BY u.id ASC'
    rows = conn.execute(query, (duty_date,)).fetchall()
    conn.close()
    return rows
