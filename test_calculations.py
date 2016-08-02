from unittest import TestCase

import csvParser
from calculations import by_exchange_ratio, by_absolute_move, calc_adjusted_nbs, calc_nbs, reverse_move, \
    sum_salience_power
from objects.Actor import Actor
from objects.ActorIssue import ActorIssue
from objects.Exchange import Exchange


class TestNBSCalculations(TestCase):
    def setUp(self):
        self.a = ActorIssue(position=0, salience=1, power=1)
        self.b = ActorIssue(position=100, salience=1, power=1)
        self.c = ActorIssue(position=100, salience=1, power=1)
        self.actor_issues = [self.a, self.b, self.c]

    def test_calc_nbs(self):
        self.assertEqual(calc_nbs([self.a, self.b]), 50)
        self.assertEqual(calc_nbs(self.actor_issues), 200 / 3)

    def test_calc_adjusted_nbs(self):
        a1 = Actor("Mock")
        a1.Id = 0

        a2 = Actor("Mock2")
        a2.Id = 1

        a3 = Actor("Mock3")
        a3.Id = 2

        self.assertEqual(calc_adjusted_nbs(self.actor_issues, a1, 100), 100)
        self.assertEqual(calc_adjusted_nbs(self.actor_issues, a2, 0), 200 / 3)
        self.assertEqual(calc_adjusted_nbs(self.actor_issues, a1, 0), 100 / 3)
        self.assertEqual(calc_adjusted_nbs(self.actor_issues, a3, 0), 0)


class TestBy_absolute_move(TestCase):
    def test_by_absolute_move(self):
        csv = csvParser.Parser()

        model = csv.read("data/CoP21.csv")

        # /	actor	issue	position	salience	power
        # D	China	financevol	100	0.5	1
        # D	USA	financevol	0	0.7	1
        # D	China	eaa	0	0.65	1
        # D	USA	eaa	100	0.4	1

        i = model.Actors["USA"]
        j = model.Actors["China"]
        p = "financevol"
        q = "eaa"
        e = Exchange(i, j, p, q, model)

        dp = by_absolute_move(model.ActorIssues[e.i.supply], e.i)
        dq = by_exchange_ratio(e.i, dp)

        self.assertAlmostEqual(dp, 10.309, delta=0.001)
        self.assertAlmostEqual(dq, 9.021, delta=0.001)

        move = reverse_move(model.ActorIssues[e.j.supply], exchange_ratio=dq, actor=e.j)

        self.assertAlmostEqual(move, 89.214, delta=0.001)

        self.assertLess(move, e.i.x - e.j.x_demand)

        dp_1 = by_absolute_move(model.ActorIssues[e.j.supply], e.j)
        dq_1 = by_exchange_ratio(e.j, dp)

        move_1 = reverse_move(model.ActorIssues[e.i.supply], e.i, dq_1)
        self.assertGreater(move_1, 100)

    def test_sumSaliencePower(self):
        a1 = ActorIssue(50, 0.75, 0.75)
        a2 = ActorIssue(50, 0.25, 0.25)
        a3 = ActorIssue(10, 1, 1)

        self.assertEqual(sum_salience_power([a1, a2, a3]), (0.75 * 0.75 + 0.25 * 0.25 + 1 * 1))
