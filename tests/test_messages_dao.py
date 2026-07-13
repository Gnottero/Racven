from database import messages_dao, users_dao


def _make_user(n, role='participant'):
    return users_dao.create_user(
        f'Nome{n}', f'Cognome{n}', f'tag{n}', 'hash', role=role, contributor=True
    )


def test_get_recent_messages_for_user_returns_only_own_messages(temp_db):
    user_id = _make_user(1)
    other_id = _make_user(2)
    messages_dao.create_message(user_id, 'ciao')
    messages_dao.create_message(other_id, 'salve')

    rows = messages_dao.get_recent_messages_for_user(user_id)

    assert len(rows) == 1
    assert rows[0]['body'] == 'ciao'
    assert rows[0]['user_id'] == user_id
    assert rows[0]['user_tag'] == 'tag1'


def test_get_all_messages_returns_every_user(temp_db):
    user_id = _make_user(1)
    other_id = _make_user(2)
    messages_dao.create_message(user_id, 'ciao')
    messages_dao.create_message(other_id, 'salve')

    rows = messages_dao.get_all_messages()

    assert len(rows) == 2
    assert {row['user_id'] for row in rows} == {user_id, other_id}


def test_get_message_by_id_returns_none_when_missing(temp_db):
    assert messages_dao.get_message_by_id(999) is None


def test_delete_message_removes_row(temp_db):
    user_id = _make_user(1)
    row = messages_dao.create_message(user_id, 'ciao')

    messages_dao.delete_message(row['id'])

    assert messages_dao.get_message_by_id(row['id']) is None
    assert messages_dao.get_all_messages() == []
