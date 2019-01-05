from unittest import TestCase

from decide.model.equalgain import EqualGainModel, EqualGainExchange


class TestExchange(TestCase):
    def test_init(self):
        model = EqualGainModel()

        a1 = model.add_actor("a1")
        a2 = model.add_actor("a2")
        a3 = model.add_actor("a3")
        a4 = model.add_actor("a4")

        model.add_issue("p")
        model.add_issue("q")

        model.add_actor_issue(a1, "p", 70, 0.75, 0.5)
        model.add_actor_issue(a2, "p", 30, 0.25, 0.5)
        model.add_actor_issue(a3, "p", 30, 0.25, 0.5)
        model.add_actor_issue(a4, "p", 0, 0.6, 0.85)

        model.add_actor_issue(a1, "q", 70, 0.25, 0.5)
        model.add_actor_issue(a2, "q", 30, 0.75, 0.5)
        model.add_actor_issue(a3, "q", 30, 0.75, 0.5)
        model.add_actor_issue(a4, "q", 100, 0.8, 0.85)

        model.calc_nbs()

        e = EqualGainExchange(a1, a2, "p", "q", model, groups=["a", "d"])
        e.calculate()

        e2 = EqualGainExchange(a1, a2, "p", "q", model, groups=["a", "d"])

        e2.updates["p"]["a3"] = 100
        e2.calculate()

        e3 = EqualGainExchange(a1, a3, "p", "q", model, groups=["a", "d"])
        e3.calculate()
