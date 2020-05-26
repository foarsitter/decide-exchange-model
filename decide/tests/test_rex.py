import csv
import decimal
import random
import statistics
from decimal import Decimal

import pytest

from decide.data.modelfactory import ModelFactory
from decide.data.reader import InputDataFile
from decide.model.equalgain import EqualGainModel, EqualGainExchange, EqualGainExchangeActor


@pytest.fixture
def model_factory():
    input_data = """'#A'	'Actor-1'	'Actor-1'	''	
'#A'	'Actor-2'	'Actor-2'	''	
'#P'	'Issue-1'	'Issue-1'	'Issue-1'	
'#M'	'Issue-1'	0	
'#M'	'Issue-1'	100	
'#P'	'Issue-2'	'Issue-2'	'Issue-2'	
'#M'	'Issue-2'	0	
'#M'	'Issue-2'	100	
'#D'	'Actor-1'	'Issue-1'	0.0	10	1	
'#D'	'Actor-1'	'Issue-2'	0.0	90	1	
'#D'	'Actor-2'	'Issue-1'	100.0	60	1	
'#D'	'Actor-2'	'Issue-2'	100.0	50	1"""

    reader = csv.reader(input_data.splitlines(), delimiter="\t", quotechar="'")

    data_file = InputDataFile.open_reader(reader)

    assert len(data_file.actors) == 2
    assert len(data_file.actor_issues) == 4

    model_factory = ModelFactory(data_file)

    return model_factory


def test_rex(model_factory):
    rex = model_factory(model_klass=EqualGainModel, randomized_value=1)

    actor_1 = rex.actors['Actor-1']
    actor_2 = rex.actors['Actor-2']
    issue_1 = rex.issues['Issue-1']
    issue_2 = rex.issues['Issue-2']

    rex.calc_nbs()
    rex.determine_positions()
    rex.calc_combinations()
    rex.determine_groups_and_calculate_exchanges()

    nbs_issue_1 = rex.nbs[issue_1]
    nbs_issue_2 = rex.nbs[issue_2]

    assert rex.nbs[issue_1] == pytest.approx(Decimal(85 + 5 / 7))
    assert rex.nbs[issue_2] == pytest.approx(Decimal(35 + 5 / 7))
    exchange = rex.exchanges[0]

    a2 = exchange.i  # type: EqualGainExchangeActor
    a1 = exchange.j  # type: EqualGainExchangeActor

    assert a2.actor == actor_2
    assert a1.actor == actor_1

    nbs_issue_1_adjusted = a1.adjust_nbs(a1.opposite_actor.demand.position)
    nbs_issue_2_adjusted = a2.adjust_nbs(a2.opposite_actor.demand.position)

    assert nbs_issue_1_adjusted == 100
    assert nbs_issue_2_adjusted == 0

    nbs_issue_1_delta = abs(nbs_issue_1 - nbs_issue_1_adjusted)
    nbs_issue_2_delta = abs(nbs_issue_2 - nbs_issue_2_adjusted)

    loss_actor_1_issue_1 = nbs_issue_1_delta * a1.supply.salience * a1.supply.power
    gain_actor_2_issue_1 = nbs_issue_1_delta * a2.demand.salience * a2.demand.power

    assert loss_actor_1_issue_1 == pytest.approx(Decimal(1000 / 7))
    assert gain_actor_2_issue_1 == pytest.approx(Decimal(6000 / 7))

    gain_actor_1_issue_2 = nbs_issue_2_delta * a1.demand.salience * a1.demand.power
    loss_actor_2_issue_2 = nbs_issue_2_delta * a2.supply.salience * a2.supply.power

    assert gain_actor_1_issue_2 == pytest.approx(Decimal(22500 / 7))
    assert loss_actor_2_issue_2 == pytest.approx(Decimal(12500 / 7))

    s = a2.supply.salience / (a1.demand.salience + a2.supply.salience)

    delta_2_u1 = loss_actor_1_issue_1 / (s * a1.demand.salience)

    assert delta_2_u1 == pytest.approx(Decimal(1000 / 225))

    delta_2_u2 = gain_actor_2_issue_1 / (s * a2.supply.salience)

    assert delta_2_u2 == pytest.approx(48)

    max_eu_actor_1 = s * a1.demand.salience * delta_2_u2 - loss_actor_1_issue_1
    assert max_eu_actor_1 == 1400

    max_eu_actor_2 = gain_actor_2_issue_1 - (s * a2.supply.salience * delta_2_u1)
    assert max_eu_actor_2 == pytest.approx(Decimal(777.7778))


def test_rex_2(model_factory):
    rex = model_factory(model_klass=EqualGainModel, randomized_value=1)

    actor_1 = rex.actors['Actor-1']
    actor_2 = rex.actors['Actor-2']
    issue_1 = rex.issues['Issue-1']
    issue_2 = rex.issues['Issue-2']

    rex.calc_nbs()
    rex.determine_positions()
    rex.calc_combinations()
    rex.determine_groups_and_calculate_exchanges()

    nbs_issue_1 = rex.nbs[issue_1]
    nbs_issue_2 = rex.nbs[issue_2]

    assert rex.nbs[issue_1] == pytest.approx(Decimal(85 + 5 / 7))
    assert rex.nbs[issue_2] == pytest.approx(Decimal(35 + 5 / 7))
    exchange = rex.exchanges[0]  # type: EqualGainExchange

    assert exchange.i.actor == actor_2
    assert exchange.j.actor == actor_1

    assert exchange.i.supply.issue == issue_2
    assert exchange.j.supply.issue == issue_1

    nbs_supply_i_adjusted = exchange.i.adjust_nbs(exchange.i.opposite_actor.demand.position)
    nbs_supply_j_adjusted = exchange.j.adjust_nbs(exchange.j.opposite_actor.demand.position)

    assert nbs_supply_i_adjusted == 0
    assert nbs_supply_j_adjusted == 100

    nbs_supply_i_delta = abs(exchange.i.nbs_0 - nbs_supply_i_adjusted)
    nbs_supply_j_delta = abs(exchange.j.nbs_0 - nbs_supply_j_adjusted)

    loss_actor_j_supply_issue = nbs_supply_j_delta * exchange.j.supply.salience * exchange.j.supply.power
    gain_actor_i_demand_issue = nbs_supply_j_delta * exchange.i.demand.salience * exchange.i.demand.power

    assert loss_actor_j_supply_issue == pytest.approx(Decimal(1000 / 7))
    assert gain_actor_i_demand_issue == pytest.approx(Decimal(6000 / 7))

    loss_actor_i_supply_issue = nbs_supply_i_delta * exchange.i.supply.salience * exchange.i.supply.power
    gain_actor_j_demand_issue = nbs_supply_i_delta * exchange.j.demand.salience * exchange.j.demand.power

    assert loss_actor_i_supply_issue == pytest.approx(Decimal(12500 / 7))
    assert gain_actor_j_demand_issue == pytest.approx(Decimal(22500 / 7))

    # We kiezen hier voor actor i
    y = gain_actor_j_demand_issue / loss_actor_i_supply_issue
    z = gain_actor_i_demand_issue / loss_actor_j_supply_issue

    assert z > y
    # if y < z: issue 2
    s = exchange.i.supply.salience / (exchange.i.supply.salience + exchange.i.opposite_actor.demand.salience)

    delta_2_uj = loss_actor_j_supply_issue / (s * exchange.i.opposite_actor.demand.salience)

    assert delta_2_uj == pytest.approx(Decimal(1000 / 225))

    delta_2_ui = gain_actor_i_demand_issue / (s * exchange.i.supply.salience)

    assert delta_2_ui == pytest.approx(48)

    max_eu_actor_j = s * exchange.j.demand.salience * delta_2_ui - loss_actor_j_supply_issue
    assert max_eu_actor_j == 1400

    max_eu_actor_i = gain_actor_i_demand_issue - (s * exchange.i.supply.salience * delta_2_uj)
    assert max_eu_actor_i == pytest.approx(Decimal(777.7778))

    exchange.calculate_maximum_utility()

    assert exchange.i.eu_max == max_eu_actor_i
    assert exchange.j.eu_max == max_eu_actor_j

    exchange.j, exchange.i = exchange.i, exchange.j

    exchange.calculate_maximum_utility()

    assert exchange.j.eu_max == max_eu_actor_i
    assert exchange.i.eu_max == max_eu_actor_j


# def test_x(model_factory):
#
#     for p in range(0, 125, 25):
#         p = decimal.Decimal(p / 100)
#
#         rex = model_factory(model_klass=EqualGainModel, randomized_value=p)
#
#         rex.calc_nbs()
#         rex.determine_positions()
#         rex.calc_combinations()
#         rex.determine_groups_and_calculate_exchanges()
#
#         exchange = rex.exchanges[0]  # type: EqualGainExchange
#
#         x = []
#
#         for _ in range(10000):
#             exchange.calculate()
#             u = random.uniform(0, 1)
#             v = random.uniform(0, 1)
#             z = decimal.Decimal(random.uniform(0, 1))
#
#             exchange.calculate_maximum_utility()
#
#             exchange.i.randomized_gain(u, v, z)
#
#             x.append(exchange.i.eu)
#         y = statistics.variance(x)
#         print(p, y)
