import math
from decimal import *

from decide.model.equalgain import EqualGainModel


def test_add_actor():
    model = EqualGainModel()

    a1 = model.add_actor("TestActor1")
    a2 = model.add_actor("TestActor2")

    assert len(model.actors) == 2
    assert a1 != a2


def test_first_phase(model):
    model.calc_nbs()  # tested in test_calculations.py#test_calc_nbs

    model.calc_combinations()  # tested below
    model.determine_positions()
    model.determine_groups_and_calculate_exchanges()

    totalactor_issues = 0

    for k, v in model.groups.items():
        a = len(model.groups[k]["a"])
        b = len(model.groups[k]["b"])
        c = len(model.groups[k]["c"])
        d = len(model.groups[k]["d"])

        assert sum([a, b, c, d]) == 10

        totalactor_issues += a * d
        totalactor_issues += b * c

    assert totalactor_issues == 240

    e = model.highest_gain()

    assert e.gain - Decimal(1.973684210526315789473684214) < 1e-8

    # the delta is necessary for the random component by exchanges which have an equal gain.
    # in some cases the gain of the exchanges (two exchanges with each two (unique) actors) are the same.
    # we pick random the next exchange. Theoretically it is even possible to get more exchanges with the same gain
    assert len(model.exchanges) - 239 < 2

    realized = list()
    realized.append(e)

    model.remove_invalid_exchanges(e)

    e1 = model.highest_gain()
    model.remove_invalid_exchanges(e1)
    realized.append(e1)

    assert e1.gain - Decimal(1.79263630876534102340553952) < 1e-8

    while len(model.exchanges) > 0:
        realize = model.highest_gain()
        model.remove_invalid_exchanges(realize)
        realized.append(realize)

    assert len(realized) == 37


def test_calc_combinations(model):
    model.calc_combinations()
    combinations = len(list(model.issue_combinations))

    n = len(model.issues)
    k = 2

    assert combinations == math.factorial(n) / (math.factorial(k) * math.factorial(n - k))
