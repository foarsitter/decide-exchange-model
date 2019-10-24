from decide.data import database as db


def test_eq():
    """
    Shows the possibility of the hash/dictionary key implement
    """
    store = {}

    data_set = db.DataSet(name="pizza")
    store[data_set] = data_set

    assert store["pizza"] == data_set

    iteration = db.Iteration()
    iteration.pointer = 1

    iteration2 = db.Iteration()
    iteration2.pointer = 2

    iteration3 = db.Iteration()
    iteration3.pointer = 1

    store[iteration3] = iteration3

    assert iteration2 != iteration
    assert iteration3 == iteration
    assert store[iteration3] == iteration
    assert store[1] == iteration


def test_database(sqlite_db):
    created = db.DataSet.create(name="test123")

    data_set = db.DataSet.get(name="test123")

    assert data_set == created


def test_exchange_database():
    db.connection.drop_tables([db.ExchangeActor, db.Exchange])
    db.connection.create_tables([db.ExchangeActor, db.Exchange])
