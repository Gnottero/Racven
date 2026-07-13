from database import messages_dao, users_dao
from tests.conftest import login_as


def _make_user(n, role='participant'):
    return users_dao.create_user(
        f'Nome{n}', f'Cognome{n}', f'tag{n}', 'hash', role=role, contributor=True
    )


def test_delete_message_forbidden_for_non_owner_non_admin(client, temp_db):
    owner_id = _make_user(1)
    other_id = _make_user(2)
    row = messages_dao.create_message(owner_id, 'ciao')

    login_as(client, other_id)
    response = client.post(
        f"/messages/{row['id']}/delete", data={'csrf_token': 'test-token'}
    )

    assert response.status_code == 403
    assert messages_dao.get_message_by_id(row['id']) is not None


def test_delete_message_not_found(client, temp_db):
    user_id = _make_user(1)

    login_as(client, user_id)
    response = client.post('/messages/999/delete', data={'csrf_token': 'test-token'})

    assert response.status_code == 404


def test_delete_message_allowed_for_owner(client, temp_db):
    owner_id = _make_user(1)
    row = messages_dao.create_message(owner_id, 'ciao')

    login_as(client, owner_id)
    response = client.post(
        f"/messages/{row['id']}/delete", data={'csrf_token': 'test-token'}
    )

    assert response.status_code == 302
    assert messages_dao.get_message_by_id(row['id']) is None


def test_delete_message_allowed_for_admin(client, temp_db):
    owner_id = _make_user(1)
    admin_id = _make_user(2, role='admin')
    row = messages_dao.create_message(owner_id, 'ciao')

    login_as(client, admin_id)
    response = client.post(
        f"/messages/{row['id']}/delete", data={'csrf_token': 'test-token'}
    )

    assert response.status_code == 302
    assert messages_dao.get_message_by_id(row['id']) is None
