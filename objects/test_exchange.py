from unittest import TestCase

from objects.Exchange import Exchange
from objects.Model import Model


class TestExchange(TestCase):
    def test_init(self):
        model = Model()

        a1 = model.add_actor("a1")
        a2 = model.add_actor("a2")

        model.add_issue("p", "P")
        model.add_issue("q", "Q")

        model.add_actor_issue(a1.Name, "p", 70, 0.5, 0.5)
        model.add_actor_issue(a2.Name, "p", 30, 0.5, 0.5)

        model.add_actor_issue(a1.Name, "q", 70, 0.5, 0.5)
        model.add_actor_issue(a2.Name, "q", 30, 0.5, 0.5)

        e = Exchange(a1, a2, "p", "q", model)
