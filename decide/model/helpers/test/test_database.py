import logging
import os
from unittest import TestCase

from decide.model.equalgain import EqualGainModel
from decide.model.helpers import csvparser
from decide.model.helpers import database as db
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver


class BaseDatabaseTestCase(TestCase):
    def setUp(self):
        logging.info("setup")
        # Bind model classes to test db. Since we have a complete list of
        # all models, we do not need to recursively bind dependencies.

        csv = csvparser.CsvParser(EqualGainModel())

        path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../../../../data/input/sample_data.txt",
        )
        self.model = csv.read(path)
        self.model.randomized_value = 0.10

        self.event_handler = Observable(model_ref=self.model, output_directory="")
        self.observer = SQLiteObserver(self.event_handler, output_directory=":memory:")


class TestHashFunctions(BaseDatabaseTestCase):
    def test_eq(self):
        """
        Shows the possibility of the hash/dictionary key implement
        """
        store = {}

        data_set = db.DataSet(name="pizza")
        store[data_set] = data_set
        self.assertEqual(store["pizza"], data_set)

        iteration = db.Iteration()
        iteration.pointer = 1

        iteration2 = db.Iteration()
        iteration2.pointer = 2

        iteration3 = db.Iteration()
        iteration3.pointer = 1

        store[iteration3] = iteration3

        self.assertNotEqual(iteration2, iteration)

        self.assertEqual(iteration3, iteration)

        self.assertEqual(store[iteration3], iteration)

        self.assertEqual(store[1], iteration)

    def test_database(self):
        created = db.DataSet.create(name="test123")

        data_set = db.DataSet.get(name="test123")

        self.assertEqual(data_set, created)

    def test_data_model(self):

        self.observer.before_repetitions(repetitions=1, iterations=1)  # TODO FIX
        self.observer.before_iterations(1)
        self.observer.before_loop(0, 1)

        # compare the ActorIssues against the database results
        actor_issue_count = sum([len(x) for x in self.model.actor_issues.values()])
        self.assertEqual(db.ActorIssue.select().count(), actor_issue_count)

        # the after_loop events captures again all the actor issues, so the amount of actorIssues is 2 times that high
        self.observer.end_loop(0, 1)
        self.assertEqual(db.ActorIssue.select().count(), actor_issue_count * 2)

    def test_exchange_database(self):
        db.connection.drop_tables([db.ExchangeActor, db.Exchange])
        db.connection.create_tables([db.ExchangeActor, db.Exchange])
