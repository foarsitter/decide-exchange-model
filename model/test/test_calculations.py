from decimal import *
from unittest import TestCase

from model.base import ActorIssue, Actor, Issue
from model.calculations import calc_nbs_denominator, calc_nbs, adjusted_nbs, by_absolute_move, by_exchange_ratio, \
    reverse_move, sum_salience_power
from model.equalgain import EqualGainExchange, EqualGainModel
from model.helpers import csvparser


class TestNBSCalculations(TestCase):
    def setUp(self):

        a = Actor("a")
        b = Actor("b")
        c = Actor("c")

        p = Issue('p')

        self.a = ActorIssue(a, p, position=0, salience=1, power=1)
        self.b = ActorIssue(b, p, position=100, salience=1, power=1)
        self.c = ActorIssue(c, p, position=100, salience=1, power=1)

        self.actor_issues = {"a": self.a, "b": self.b, "c": self.c}
        self.denominator = calc_nbs_denominator(self.actor_issues)
        self.model = EqualGainModel()

    def test_calc_nbs(self):
        denominator = calc_nbs_denominator({"a": self.a, "b": self.b})

        self.assertEqual(calc_nbs({"a": self.a, "b": self.b}, denominator), 50)
        self.assertEqual(calc_nbs(self.actor_issues, self.denominator), Decimal(200) / Decimal(3))

    def test_calc_adjusted_nbs(self):
        a1 = "a"
        a2 = "b"
        a3 = "c"

        self.assertEqual(adjusted_nbs(self.actor_issues, {}, a1, 100, self.denominator), 100)

        self.assertEqual(adjusted_nbs(self.actor_issues, {}, a2, 0, self.denominator), Decimal(100) / Decimal(3))

        self.assertEqual(adjusted_nbs(self.actor_issues, {}, a1, 0, self.denominator), Decimal(200) / Decimal(3))

        self.assertEqual(adjusted_nbs(self.actor_issues, {"a": 100}, a3, 0, self.denominator),
                         Decimal(200) / Decimal(3))

    def test_by_absolute_move(self):
        csv = csvparser.CsvParser(self.model)

        model = csv.read("data/input/sample_data.txt")

        # /	actor	issue	position	salience	power
        # D	China	financevol	100	0.5	1
        # D	USA	financevol	0	0.7	1
        # D	China	eaa	0	0.65	1
        # D	USA	eaa	100	0.4	1

        i = model.actors["wcentr"]
        j = model.actors["willems"]
        p = model.issues["tolheffingbinnenstad"]
        q = model.issues["extrainvestering"]
        e = EqualGainExchange(i, j, p, q, model, groups=['a', 'd'])

        dp = by_absolute_move(model.actor_issues[e.i.supply_issue], e.i)
        dq = by_exchange_ratio(e.i, dp)

        self.assertAlmostEqual(dp, Decimal(13.15789473684210526315789474), delta=0.001)
        self.assertAlmostEqual(dq, Decimal(10.38781163434903047091412743), delta=0.001)

        move = reverse_move(model.actor_issues[e.j.supply_issue], exchange_ratio=dq, actor=e.j)

        self.assertAlmostEqual(move, Decimal(61.05117364047237206589881911), delta=0.001)

        self.assertLess(move, abs(e.i.x - e.j.x_demand))

        dp_1 = by_absolute_move(model.actor_issues[e.j.supply_issue], e.j)
        dq_1 = by_exchange_ratio(e.j, dp)

        move_1 = reverse_move(model.actor_issues[e.i.supply_issue], e.i, dq_1)
        self.assertGreater(move_1, abs(e.i.x - e.j.x_demand))

    def test_sumSaliencePower(self):
        # a1 = ActorIssue("a", "p", 50, 0.75, 0.75)
        # a2 = ActorIssue("b", "p", 50, 0.25, 0.25)
        # a3 = ActorIssue("c", "p", 10, 1, 1)

        self.assertEqual(sum_salience_power({"a": self.a, "b": self.b, "c": self.c}), (3))

    def test_externalities(self):
        csv = csvparser.CsvParser(self.model)

        model = csv.read("data/input/sample_data.txt")

        model.calc_nbs()
        model.determine_positions()
        model.calc_combinations()
        model.determine_groups()

        i = model.actors["d66"]
        j = model.actors["cda"]
        p = model.issues['wanneertol']
        q = model.issues["tolheffingbinnenstad"]
        e = EqualGainExchange(i, j, p, q, model, groups=['a', 'd'])

        e.calculate()

        nbs_0 = model.nbs[p]
        nbs_1 = adjusted_nbs(model.actor_issues[p], e.updates, e.j.actor, e.j.y,
                             model.nbs_denominators[p])
        #
        # Russia = model.actor_issues[p]["rusia"]  # russia is an D group actor, so he is inner
        # Umbrellamin = model.actor_issues[p]["umbrellamin"]  # Umbrellamin is and B group actor, so he is outer
        # Arabstates = model.actor_issues[p]["arabstates"]  # Arabstates is and C group actor, so he is outer

        # # todo add type checks for op,ip,in,on and own
        # # todo fix this test with the proper calculations
        #
        # ext_russia = calculations.externalities(Russia.actor_name, model, e)
        # self.assertEqual(ext_russia, (
        # abs(nbs_0 - Russia.position) * Russia.salience - abs(nbs_1 - Russia.position)) * Russia.salience)
        #
        # ext_umbrella = calculations.externalities(Umbrellamin.actor_name, model, e)
        # self.assertEqual(ext_umbrella,
        #                  (abs(nbs_0 - Umbrellamin.position) - abs(nbs_1 - Umbrellamin.position)) * Umbrellamin.salience)
        #
        # ext_Arabstates = calculations.externalities(Arabstates.actor_name, model, e)
        # self.assertEqual(ext_Arabstates,
        #                  (abs(nbs_0 - Arabstates.position) - abs(nbs_1 - Arabstates.position)) * Arabstates.salience)
        #
        # # only one actor of the exchange has an positive own externality on this.
        #
        # ai_i = model.actor_issues[p]["usa"]
        # ai_j = model.actor_issues[p]["china"]
        #
        # ext_i = calculations.xternalities(ai_i.actor_name, model, e)
        # self.assertEqual(ext_i["value"], (abs(nbs_0 - ai_i.position) - abs(nbs_1 - ai_i.position)) * ai_i.salience)
        #
        # ext_j = calculations.externalities(ai_j.actor_name, model, e)
        # self.assertEqual(ext_j["value"], (abs(nbs_0 - ai_j.position) - abs(nbs_1 - ai_j.position)) * ai_j.salience)
