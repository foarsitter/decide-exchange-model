import random
from operator import attrgetter

import decimal

from model.base import Actor, Issue
from . import base
from . import calculations


class EqualGainExchangeActor(base.AbstractExchangeActor):
    """
    AbstractExchangeActor is the same actor...
    """

    def __init__(self, model: 'EqualGainModel', actor: Actor, demand_issue: Issue, supply_issue: Issue,
                 exchange: 'EqualGainExchange'):
        super().__init__(model, actor, demand_issue, supply_issue, exchange)

        self.equal_gain_voting = '-'
        self.z = '-'

    def randomized_gain(self, u, v, z, exchange_ratio, exchange_ratio_string):

        p = self.exchange.model.randomized_value

        eu = self.exchange.gain

        self.z = z
        self.opposite_actor.z = '-'

        eui_max = None

        if v:  # V < 0.5:
            exchange_ratio_zero_i = calculations.exchange_ratio_by_expected_utility(exchange_ratio,
                                                                                    self.supply.salience,
                                                                                    self.demand.salience)

            eui_max = abs(calculations.expected_utility(self, exchange_ratio_zero_i, exchange_ratio))

            eui = p * z * (eui_max - eu) + eu
        else:
            eui = eu - p * z * eu

        # calculate the expected utility of J
        move_i = abs(self.supply.position - self.opposite_actor.demand.position)

        # supply exchange ratio for i = q, supply for j = p
        exchange_ratio_q = calculations.exchange_ratio(move_i,
                                                       self.supply.salience,
                                                       self.supply.power,
                                                       self.model.nbs_denominators[self.supply.issue])

        # supply exchange ratio for j, demand for i
        exchange_ratio_p = (eui + exchange_ratio_q * self.supply.salience) / self.demand.salience

        eui_check = abs(calculations.expected_utility(self, exchange_ratio_q, exchange_ratio_p))

        if abs(eui_check - eui) > 1e-10:
            raise Exception('deze moet gelijk zijn.')

        move_j = calculations.reverse_move(actor_issues=self.opposite_actor.actor_issues(),
                                           actor=self.opposite_actor,
                                           c_exchange_ratio=exchange_ratio_p)

        euj = abs(calculations.expected_utility(self.opposite_actor, exchange_ratio_p, exchange_ratio_q))

        delta_x_j_supply = abs(self.opposite_actor.supply.position - self.demand.position)

        if abs(move_j) > delta_x_j_supply:
            exchange_ratio_p_b = calculations.exchange_ratio(delta_x_j_supply,
                                                             self.opposite_actor.supply.salience,
                                                             self.opposite_actor.supply.power,
                                                             self.model.nbs_denominators[
                                                                 self.opposite_actor.supply.issue])

            exchange_ratio_q_b = abs((eui - exchange_ratio_p_b * self.demand.salience) / self.supply.salience)

            move_j_b = delta_x_j_supply
            move_i_b = calculations.reverse_move(self.actor_issues(), self, exchange_ratio_q_b)

            if abs(move_i_b) < abs(self.supply.position - self.opposite_actor.demand.position):

                euj = abs(calculations.expected_utility(self.opposite_actor, exchange_ratio_p_b, exchange_ratio_q_b))
                eui_check = abs(calculations.expected_utility(self, exchange_ratio_q_b, exchange_ratio_p_b))

                if abs(eui - eui_check) > 1e-10:
                    # print('This is not correct!')
                    raise Exception('This is not correct!')
                else:
                    move_i = move_i_b
                    move_j = move_j_b
            else:
                raise Exception('Impossible')

        if abs(eui - eui_check) > 1e-10:
            raise Exception('This is not correct!')

        if eui_max is None:
            # if they are not equal
            if not abs(euj - eui) < 1e-10:
                if (euj - eui) < 1e-10:
                    raise Exception('euj should be lager')

        if p == 0 and abs(eui - euj) > 1e-10:
            print('Not Equal Gain. {0}'.format(self.is_adjusted_by_nbs or self.opposite_actor.is_adjusted_by_nbs))

        self.eu = eui
        self.opposite_actor.eu = euj

        self.move = move_i
        self.opposite_actor.move = move_j

        if self.supply.position > self.opposite_actor.demand.position:
            self.move *= -1

        if self.opposite_actor.supply.position > self.demand.position:
            self.opposite_actor.move *= -1

        self.moves.pop()
        self.moves.append(self.move)

        self.opposite_actor.moves.pop()
        self.opposite_actor.moves.append(self.opposite_actor.move)

        self.y = self.supply.position + self.move
        self.opposite_actor.y = self.opposite_actor.supply.position + self.opposite_actor.move

        b1 = self.is_move_valid(self.move)
        b2 = self.opposite_actor.is_move_valid(self.opposite_actor.move)

        self.exchange.is_valid = b1 and b2

        self.check_nbs()
        self.opposite_actor.check_nbs()


class EqualGainExchange(base.AbstractExchange):
    actor_class = EqualGainExchangeActor

    def __init__(self, i, j, p, q, m, groups):
        super().__init__(i, j, p, q, m, groups)

    def calculate(self):
        # first we try to move j to the position of i on issue p
        # we start with the calculation for j
        self.dp = calculations.by_absolute_move(self.j.actor_issues(), self.j)
        self.dq = calculations.by_exchange_ratio(self.j, self.dp)

        self.i.move = calculations.reverse_move(self.i.actor_issues(), self.i, self.dq)
        self.j.move = abs(self.i.demand.position - self.j.supply.position)

        # if the move exceeds the interval
        if abs(self.i.move) > abs(self.j.demand.position - self.i.supply.position):
            self.dq = calculations.by_absolute_move(self.i.actor_issues(), self.i)
            self.dp = calculations.by_exchange_ratio(self.i, self.dq)

            self.i.move = abs(self.j.demand.position - self.i.supply.position)
            self.j.move = calculations.reverse_move(self.j.actor_issues(), self.j, self.dp)

        # TODO add check of NBS.
        # this check is only necessary for the smallest exchange,
        # because if the smallest exchange exceeds the limit the larger one will definitely do so

        # determine the direction of both moves
        if self.i.supply.position > self.j.demand.position:
            self.i.move *= -1

        if self.j.supply.position > self.i.demand.position:
            self.j.move *= -1

        # keep the moves in memory so we can check the direction of the actor
        self.i.moves.append(self.i.move)
        self.j.moves.append(self.j.move)

        # adjust the voting positions
        self.i.y = self.i.supply.position + self.i.move
        self.j.y = self.j.supply.position + self.j.move

        self.i.equal_gain_voting = self.i.y
        self.j.equal_gain_voting = self.j.y

        # calculate the utility gains for both actors
        eui = calculations.expected_utility(self.i, self.dq, self.dp)
        euj = calculations.expected_utility(self.j, self.dp, self.dq)

        # since this is the Equal Gain model, the gains should be equal
        if calculations.is_gain_equal(eui, euj):
            self.gain = abs(eui)

        b1 = self.i.is_move_valid(self.i.move)
        b2 = self.j.is_move_valid(self.j.move)

        self.is_valid = b1 and b2

        if self.gain < 1e-10:
            self.is_valid = False

        if self.is_valid:
            self.i.check_nbs()
            self.j.check_nbs()

            b1 = self.i.is_move_valid(self.i.move)
            b2 = self.j.is_move_valid(self.j.move)

            self.is_valid = b1 and b2
        else:
            return  # stop if its not valid

        u = random.uniform(0, 1) > 0.5
        v = random.uniform(0, 1) > 0.5

        z = decimal.Decimal(random.uniform(0, 1))

        if self.i.y > 100 or self.i.y < 0:
            print('de move van i is groter of kleiner dan 100 {0}'.format(self.i.y))
            t1 = self.i.is_move_valid(self.i.move)
        elif self.j.y > 100 or self.j.y < 0:
            print('de move van j is groter of kleiner dan 100 {0}'.format(self.j.y))
            t2 = self.j.is_move_valid(self.j.move)

        if u:  # U < 0.5:
            self.i.randomized_gain(u, v, z, self.dp, "dp")
        else:
            self.j.randomized_gain(u, v, z, self.dq, "dq")

        if self.i.y > 100 or self.i.y < 0:
            print('de move van i is groter of kleiner dan 100 {0}'.format(self.i.y))
            t1 = self.i.is_move_valid(self.i.move)
        elif self.j.y > 100 or self.j.y < 0:
            print('de move van j is groter of kleiner dan 100 {0}'.format(self.j.y))
            t2 = self.j.is_move_valid(self.j.move)

    def csv_row(self, head=False):

        if head:
            return [
                # the actors
                "actor_name",  # exchange.i.actor_name,
                "supply",  # exchange.i.supply,
                "power",
                "sal s",
                "sal d",
                "sal s/d",
                "start",
                "move",
                "voting",
                "equal gain voting",
                "demand",
                "z",
                "eu",
                "gain",
                "nbs 0",
                "nbs 1",
                "delta nbs",
                "check",
                "",
                "actor_name",  # exchange.i.actor_name,
                "supply",  # exchange.i.supply,
                "power",
                "sal s",
                "sal d",
                "sal s/d",
                "start",
                "move",
                "voting",
                "equal gain voting",
                "demand",
                "z",
                "eu",
                "gain",
                "nbs 0",
                "nbs 1",
                "delta nbs",
                "check"
            ]

        exchange = self

        delta_nbs_i = abs(exchange.i.nbs_0 - exchange.i.nbs_1)
        delta_nbs_j = abs(exchange.j.nbs_0 - exchange.j.nbs_1)

        eu_i = abs(delta_nbs_i * exchange.i.supply.salience - delta_nbs_j * exchange.i.demand.salience)
        eu_j = abs(delta_nbs_j * exchange.j.supply.salience - delta_nbs_i * exchange.j.demand.salience)

        check_i = abs(eu_i - exchange.i.eu) < 1e-10
        check_j = abs(eu_j - exchange.j.eu) < 1e-10

        return [
            # the actors
            exchange.i.actor.name,
            exchange.i.supply.issue,
            exchange.i.supply.power,
            exchange.i.supply.salience,
            exchange.i.demand.salience,
            exchange.i.supply.salience / exchange.i.demand.salience,
            exchange.i.supply.position,
            exchange.i.move,
            exchange.i.y,
            exchange.i.equal_gain_voting,
            exchange.i.opposite_actor.demand.position,
            exchange.i.z,
            exchange.i.eu,
            exchange.gain,
            exchange.i.nbs_0,
            exchange.i.nbs_1,
            delta_nbs_i,
            check_i,
            "",
            exchange.j.actor.name,
            exchange.j.supply.issue,
            exchange.j.supply.power,
            exchange.j.supply.salience,
            exchange.j.demand.salience,
            exchange.j.supply.salience / exchange.j.demand.salience,
            exchange.j.supply.position,
            exchange.j.move,
            exchange.j.y,
            exchange.j.equal_gain_voting,
            exchange.j.opposite_actor.demand.position,
            exchange.j.z,
            exchange.j.eu,
            exchange.gain,
            exchange.j.nbs_0,
            exchange.j.nbs_1,
            delta_nbs_j,
            check_j,
        ]


class EqualGainModel(base.AbstractModel):
    """
    Equal Gain implementation
    """

    """
    there can be a random component added to
    the model but this gives not equal outcomes for testing purpose
    """
    ALLOW_RANDOM = True

    def __init__(self, randomized_value=0):
        super().__init__()

        self.randomized_value = randomized_value

    def sort_exchanges(self):
        """
        The exchanges are sorted by there (equal) gain, highest first
        """
        self.exchanges.sort(key=attrgetter("gain"), reverse=True)

    def highest_gain(self):
        """
        Overrides Abstract # To sort the list in place...
        :return:
        """
        self.sort_exchanges()

        realize = self.exchanges.pop(0)

        if len(self.exchanges) > 0:

            if EqualGainModel.ALLOW_RANDOM:

                next_exchange = self.exchanges[0]

                if abs(realize.gain - next_exchange.gain) < 1e-10:
                    if random.random() >= 0.5:
                        self.exchanges.append(realize)
                        realize = self.exchanges.pop(0)
                    else:
                        self.exchanges.append(next_exchange)

        return realize

    @staticmethod
    def new_exchange_factory(i, j, p, q, model, groups):
        return EqualGainExchange(i, j, p, q, model, groups)
