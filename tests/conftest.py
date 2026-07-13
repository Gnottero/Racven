import os
import tempfile

import pytest

from database import database as db_module


@pytest.fixture
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    monkeypatch.setattr(db_module, 'DATABASE', path)
    db_module.init_db()
    yield path
    os.remove(path)


@pytest.fixture
def client(temp_db):
    from racven import app as flask_app

    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


def login_as(client, user_id):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['csrf_token'] = 'test-token'
