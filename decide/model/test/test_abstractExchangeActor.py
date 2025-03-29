from unittest import TestCase

from decide.model.base import AbstractExchangeActor
from decide.model.base import AbstractModel
from decide.model.base import Issue


class TestAbstractExchangeActor(TestCase):
    def test___eq__(self) -> None:
        model = AbstractModel()

        test_issue = model.add_issue("test")
        test1_issue = model.add_issue("test1")

        test_issue.lower = 0
        test_issue.upper = 100
        test_issue.calculate_step_size()

        test1_issue.lower = 0
        test1_issue.upper = 100
        test1_issue.calculate_step_size()

        test_actor = model.add_actor("test")
        test1_actor = model.add_actor("test1")
        test1_issue_duplicated = model.add_issue("test")
        test1_actor_duplicated = model.add_actor("test1")

        test1_issue_duplicated.lower = 0
        test1_issue_duplicated.upper = 100

        assert test_actor == test_actor
        assert test_actor != test1_actor

        assert test_actor.__hash__() == hash(test_actor.actor_id)
        assert test1_actor_duplicated == test1_actor

        assert test_actor in model.actors
        assert test_issue in model.issues

        b = Issue("test")
        b.name = "test"
        b.lower = 0
        b.upper = 100
        b.calculate_step_size()

        assert b.__hash__() == test_issue.__hash__()

        assert b in model.issues

        assert test1_issue_duplicated == test_issue
        assert test_issue.__hash__() == hash(test_issue.issue_id)
        assert test_issue.__hash__() == hash("test")
        assert test_issue.__hash__() == hash(test1_issue_duplicated.issue_id)

        assert test_actor in model.actors
        model.add_actor_issue("test", "test", 100, 1, 1)
        model.add_actor_issue("test", "test1", 100, 1, 1)
        model.add_actor_issue("test1", "test", 100, 1, 1)
        model.add_actor_issue("test1", "test1", 100, 1, 1)

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

        assert exchange_actor0 == exchange_actor0
        assert exchange_actor0 == exchange_actor4
        assert exchange_actor0 != exchange_actor1

        assert exchange_actor0.equals_supply_issue(exchange_actor4)
        assert exchange_actor0.equals_demand_issue(exchange_actor4)

        assert not exchange_actor0.equals_supply_issue(exchange_actor1)
        assert not exchange_actor4.equals_supply_issue(exchange_actor1)
