import math
import os
from decimal import *
from unittest import TestCase

from decide.model.equalgain import EqualGainModel
from decide.model.helpers import csvparser


class TestModel(TestCase):
    def setUp(self):
        csv = csvparser.CsvParser(EqualGainModel())
        file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../../../data/input/sample_data.txt",
        )
        self.model = csv.read(file)
        # self.model = csv.read("data\\CoP21.csv")

    def test_addActor(self):
        model = EqualGainModel()

        a1 = model.add_actor("TestActor1")
        a2 = model.add_actor("TestActor2")

        self.assertEqual(len(model.actors), 2)
        self.assertNotEqual(a1, a2)

    def test_first_phase(self):
        model = self.model

        model.calc_nbs()  # tested in test_calculations.py#test_calc_nbs

        model.calc_combinations()  # tested below
        model.determine_positions()
        model.determine_groups()

        totalactor_issues = 0

        for k, v in model.groups.items():
            a = len(model.groups[k]["a"])
            b = len(model.groups[k]["b"])
            c = len(model.groups[k]["c"])
            d = len(model.groups[k]["d"])

            self.assertEqual(sum([a, b, c, d]), 10)

            totalactor_issues += a * d
            totalactor_issues += b * c

        self.assertEqual(totalactor_issues, 240)

        e = model.highest_gain()

        self.assertAlmostEqual(
            e.gain, Decimal(1.973684210526315789473684214), delta=1e-8
        )

        # the delta is necessary for the random component by exchanges which have an equal gain.
        # in some cases the gain of the exchanges (two exchanges with each two (unique) actors) are the same.
        # we pick random the next exchange. Theoretically it is even possible to get more exchanges with the same gain
        self.assertAlmostEqual(len(model.exchanges), 239, delta=2)
        realized = list()
        realized.append(e)

        model.remove_invalid_exchanges(e)

        e1 = model.highest_gain()
        model.remove_invalid_exchanges(e1)
        realized.append(e1)

        self.assertAlmostEqual(
            e1.gain, Decimal(1.79263630876534102340553952), delta=1e-8
        )

        while len(model.exchanges) > 0:
            realize = model.highest_gain()
            model.remove_invalid_exchanges(realize)
            realized.append(realize)

            # self.assertEqual(len(realized), 16)

    def test_calc_combinations(self):
        self.model.calc_combinations()
        combinations = len(list(self.model.issue_combinations))

        n = len(self.model.issues)
        k = 2

        self.assertEqual(
            combinations,
            math.factorial(n) / (math.factorial(k) * math.factorial(n - k)),
        )
