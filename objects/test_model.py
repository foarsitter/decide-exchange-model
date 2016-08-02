import math
from unittest import TestCase

import csvParser
from objects.Model import Model


class TestModel(TestCase):
    def setUp(self):
        csv = csvParser.Parser()
        self.model = csv.read("C:/Users/jelmer/PycharmProjects/EqualGain/data/data_short.csv")

    def test_addActor(self):
        model = Model()

        a1 = model.add_actor("TestActor1")
        a2 = model.add_actor("TestActor2")

        self.assertEqual(a1.Id, 0)
        self.assertEqual(a2.Id, 1)

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

        self.assertAlmostEqual(e.gain, 1.128903122498, delta=1e-8)

    def test_calc_combinations(self):
        self.model.calc_combinations()
        combinations = len(list(self.model.issue_combinations))

        n = len(self.model.Issues)
        k = 2

        self.assertEqual(combinations, math.factorial(n) / (math.factorial(k) * math.factorial(n - k)))
