from unittest import TestCase

from model.base import AbstractExchangeActor, AbstractModel, Actor


class TestAbstractExchangeActor(TestCase):
    def test___eq__(self):
        model = AbstractModel()

        model.add_issue("test")
        model.add_issue("test1")

        model.add_actor_issue("test", "test", 100, 1, 1)
        model.add_actor_issue("test", "test1", 100, 1, 1)
        model.add_actor_issue("test1", "test", 100, 1, 1)
        model.add_actor_issue("test1", "test1", 100, 1, 1)

        exchange_actor0 = AbstractExchangeActor(model=model, actor_name="test", demand="test", supply="test1", group=['a', 'd'])
        exchange_actor1 = AbstractExchangeActor(model=model, actor_name="test1", demand="test1", supply="test", group=['a', 'd'])

        exchange_actor4 = AbstractExchangeActor(model=model, actor_name="test", demand="test", supply="test1", group=['a', 'd'])

        self.assertTrue(exchange_actor0 == exchange_actor0)
        self.assertTrue(exchange_actor0 == exchange_actor4)
        self.assertTrue(exchange_actor0 != exchange_actor1)

        self.assertTrue(exchange_actor0.equals_supply_issue(exchange_actor4))
        self.assertTrue(exchange_actor0.equals_demand_issue(exchange_actor4))

        self.assertTrue(exchange_actor0.equals_demand_issue_str(actor_name=exchange_actor4.actor_name, demand_issue=exchange_actor4.demand_issue))
        self.assertTrue(exchange_actor0.equals_supply_issue_str(actor_name=exchange_actor4.actor_name, supply_issue=exchange_actor4.supply_issue))

        self.assertFalse(exchange_actor0.equals_supply_issue(exchange_actor1))
        self.assertFalse(exchange_actor4.equals_supply_issue(exchange_actor1))

