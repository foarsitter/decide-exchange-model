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

        X = euj

        # we should choose a random actor, but we assume i is selected
        # random_actor = exchange.i if random.getrandbits(1) else exchange.j

        random_actor = exchange.i  # type: EqualGainExchangeActor

        # to achieve the maximum gain, the actor moves completely to the other side
        # random_actor.y = exchange.j.x_demand
        # while the other actor does not move
        # random_actor.opposite_actor.y = random_actor.opposite_actor.x

        # nbs = model.nbs[random_actor.supply_issue]
        # nbs_adj = calculations.adjusted_nbs(model.actor_issues[random_actor.supply_issue],
        #                           {},
        #                           random_actor.actor_name, random_actor.y,
        #                           model.nbs_denominators[random_actor.supply_issue])

        # nbs_diff = abs(nbs-nbs_adj)

        # eui_max = nbs_diff * random_actor.s

        gain = X / random_actor.opposite_actor.s

        Y = eui + gain * random_actor.s

        nbs_adjusted = random_actor.nbs_1 - gain

        new_pos = calculations.position_by_nbs(model.actor_issues[random_actor.supply_issue],
                                               random_actor,
                                               nbs_adjusted,
                                               model.nbs_denominators[random_actor.supply_issue])

        random_actor.y = new_pos

        r = decimal.Decimal(random.random())  # between 0 and 1

        eu_ir = ((X - r * X), (X + r * (Y-X)))

        # // en dan?

        dus = random.uniform(float(eu_ir[0]), float(eu_ir[1]))

        delta_x_i = abs(random_actor.x - random_actor.y)
        delta_x_j = abs(random_actor.opposite_actor.x - random_actor.opposite_actor.y)

        dp = calculations.exchange_ratio(delta_x_i, salience=random_actor.s, power=random_actor.c,
                                    dominator=model.nbs_denominators[random_actor.supply_issue])
        dq = calculations.exchange_ratio(delta_x_j, salience=random_actor.opposite_actor.s, power=random_actor.opposite_actor.c,
                                    dominator=model.nbs_denominators[random_actor.opposite_actor.supply_issue])

        eui = calculations.expected_utility(random_actor, dq, dp)
        euj = calculations.expected_utility(random_actor.opposite_actor, dp, dq)

        print('done..')
