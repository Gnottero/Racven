from datetime import date

from database import duty_dao, users_dao
from services import duty_service


def _make_contributor(n):
    return users_dao.create_user(
        f'Nome{n}', f'Cognome{n}', f'tag{n}', 'hash', role='participant', contributor=True
    )


def test_recalculate_schedule_does_not_touch_past_days(temp_db):
    today = date(2026, 7, 15)
    for i in range(4):
        _make_contributor(i)

    duty_service.ensure_month_schedule(today)
    before = duty_service.get_month_schedule(today)
    past_days_before = {d['date']: d['members'] for d in before['days'] if d['date'] < today.isoformat()}

    assert past_days_before, 'il test presuppone che esistano giorni passati nel mese generato'

    users_dao.set_contributor(1, False)
    duty_service.recalculate_schedule(today)

    after = duty_service.get_month_schedule(today)
    past_days_after = {d['date']: d['members'] for d in after['days'] if d['date'] < today.isoformat()}

    assert past_days_after == past_days_before, (
        'recalculate_schedule ha modificato assegnazioni di giorni passati'
    )


def test_reorder_groups_keeps_membership_and_todays_assignment(temp_db):
    today = date(2026, 7, 15)
    for i in range(4):
        _make_contributor(i)

    duty_service.ensure_month_schedule(today)
    groups_before = duty_service.get_current_groups(today)
    members_before = {g['id']: {m['id'] for m in g['members']} for g in groups_before}
    today_assignment_before = {row['user_id'] for row in duty_dao.get_assignment_for_date(today.isoformat())}

    new_order = [g['id'] for g in reversed(groups_before)]
    duty_service.reorder_groups(new_order, today)

    groups_after = duty_service.get_current_groups(today)
    members_after = {g['id']: {m['id'] for m in g['members']} for g in groups_after}
    today_assignment_after = {row['user_id'] for row in duty_dao.get_assignment_for_date(today.isoformat())}

    assert members_after == members_before, 'reorder_groups non deve alterare la composizione dei gruppi'
    assert today_assignment_after == today_assignment_before, 'reorder_groups non deve alterare il turno di oggi'
    assert [g['id'] for g in groups_after] == new_order


def test_reorder_groups_updates_future_days_and_preserves_past(temp_db):
    today = date(2026, 7, 15)
    for i in range(6):  # 3 groups: with only 2 groups, preserving today's
        _make_contributor(i)  # assignment leaves only one possible "next" day.

    duty_service.ensure_month_schedule(today)
    before = duty_service.get_month_schedule(today)
    past_before = {d['date']: d['members'] for d in before['days'] if d['date'] < today.isoformat()}
    future_before = {
        d['date']: {m['id'] for m in d['members']}
        for d in before['days'] if d['date'] > today.isoformat()
    }

    groups = duty_service.get_current_groups(today)
    new_order = [g['id'] for g in reversed(groups)]
    duty_service.reorder_groups(new_order, today)

    after = duty_service.get_month_schedule(today)
    past_after = {d['date']: d['members'] for d in after['days'] if d['date'] < today.isoformat()}
    future_after = {
        d['date']: {m['id'] for m in d['members']}
        for d in after['days'] if d['date'] > today.isoformat()
    }

    assert past_after == past_before, 'reorder_groups non deve alterare i giorni passati'
    assert future_after != future_before, 'reorder_groups deve aggiornare i giorni futuri con il nuovo ordine'


def test_get_current_groups_shape(temp_db):
    today = date(2026, 7, 15)
    for i in range(4):
        _make_contributor(i)

    duty_service.ensure_month_schedule(today)
    groups = duty_service.get_current_groups(today)

    assert len(groups) == 2
    assert [g['ordinal'] for g in groups] == [0, 1]
    for g in groups:
        assert len(g['members']) == 2
        assert set(g['members'][0].keys()) == {'id', 'first_name', 'last_name', 'user_tag'}


def test_recalculate_schedule_updates_future_days(temp_db):
    today = date(2026, 7, 15)
    ids = [_make_contributor(i) for i in range(4)]

    duty_service.ensure_month_schedule(today)
    before = duty_service.get_month_schedule(today)
    future_before = {d['date']: d['members'] for d in before['days'] if d['date'] >= today.isoformat()}

    users_dao.set_contributor(ids[0], False)
    duty_service.recalculate_schedule(today)

    after = duty_service.get_month_schedule(today)
    future_after = {d['date']: d['members'] for d in after['days'] if d['date'] >= today.isoformat()}

    assert future_after != future_before, (
        'recalculate_schedule non ha aggiornato i giorni da oggi in poi dopo un cambio di contributori'
    )
