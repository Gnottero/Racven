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

    last_day = calendar.monthrange(start_date.year, start_date.month)[1]
    end_date = date(start_date.year, start_date.month, last_day)

    day = start_date
    idx = 0
    while day <= end_date:
        duty_dao.insert_assignment(day.isoformat(), group_ids[idx % len(group_ids)])
        idx += 1
        day += timedelta(days=1)


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
