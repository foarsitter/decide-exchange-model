import os
from decimal import *
from unittest import TestCase
from unittest.mock import patch, MagicMock

from decide.model import calculations, base
from decide.model.equalgain import EqualGainExchange, EqualGainModel
from decide.model.helpers import csvparser


class BaseModelTest(TestCase):
    def setUp(self):
        self.model = EqualGainModel()

        filename = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../../../data/input/sample_data.txt",
        )

        csv = csvparser.CsvParser(self.model)
        csv.read(filename=filename)


class TestNBSCalculations(TestCase):
    def setUp(self):
        a = base.Actor("a")
        b = base.Actor("b")
        c = base.Actor("c")

        p = base.Issue("p")

        self.a = base.ActorIssue(a, p, position=0, salience=1, power=1)
        self.b = base.ActorIssue(b, p, position=100, salience=1, power=1)
        self.c = base.ActorIssue(c, p, position=100, salience=1, power=1)

        self.actor_issues = {"a": self.a, "b": self.b, "c": self.c}
        self.denominator = calculations.calc_nbs_denominator(self.actor_issues)
        self.model = EqualGainModel()

    def test_calc_nbs(self):
        denominator = calculations.calc_nbs_denominator({"a": self.a, "b": self.b})

        self.assertEqual(
            calculations.nash_bargaining_solution(
                {"a": self.a, "b": self.b}, denominator
            ),
            50,
        )
        self.assertEqual(
            calculations.nash_bargaining_solution(self.actor_issues, self.denominator),
            Decimal(200) / Decimal(3),
        )

    def test_calc_adjusted_nbs(self):
        a1 = "a"
        a2 = "b"
        a3 = "c"

        self.assertEqual(
            calculations.adjusted_nbs(self.actor_issues, {}, a1, 100, self.denominator),
            100,
        )

        self.assertEqual(
            calculations.adjusted_nbs(self.actor_issues, {}, a2, 0, self.denominator),
            Decimal(100) / Decimal(3),
        )

        self.assertEqual(
            calculations.adjusted_nbs(self.actor_issues, {}, a1, 0, self.denominator),
            Decimal(200) / Decimal(3),
        )

        self.assertEqual(
            calculations.adjusted_nbs(
                self.actor_issues, {"a": 100}, a3, 0, self.denominator
            ),
            Decimal(200) / Decimal(3),
        )

    def test_by_absolute_move(self):
        csv = csvparser.CsvParser(self.model)

        file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../../../data/input/sample_data.txt",
        )
        model = csv.read(file)

        i = model.actors["wcentr"]
        j = model.actors["willems"]
        p = model.issues["tolheffingbinnenstad"]
        q = model.issues["extrainvestering"]
        e = EqualGainExchange(i, j, p, q, model, groups=["a", "d"])

        dp = calculations.by_absolute_move(model.actor_issues[e.i.supply.issue], e.i)
        dq = calculations.by_exchange_ratio(e.i, dp)

        self.assertAlmostEqual(dp, Decimal(13.15789473684210526315789474), delta=0.001)
        self.assertAlmostEqual(dq, Decimal(10.38781163434903047091412743), delta=0.001)

        move = calculations.reverse_move(
            model.actor_issues[e.j.supply.issue], exchange_ratio=dq, actor=e.j
        )

        self.assertAlmostEqual(
            move, Decimal(61.05117364047237206589881911), delta=0.001
        )

        self.assertLess(move, abs(e.i.supply.position - e.j.demand.position))

        dp_1 = calculations.by_absolute_move(model.actor_issues[e.j.supply.issue], e.j)
        dq_1 = calculations.by_exchange_ratio(e.j, dp)

        move_1 = calculations.reverse_move(
            model.actor_issues[e.i.supply.issue], e.i, dq_1
        )
        self.assertGreater(move_1, abs(e.i.supply.position - e.j.demand.position))

    def test_sumSaliencePower(self):
        self.assertEqual(
            calculations.sum_salience_power({"a": self.a, "b": self.b, "c": self.c}),
            (3),
        )

    def test_new_start_position(self):
        self.assertAlmostEqual(
            calculations.new_start_position(1, 0, 100), 10, delta=1e-10
        )
        self.assertAlmostEqual(
            calculations.new_start_position(1, 100, 0), 90, delta=1e-10
        )


class TestCalculations(BaseModelTest):
    @patch("decide.model.calculations.sum_salience_power")
    def test_reverse_move(self, sum_salience_power):
        sum_salience_power.return_value = 3
        actor = MagicMock()
        actor.supply = MagicMock(salience=1, power=1)

        res = calculations.reverse_move(actor_issues=[], actor=actor, exchange_ratio=1)

        self.assertEqual(res, 3)

    def test_sum_salience_power(self):
        actor_issues = [
            base.ActorIssue(None, None, 1, 1, 1),
            base.ActorIssue(None, None, 1, 1, 1),
        ]

        mock = MagicMock()
        mock.values = MagicMock(return_value=actor_issues)

        self.assertEqual(mock.values(), actor_issues)

        self.assertEqual(calculations.sum_salience_power(mock), 2)

        actor_issues.append(base.ActorIssue(None, None, 1, 1, 1))

        self.assertEqual(calculations.sum_salience_power(mock), 3)
