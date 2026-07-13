import calendar
from datetime import date, timedelta
from itertools import groupby

from database import duty_dao, users_dao


def partition_into_groups(user_ids):
    """Split a deterministically-ordered list of contributor ids into fixed
    groups of 2, folding the odd one out into a triple when needed.
    Never returns a group larger than 3 (or smaller than 2, except the
    degenerate single-contributor case)."""
    ids = list(user_ids)
    n = len(ids)
    if n == 0:
        return []
    if n == 1:
        return [ids]

    pair_count = n // 2
    remainder = n % 2
    if remainder == 1:
        pair_count -= 1  # last pair becomes a triple instead

    groups = []
    i = 0
    for _ in range(pair_count):
        groups.append(ids[i:i + 2])
        i += 2
    if remainder == 1:
        groups.append(ids[i:i + 3])
        i += 3
    return groups


def _row_to_member(row):
    return {
        'id': row['user_id'],
        'first_name': row['first_name'],
        'last_name': row['last_name'],
        'user_tag': f"@{row['user_tag']}",
    }


def _assign_days(cycle_month, start_date, group_ids, start_idx=0):
    year, month = (int(part) for part in cycle_month.split('-'))
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    if start_date > end_date:
        return

    day = start_date
    idx = start_idx
    while day <= end_date:
        duty_dao.insert_assignment(day.isoformat(), group_ids[idx % len(group_ids)])
        idx += 1
        day += timedelta(days=1)


def _generate_schedule(cycle_month, start_date):
    contributor_ids = users_dao.get_contributor_ids()
    groups = partition_into_groups(contributor_ids)

    duty_dao.delete_assignments_from(cycle_month, start_date.isoformat())

    if not groups:
        return

    version = duty_dao.get_latest_version(cycle_month) + 1
    group_ids = [
        duty_dao.insert_group(cycle_month, version, ordinal, member_ids)
        for ordinal, member_ids in enumerate(groups)
    ]

    _assign_days(cycle_month, start_date, group_ids)


def ensure_month_schedule(today=None):
    """Lazily generate the current month's schedule the first time it's
    needed, avoiding any cron/scheduler dependency."""
    today = today or date.today()
    cycle_month = today.strftime('%Y-%m')
    if not duty_dao.has_schedule(cycle_month):
        _generate_schedule(cycle_month, date(today.year, today.month, 1))


def recalculate_schedule(today=None):
    """Reform groups from the current contributor set and reassign only
    today-onward days, leaving already-elapsed days untouched."""
    today = today or date.today()
    cycle_month = today.strftime('%Y-%m')
    _generate_schedule(cycle_month, today)


def get_current_groups(today=None):
    """Groups (with members) of the latest version for the current cycle
    month, ordered by their current rotation ordinal."""
    today = today or date.today()
    ensure_month_schedule(today)
    cycle_month = today.strftime('%Y-%m')
    version = duty_dao.get_latest_version(cycle_month)
    rows = duty_dao.get_groups_with_members(cycle_month, version)

    groups = []
    for group_id, group_rows in groupby(rows, key=lambda r: r['group_id']):
        group_rows = list(group_rows)
        groups.append({
            'id': group_id,
            'ordinal': group_rows[0]['ordinal'],
            'members': [_row_to_member(r) for r in group_rows],
        })
    groups.sort(key=lambda g: g['ordinal'])
    return groups


def reorder_groups(new_order_group_ids, today=None):
    """Change the rotation order of the current month's existing groups
    without touching their membership. Today's already-assigned duty is
    left untouched; the round robin for tomorrow onward resumes right
    after today's group in the new order, so every group still gets a
    turn before any of them repeats."""
    today = today or date.today()
    cycle_month = today.strftime('%Y-%m')

    duty_dao.update_group_ordinals(
        {group_id: idx for idx, group_id in enumerate(new_order_group_ids)}
    )

    today_rows = duty_dao.get_assignment_for_date(today.isoformat())
    if today_rows and today_rows[0]['duty_group_id'] in new_order_group_ids:
        current_idx = new_order_group_ids.index(today_rows[0]['duty_group_id'])
        start_idx = (current_idx + 1) % len(new_order_group_ids)
    else:
        start_idx = 0

    tomorrow = today + timedelta(days=1)
    duty_dao.delete_assignments_from(cycle_month, tomorrow.isoformat())
    _assign_days(cycle_month, tomorrow, new_order_group_ids, start_idx=start_idx)


def get_today_duty(today=None):
    today = today or date.today()
    ensure_month_schedule(today)
    rows = duty_dao.get_assignment_for_date(today.isoformat())
    return {
        'date': today.isoformat(),
        'members': [_row_to_member(row) for row in rows],
    }


def get_month_schedule(today=None):
    today = today or date.today()
    ensure_month_schedule(today)
    cycle_month = today.strftime('%Y-%m')
    rows = duty_dao.get_month_assignments(cycle_month)

    days = []
    for duty_date, day_rows in groupby(rows, key=lambda r: r['duty_date']):
        members = [_row_to_member(row) for row in day_rows]
        day_obj = date.fromisoformat(duty_date)
        days.append({
            'date': duty_date,
            'members': members,
            'is_today': duty_date == today.isoformat(),
            'is_past': day_obj < today,
            'weekday': day_obj.weekday(),
        })
    return {
        'cycle_month': cycle_month,
        'days': days,
    }
