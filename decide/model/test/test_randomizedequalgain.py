import decimal
import random
from unittest import TestCase

from scipy import stats

from decide.model import calculations
from decide.model.equalgain import EqualGainModel, EqualGainExchange


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

        exchange_ratio_zero_i = calculations.exchange_ratio_by_expected_utility(exchange.dp, exchange.i.supply.salience, exchange.i.demand.salience)
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

        exchange_ratio_zero_j = calculations.exchange_ratio_by_expected_utility(exchange.dq, exchange.j.supply.salience,
                                                                                exchange.j.demand.salience)
        euj_max = calculations.expected_utility(exchange.j, exchange.dq, exchange_ratio_zero_j)

        if euj_max > 1e-10:
            raise Exception('error')

        yj = abs(calculations.expected_utility(exchange.j.opposite_actor, exchange_ratio_zero_j, exchange.dq))

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

    def test_calculations_doc(self):

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
        eu = exchange.gain

        self.assertAlmostEqual(eui, euj, delta=1e-25)  # here we have an equal utility gain

        p = decimal.Decimal(0.1)

        U = decimal.Decimal(random.random())
        V = decimal.Decimal(random.random())
        Z = decimal.Decimal(random.random())

        if U < 0.5:
            if V < 0.5:
                exchange_ratio_zero_i = calculations.exchange_ratio_by_expected_utility(exchange.dp,
                                                                                        exchange.i.supply.salience,
                                                                                        exchange.i.demand.salience)
                eui_max = calculations.expected_utility(exchange.i, exchange.dp, exchange_ratio_zero_i)
                eui = p * Z * (eui_max - eu) + eu
            else:
                eui = eu - p * Z * eu

            # calculate the exepcted utility of J
            supply_actor = exchange.i

            new_gain = eui
        else:
            if V < 0.5:
                exchange_ratio_zero_j = calculations.exchange_ratio_by_expected_utility(exchange.dq,
                                                                                        exchange.j.supply.salience,
                                                                                        exchange.j.demand.salience)
                euj_max = calculations.expected_utility(exchange.i, exchange.dp, exchange_ratio_zero_j)
                euj = p * Z * (euj_max - eu) + eu
            else:
                euj = eu - p * Z * eu

            supply_actor = exchange.j
            new_gain = euj

        delta_x = abs(supply_actor.supply.position - supply_actor.opposite_actor.demand.position)
        # supply exchange ratio for i, demand for j
        exchange_ratio = calculations.exchange_ratio(delta_x, supply_actor.supply.salience, supply_actor.supply.power,
                                                     model.nbs_denominators[supply_actor.supply.issue])

        # supply exchange ratio for j, demand for i
        dq = calculations.exchange_ratio_by_expected_utility(exchange_ratio, supply_actor.supply.salience,
                                                             supply_actor.demand.salience, utility=new_gain)

        euj = calculations.expected_utility(supply_actor.opposite_actor, dq, exchange_ratio)
        print(euj)

    def test_random_distribution(self):

        from random import uniform
        import numpy as np
        n = 1000

        distibution_to_test = [uniform(0, 1) for _ in range(n)]

        kstest = stats.kstest(distibution_to_test, stats.uniform.cdf, N=n)

        print(kstest)

        kstest = stats.kstest(distibution_to_test, 'uniform', N=n)

        print(kstest)

        s = np.random.uniform(0, 1, n)

        kstest = stats.kstest(s, stats.uniform.cdf, N=n)

        print(kstest)