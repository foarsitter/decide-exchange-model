from decimal import *
from unittest import TestCase

import csvParser
from calculations import by_exchange_ratio, by_absolute_move, calc_adjusted_nbs, calc_nbs, reverse_move, \
    sum_salience_power, calc_nbs_denominator, externalities
from objects.Actor import Actor
from objects.ActorIssue import ActorIssue
from objects.Exchange import Exchange


class TestNBSCalculations(TestCase):
    def setUp(self):
        self.a = ActorIssue(Actor("a"), position=0, salience=1, power=1)
        self.b = ActorIssue(Actor("b"), position=100, salience=1, power=1)
        self.c = ActorIssue(Actor("c"), position=100, salience=1, power=1)

        self.actor_issues = {"a": self.a, "b": self.b, "c": self.c}
        self.denominator = calc_nbs_denominator(self.actor_issues)

    def test_calc_nbs(self):
        denominator = calc_nbs_denominator({"a": self.a, "b": self.b})

        self.assertEqual(calc_nbs({"a": self.a, "b": self.b}, denominator), 50)
        self.assertEqual(calc_nbs(self.actor_issues, self.denominator), Decimal(200) / Decimal(3))

    def test_calc_adjusted_nbs(self):
        a1 = Actor("a")

        a2 = Actor("b")

        a3 = Actor("c")

        self.assertEqual(calc_adjusted_nbs(self.actor_issues, {}, a1, 100, self.denominator), 100)

        self.assertEqual(calc_adjusted_nbs(self.actor_issues, {}, a2, 0, self.denominator), Decimal(100) / Decimal(3))

        self.assertEqual(calc_adjusted_nbs(self.actor_issues, {}, a1, 0, self.denominator), Decimal(200) / Decimal(3))

        self.assertEqual(calc_adjusted_nbs(self.actor_issues, {"a": 100}, a3, 0, self.denominator),
                         Decimal(200) / Decimal(3))


class TestBy_absolute_move(TestCase):
    def test_by_absolute_move(self):
        csv = csvParser.Parser()

        model = csv.read("data\\CoP21.csv")

        # /	actor	issue	position	salience	power
        # D	China	financevol	100	0.5	1
        # D	USA	financevol	0	0.7	1
        # D	China	eaa	0	0.65	1
        # D	USA	eaa	100	0.4	1

        i = model.Actors["USA"]
        j = model.Actors["China"]
        p = "financevol"
        q = "eaa"
        e = Exchange(i, j, p, q, model, groups=['a', 'd'])

        dp = by_absolute_move(model.ActorIssues[e.i.supply], e.i)
        dq = by_exchange_ratio(e.i, dp)

        self.assertAlmostEqual(dp, Decimal(10.309), delta=0.001)
        self.assertAlmostEqual(dq, Decimal(9.021), delta=0.001)

        move = reverse_move(model.ActorIssues[e.j.supply], exchange_ratio=dq, actor=e.j)

        self.assertAlmostEqual(move, Decimal(89.214), delta=0.001)

        self.assertLess(move, e.i.x - e.j.x_demand)

        dp_1 = by_absolute_move(model.ActorIssues[e.j.supply], e.j)
        dq_1 = by_exchange_ratio(e.j, dp)

        move_1 = reverse_move(model.ActorIssues[e.i.supply], e.i, dq_1)
        self.assertGreater(move_1, 100)

    def test_sumSaliencePower(self):
        a1 = ActorIssue(Actor("a"), 50, 0.75, 0.75)
        a2 = ActorIssue(Actor("b"), 50, 0.25, 0.25)
        a3 = ActorIssue(Actor("c"), 10, 1, 1)

        self.assertEqual(sum_salience_power({"a": a1, "b": a2, "c": a3}), (0.75 * 0.75 + 0.25 * 0.25 + 1 * 1))

    def test_externalities(self):
        csv = csvParser.Parser()

        model = csv.read("data\\CoP21.csv")

        # /	actor	issue	position	salience	power
        # D	China	financevol	100	0.5	1
        # D	USA	financevol	0	0.7	1
        # D	China	eaa	0	0.65	1
        # D	USA	eaa	100	0.4	1

        model.calc_nbs()
        model.determine_positions()
        model.calc_combinations()
        model.determine_groups()

        i = model.Actors["USA"]
        j = model.Actors["China"]
        p = "financevol"
        q = "eaa"
        e = Exchange(i, j, p, q, model, groups=['a', 'd'])

        e.calculate()

        nbs_0 = model.nbs[p]
        nbs_1 = calc_adjusted_nbs(model.ActorIssues[p], e.updates, e.j.actor, e.j.y,
                                  model.nbs_denominators[p])

        Russia = model.ActorIssues[p]["Russia"]  # russia is an D group actor, so he is inner
        Umbrellamin = model.ActorIssues[p]["Umbrellamin"]  # Umbrellamin is and B group actor, so he is outer
        Arabstates = model.ActorIssues[p]["Arabstates"]  # Arabstates is and C group actor, so he is outer

        # todo add type checks for op,ip,in,on and own

        ext_russia = externalities(Russia, nbs_0, nbs_1, e)
        self.assertEqual(ext_russia["value"], ((nbs_0 - Russia.position) - (nbs_1 - Russia.position)) * Russia.salience)

        ext_umbrella = externalities(Umbrellamin, nbs_0, nbs_1, e)
        self.assertEqual(ext_umbrella["value"],
                         (abs(nbs_0 - Umbrellamin.position) - abs(nbs_1 - Umbrellamin.position)) * Umbrellamin.salience)

        ext_Arabstates = externalities(Arabstates, nbs_0, nbs_1, e)
        self.assertEqual(ext_Arabstates["value"],
                         (abs(nbs_0 - Arabstates.position) - abs(nbs_1 - Arabstates.position)) * Arabstates.salience)

        # only one actor of the exchange has an positive own externality on this.

        ai_i = model.ActorIssues[p]["USA"]
        ai_j = model.ActorIssues[p]["China"]

        ext_i = externalities(ai_i, nbs_0, nbs_1, e)
        self.assertEqual(ext_i["value"], (abs(nbs_0 - ai_i.position) - abs(nbs_1 - ai_i.position)) * ai_i.salience)

        ext_j = externalities(ai_j, nbs_0, nbs_1, e)
        self.assertEqual(ext_j["value"], (abs(nbs_0 - ai_j.position) - abs(nbs_1 - ai_j.position)) * ai_j.salience)