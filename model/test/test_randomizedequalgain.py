import random
from unittest import TestCase

import decimal

from model import calculations
from model.base import Actor, Issue, ActorIssue
from model.equalgain import EqualGainModel, EqualGainExchange, EqualGainExchangeActor


class TestRandomizedEqualGain(TestCase):
    def test_init(self):
        pass

    def test_calculations(self):

        model = EqualGainModel()

        i = model.add_actor('i')
        j = model.add_actor('j')

        p = model.add_issue('p')
        q = model.add_issue('q')

        ip = model.add_actor_issue(i, p, position=0, power=0.6, salience=0.8)
        iq = model.add_actor_issue(i, q, position=0, power=0.6, salience=0.5)

        jp = model.add_actor_issue(actor=j, issue=p, position=100, power=0.5, salience=0.7)
        jq = model.add_actor_issue(actor=j, issue=q, position=100, power=0.5, salience=0.9)

        model.calc_nbs()
        model.determine_positions()
        model.calc_combinations()
        model.determine_groups()

        exchange = model.exchanges[0]  # type: EqualGainExchange
        exchange.calculate()

        eui = exchange.gain
        euj = exchange.gain

        self.assertAlmostEqual(eui, euj, delta=1e-25)  # here we have an equal utility gain

        r = decimal.Decimal(0.1)  # decimal.Decimal(random.random())  # between 0 and 1

        exchange_ratio_zero_i = calculations.exchange_ratio_by_zero_gain(exchange.dp, exchange.i.s, exchange.i.s_demand)
        eui_max = calculations.expected_utility(exchange.i, exchange.dp, exchange_ratio_zero_i)

        if eui_max > 1e-10:
            raise Exception('error')

        yi = abs(calculations.expected_utility(exchange.i.opposite_actor, exchange_ratio_zero_i, exchange.dp))

        xi = exchange.gain
        eu_ir = ((xi - r * xi), (xi + r * (yi-xi)))

        ####
        ####
        # start J
        ####
        ####

        exchange_ratio_zero_j = calculations.exchange_ratio_by_zero_gain(exchange.dq, exchange.j.s,
                                                                         exchange.j.s_demand)
        euj_max = calculations.expected_utility(exchange.j, exchange.dq, exchange_ratio_zero_j)

        if euj_max > 1e-10:
            raise Exception('error')

        yj = abs(calculations.expected_utility(exchange.j.opposite_actor, exchange.dq, exchange_ratio_zero_j))

        xj = exchange.gain

        eu_jr = ((xj - r * xj), (xi + r * (yj - xj)))

        if random.getrandbits(1) == 1:
            eui = eu_ir[0]
            euj = eu_jr[1]
        else:
            eui = eu_ir[1]
            euj = eu_jr[0]

        print(eui)
        print(euj)

