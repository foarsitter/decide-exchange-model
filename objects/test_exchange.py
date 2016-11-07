from unittest import TestCase

from objects.Exchange import Exchange
from objects.Model import Model


class TestExchange(TestCase):
    def test_init(self):
        model = Model()

        a1 = model.add_actor("a1")
        a2 = model.add_actor("a2")
        a3 = model.add_actor("a3")

        model.add_issue("p", "P")
        model.add_issue("q", "Q")

        model.add_actor_issue(a1, "p", 70, 0.75, 0.5)
        model.add_actor_issue(a2, "p", 30, 0.25, 0.5)
        model.add_actor_issue(a3, "p", 30, 0.25, 0.5)

        model.add_actor_issue(a1, "q", 70, 0.25, 0.5)
        model.add_actor_issue(a2, "q", 30, 0.75, 0.5)
        model.add_actor_issue(a3, "q", 30, 0.75, 0.5)

        model.calc_nbs()

        e = Exchange(a1, a2, "p", "q", model, groups=['a', 'b'])
        e.calculate()

        e2 = Exchange(a1, a2, "p", "q", model, groups=['a', 'd'])

        e2.updates["p"]["a3"] = 100
        e2.calculate()
        # TODO: fix this test
        # self.assertEqual(e2.j.move, 10)

class TestExchangeActor(TestCase):
    def test_equals(self):
        model = Model()

        a1 = model.add_actor("a1")
        a2 = model.add_actor("a2")
        a3 = model.add_actor("a3")

        model.add_issue("p", "P")
        model.add_issue("q", "Q")

        model.add_actor_issue(a1, "p", 70, 0.75, 0.5)
        model.add_actor_issue(a2, "p", 30, 0.25, 0.5)
        model.add_actor_issue(a3, "p", 30, 0.25, 0.5)

        model.add_actor_issue(a1, "q", 70, 0.25, 0.5)
        model.add_actor_issue(a2, "q", 30, 0.75, 0.5)
        model.add_actor_issue(a3, "q", 30, 0.75, 0.5)

        model.calc_nbs()

        e = Exchange(a1, a2, "p", "q", model, groups=['a', 'b'])

        eq = e.equal_str("a1", "a2", "p", "q")

        self.assertTrue(eq)
