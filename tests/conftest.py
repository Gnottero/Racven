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
