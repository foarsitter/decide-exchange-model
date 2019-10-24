import decimal
from unittest.mock import MagicMock, patch

import pytest

from decide.model import calculations, base
from decide.model.equalgain import EqualGainModel, EqualGainExchange


class TestModel:
    """
    Object tit populate with test data
    """

@pytest.fixture
def test_model():
    test = TestModel()

    a = base.Actor("a")
    b = base.Actor("b")
    c = base.Actor("c")

    p = base.Issue("p")

    test.a = base.ActorIssue(a, p, position=0, salience=1, power=1)
    test.b = base.ActorIssue(b, p, position=100, salience=1, power=1)
    test.c = base.ActorIssue(c, p, position=100, salience=1, power=1)

    test.actor_issues = {"a": test.a, "b": test.b, "c": test.c}
    test.denominator = calculations.calc_nbs_denominator(test.actor_issues)
    test.model = EqualGainModel()

    return test


def test_calc_nbs(test_model):
    denominator = calculations.calc_nbs_denominator({"a": test_model.a, "b": test_model.b})

    assert calculations.nash_bargaining_solution({"a": test_model.a, "b": test_model.b}, denominator) == 50
    assert calculations.nash_bargaining_solution(test_model.actor_issues, test_model.denominator) == decimal.Decimal(
        200) / decimal.Decimal(3)


def test_calc_adjusted_nbs(test_model):
    a1 = "a"
    a2 = "b"
    a3 = "c"

    assert calculations.adjusted_nbs(test_model.actor_issues, {}, a1, 100, test_model.denominator) == 100

    assert calculations.adjusted_nbs(test_model.actor_issues, {}, a2, 0, test_model.denominator) == decimal.Decimal(
        100) / decimal.Decimal(3)
    assert calculations.adjusted_nbs(test_model.actor_issues, {}, a1, 0, test_model.denominator) == decimal.Decimal(
        200) / decimal.Decimal(3)
    assert calculations.adjusted_nbs(test_model.actor_issues, {"a": 100}, a3, 0,
                                     test_model.denominator) == decimal.Decimal(200) / decimal.Decimal(3)


def test_by_absolute_move(sample_model):
    model = sample_model

    i = model.actors["Wcentr"]
    j = model.actors["Willems"]
    p = model.issues["tolheffing-binnenstad"]
    q = model.issues["extra-investering"]

    e = EqualGainExchange(i, j, p, q, model, groups=["a", "d"])

    dp = calculations.by_absolute_move(model.actor_issues[e.i.supply.issue], e.i)
    dq = calculations.by_exchange_ratio(e.i, dp)

    assert dp - decimal.Decimal(13.15789473684210526315789474) < 0.001
    assert dq - decimal.Decimal(10.38781163434903047091412743) < 0.001

    move = calculations.reverse_move(
        model.actor_issues[e.j.supply.issue], exchange_ratio=dq, actor=e.j
    )

    assert move - decimal.Decimal(61.05117364047237206589881911) < 0.001

    assert move < abs(e.i.supply.position - e.j.demand.position)

    dp_1 = calculations.by_absolute_move(model.actor_issues[e.j.supply.issue], e.j)
    dq_1 = calculations.by_exchange_ratio(e.j, dp)

    move_1 = calculations.reverse_move(
        model.actor_issues[e.i.supply.issue], e.i, dq_1
    )

    assert move_1 > abs(e.i.supply.position - e.j.demand.position)


def test_sum_salience_power(test_model):
    assert calculations.sum_salience_power({"a": test_model.a, "b": test_model.b, "c": test_model.c}) == 3


def test_new_start_position():
    assert calculations.new_start_position(1, 0, 100) - 10 < 1e-10
    assert calculations.new_start_position(1, 100, 0) - 90 < 1e-10


@patch("decide.model.calculations.sum_salience_power")
def test_reverse_move(sum_salience_power):
    sum_salience_power.return_value = 3
    actor = MagicMock()
    actor.supply = MagicMock(salience=1, power=1)

    res = calculations.reverse_move(actor_issues=[], actor=actor, exchange_ratio=1)

    assert res == 3


def test_sum_salience_power_2():
    actor_issues = [
        base.ActorIssue(None, None, 1, 1, 1),
        base.ActorIssue(None, None, 1, 1, 1),
    ]

    mock = MagicMock()
    mock.values = MagicMock(return_value=actor_issues)

    assert mock.values(), actor_issues

    assert calculations.sum_salience_power(mock), 2

    actor_issues.append(base.ActorIssue(None, None, 1, 1, 1))

    assert calculations.sum_salience_power(mock) == 3
