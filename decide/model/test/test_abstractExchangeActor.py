from unittest import TestCase

from decide.model.base import AbstractExchangeActor, AbstractModel, Issue


class TestAbstractExchangeActor(TestCase):
    def test___eq__(self):
        model = AbstractModel()

        test_issue = model.add_issue("test")
        test1_issue = model.add_issue("test1")

        test_actor = model.add_actor("test")
        test1_actor = model.add_actor("test1")
        test1_issue_duplicated = model.add_issue("test")
        test1_actor_duplicated = model.add_actor("test1")

        self.assertEqual(test_actor, test_actor)
        self.assertNotEqual(test_actor, test1_actor)

        self.assertEqual(test_actor.__hash__(), hash(test_actor.actor_id))
        self.assertEqual(test1_actor_duplicated, test1_actor)

        self.assertTrue(test_actor in model.actors)
        self.assertTrue(test_issue in model.issues)

        b = Issue("test")
        b.name = "test"

        self.assertEqual(b.__hash__(), test_issue.__hash__())

        self.assertTrue(b in model.issues)

        self.assertEqual(test1_issue_duplicated, test_issue)
        self.assertEqual(test_issue.__hash__(), hash(test_issue.issue_id))
        self.assertEqual(test_issue.__hash__(), hash("test"))
        self.assertEqual(test_issue.__hash__(), hash(test1_issue_duplicated.issue_id))

        self.assertTrue(test_actor in model.actors)
        ai1 = model.add_actor_issue("test", "test", 100, 1, 1)
        ai2 = model.add_actor_issue("test", "test1", 100, 1, 1)
        ai3 = model.add_actor_issue("test1", "test", 100, 1, 1)
        ai4 = model.add_actor_issue("test1", "test1", 100, 1, 1)

        exchange_actor0 = AbstractExchangeActor(
            model=model,
            actor=test_actor,
            demand_issue=test_issue,
            supply_issue=test1_issue,
            exchange=None,
        )

        exchange_actor1 = AbstractExchangeActor(
            model=model,
            actor=test1_actor,
            demand_issue=test1_issue,
            supply_issue=test_issue,
            exchange=None,
        )

        exchange_actor4 = AbstractExchangeActor(
            model=model,
            actor=test_actor,
            demand_issue=test_issue,
            supply_issue=test1_issue,
            exchange=None,
        )

        self.assertTrue(exchange_actor0 == exchange_actor0)
        self.assertTrue(exchange_actor0 == exchange_actor4)
        self.assertTrue(exchange_actor0 != exchange_actor1)

        self.assertTrue(exchange_actor0.equals_supply_issue(exchange_actor4))
        self.assertTrue(exchange_actor0.equals_demand_issue(exchange_actor4))

        self.assertFalse(exchange_actor0.equals_supply_issue(exchange_actor1))
        self.assertFalse(exchange_actor4.equals_supply_issue(exchange_actor1))
