from datetime import date

from database import users_dao
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
