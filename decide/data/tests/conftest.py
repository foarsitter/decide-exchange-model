import pytest

from decide.data.database import Manager


@pytest.fixture(scope='session')
def sqlite_db():
    m = Manager('sqlite:///:memory:')
    m.init_database()
    m.create_tables()
    yield m
    m.delete_tables()

