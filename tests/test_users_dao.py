from database import users_dao


def _make_user(n):
    return users_dao.create_user(
        f'Nome{n}', f'Cognome{n}', f'tag{n}', 'hash', role='participant', contributor=True
    )


def test_get_contributor_ids_defaults_to_id_order(temp_db):
    ids = [_make_user(i) for i in range(3)]

    assert users_dao.get_contributor_ids() == ids


def test_set_contributor_order_overrides_id_order(temp_db):
    ids = [_make_user(i) for i in range(3)]
    reversed_ids = list(reversed(ids))

    users_dao.set_contributor_order(reversed_ids)

    assert users_dao.get_contributor_ids() == reversed_ids


def test_new_contributor_without_duty_order_sorts_last(temp_db):
    ids = [_make_user(i) for i in range(2)]
    users_dao.set_contributor_order(list(reversed(ids)))

    new_id = _make_user(2)

    assert users_dao.get_contributor_ids() == list(reversed(ids)) + [new_id]


def test_get_contributors_ordered_matches_get_contributor_ids(temp_db):
    ids = [_make_user(i) for i in range(3)]
    users_dao.set_contributor_order(list(reversed(ids)))

    ordered_rows = users_dao.get_contributors_ordered()

    assert [row['id'] for row in ordered_rows] == users_dao.get_contributor_ids()
