from database import users_dao
from services import duty_service
from tests.conftest import login_as


def _make_user(n, role='participant', contributor=True):
    return users_dao.create_user(
        f'Nome{n}', f'Cognome{n}', f'tag{n}', 'hash', role=role, contributor=contributor
    )


def _make_admin(n):
    return _make_user(n, role='admin', contributor=False)


def test_duty_routes_forbidden_for_non_admin(client, temp_db):
    user_id = _make_user(1)
    login_as(client, user_id)

    assert client.get('/admin/duty').status_code == 403
    assert client.post(
        f'/admin/duty/contributors/{user_id}/move',
        data={'csrf_token': 'test-token', 'direction': 'up'},
    ).status_code == 403
    assert client.post(
        '/admin/duty/recalculate', data={'csrf_token': 'test-token'}
    ).status_code == 403
    assert client.post(
        '/admin/duty/groups/1/move',
        data={'csrf_token': 'test-token', 'direction': 'up'},
    ).status_code == 403


def test_move_contributor_up_swaps_order(client, temp_db):
    admin_id = _make_admin(1)
    ids = [_make_user(i) for i in range(2, 5)]  # 3 contributors, ascending order

    login_as(client, admin_id)
    resp = client.post(
        f'/admin/duty/contributors/{ids[2]}/move',
        data={'csrf_token': 'test-token', 'direction': 'up'},
    )

    assert resp.status_code == 302
    assert users_dao.get_contributor_ids() == [ids[0], ids[2], ids[1]]


def test_move_contributor_at_top_boundary_is_noop(client, temp_db):
    admin_id = _make_admin(1)
    ids = [_make_user(i) for i in range(2, 4)]

    login_as(client, admin_id)
    resp = client.post(
        f'/admin/duty/contributors/{ids[0]}/move',
        data={'csrf_token': 'test-token', 'direction': 'up'},
    )

    assert resp.status_code == 302
    assert users_dao.get_contributor_ids() == ids


def test_recalculate_duty_applies_contributor_order(client, temp_db):
    admin_id = _make_admin(1)
    ids = [_make_user(i) for i in range(2, 6)]  # 4 contributors -> 2 pairs
    users_dao.set_contributor_order(list(reversed(ids)))

    login_as(client, admin_id)
    resp = client.post('/admin/duty/recalculate', data={'csrf_token': 'test-token'})

    assert resp.status_code == 302
    groups = duty_service.get_current_groups()
    member_ids = [{m['id'] for m in g['members']} for g in groups]
    assert {ids[3], ids[2]} in member_ids
    assert {ids[1], ids[0]} in member_ids


def test_move_duty_group_stale_group_id_flashes_instead_of_crashing(client, temp_db):
    admin_id = _make_admin(1)

    login_as(client, admin_id)
    resp = client.post(
        '/admin/duty/groups/999999/move',
        data={'csrf_token': 'test-token', 'direction': 'up'},
    )

    assert resp.status_code == 302
