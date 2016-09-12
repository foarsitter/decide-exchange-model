import math
from decimal import *
from unittest import TestCase

import csvParser
from objects.Model import Model


class TestModel(TestCase):
    def setUp(self):
        csv = csvParser.Parser()
        self.model = csv.read("data\\data_short.csv")
        # self.model = csv.read("data\\CoP21.csv")

    def test_addActor(self):
        model = Model()

        a1 = model.add_actor("TestActor1")
        a2 = model.add_actor("TestActor2")

        self.assertEqual(len(model.Actors), 2)

    def test_get_actor_issue(self):
        pass
        # model = Model()
        #
        # model.add_actor_issue()

    def test_first_phase(self):
        model = self.model

        model.calc_nbs()  # tested in test_calculations.py#test_calc_nbs

        model.calc_combinations()  # tested below
        model.determine_positions()
        model.determine_groups()

        totalActorIssues = 0

        for k, v in model.groups.items():
            a = len(model.groups[k]["a"])
            b = len(model.groups[k]["b"])
            c = len(model.groups[k]["c"])
            d = len(model.groups[k]["d"])

            self.assertEqual(sum([a, b, c, d]), 15)

            totalActorIssues += a * d
            totalActorIssues += b * c

        self.assertEqual(totalActorIssues, 103)

        e = model.highest_gain()

        self.assertAlmostEqual(e.gain, Decimal(1.128903122498), delta=1e-8)
        self.assertEqual(len(model.Exchanges), 102)
        realized = list()
        realized.append(e)

        model.update_exchanges(e)

        e1 = model.highest_gain()
        model.update_exchanges(e1)
        realized.append(e1)

        self.assertAlmostEqual(e1.gain, Decimal(0.756186984), delta=1e-8)

        while len(model.Exchanges) > 0:
            realize = model.highest_gain()
            model.update_exchanges(realize)
            realized.append(realize)

        self.assertEqual(len(realized), 20)

    def test_calc_combinations(self):
        self.model.calc_combinations()
        combinations = len(list(self.model.issue_combinations))

        n = len(self.model.Issues)
        k = 2

        self.assertEqual(combinations, math.factorial(n) / (math.factorial(k) * math.factorial(n - k)))

    def test_exchange_99(self):
        csv = csvParser.Parser()
        model = csv.read("data\\CoP21.csv")

        model.calc_nbs()  # tested in test_calculations.py#test_calc_nbs

        model.calc_combinations()  # tested below
        model.determine_positions()
        model.determine_groups()

        exchange_99 = None

        in_iteration = 0

        for exchange in model.Exchanges:
            if exchange.equals(i="EU28", q="financevol", j="AOSIS", p="amb2050"):
                exchange_99 = exchange

        while len(model.Exchanges) > 0:
            realize = model.highest_gain()
            model.update_exchanges(realize)

            founded_99 = False
            for exchange in model.Exchanges:
                if exchange.equals(i="EU28", q="financevol", j="AOSIS", p="amb2050"):
                    founded_99 = True

            if not founded_99:
                break

            in_iteration += 1

        exchange_99.recalculate(realize)

        self.assertEqual(exchange_99.i.y, 0)
