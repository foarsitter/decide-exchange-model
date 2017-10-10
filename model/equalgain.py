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
        else:
            return  # stop if its not valid

        p = decimal.Decimal(self.model.randomized_value)

        if p > 0:

            eu = self.gain

            u = random.getrandbits(1)
            v = random.getrandbits(1)

            z = decimal.Decimal(random.uniform(0, 1))

            if u:  # U < 0.5:
                self.i.z = z
                self.j.z = '-'

                if v:  # V < 0.5:
                    exchange_ratio_zero_i = calculations.exchange_ratio_by_expected_utility(self.dp,
                                                                                            self.i.supply.salience,
                                                                                            self.i.demand.salience)
                    eui = p * z * (abs(calculations.expected_utility(self.i, exchange_ratio_zero_i, self.dp)) - eu) + eu
                else:
                    eui = eu - p * z * eu

                # calculate the expected utility of J
                move_i = abs(self.i.supply.position - self.i.opposite_actor.demand.position)

                # supply exchange ratio for i, demand for j
                exchange_ratio_i_supply = calculations.exchange_ratio(move_i,
                                                                      self.i.supply.salience,
                                                                      self.i.supply.power,
                                                                      self.model.nbs_denominators[self.i.supply.issue])

                # supply exchange ratio for j, demand for i
                exchange_ratio_i_demand = calculations.exchange_ratio_by_expected_utility(exchange_ratio_i_supply,
                                                                                          self.i.supply.salience,
                                                                                          self.i.demand.salience,
                                                                                          utility=eui)

                exchange_ratio_j_supply = exchange_ratio_i_demand
                exchange_ratio_j_demand = exchange_ratio_i_supply

                move_j = calculations.reverse_move(self.j.actor_issues(), self.j,
                                                   exchange_ratio_j_supply)

                delta_x_j_supply = abs(self.j.supply.position - self.j.opposite_actor.demand.position)

                euj = abs(calculations.expected_utility(self.j, exchange_ratio_j_demand, exchange_ratio_j_supply))
                eui_check = abs(calculations.expected_utility(self.i, exchange_ratio_i_supply, exchange_ratio_i_demand))

                if abs(move_j) > delta_x_j_supply:
                    exchange_ratio_j_supply = calculations.exchange_ratio(delta_x_j_supply,
                                                                          self.j.supply.salience,
                                                                          self.j.supply.power,
                                                                          self.model.nbs_denominators[
                                                                              self.j.supply.issue])

                    exchange_ratio_j_demand = calculations.by_exchange_ratio(self.j, exchange_ratio_j_supply)
                    move_j = delta_x_j_supply
                    move_i = calculations.reverse_move(self.model.actor_issues[self.i.supply.issue], self.i,
                                                       exchange_ratio_j_demand)

                    if abs(move_i) < abs(
                                    self.i.supply.position - self.i.opposite_actor.demand.position):
                        euj = abs(
                            calculations.expected_utility(self.j, exchange_ratio_j_supply, exchange_ratio_j_demand))
                        eui_check = abs(
                            calculations.expected_utility(self.i, exchange_ratio_i_supply, exchange_ratio_i_demand))
                    else:
                        raise Exception('Impossible')

                # if move_i < 0 or move_i > 100 or move_j < 0 or move_j > 100:
                #     raise Exception('Impossible')
                #
                # if self.is_valid and abs(eui_check - eui) > 1e-10:
                #     raise Exception('the gain is already calculate, should be the same {}={}'.format(eui, eui_check))

                self.i.eu = eui
                self.j.eu = euj

                self.i.move = move_i
                self.j.move = move_j

            else:
                self.j.z = z
                self.i.z = '-'

                if v:  # V < 0.5:
                    exchange_ratio_zero_j = calculations.exchange_ratio_by_expected_utility(self.dq,
                                                                                            self.j.supply.salience,
                                                                                            self.j.demand.salience)
                    euj_max = calculations.expected_utility(self.i, self.dp, exchange_ratio_zero_j)
                    euj = p * z * (euj_max - eu) + eu
                else:
                    euj = eu - p * z * eu

                # calculate the expected utility of J
                move_j = abs(self.j.supply.position - self.j.opposite_actor.demand.position)
                # supply exchange ratio for i, demand for j
                exchange_ratio_j_supply = calculations.exchange_ratio(move_j,
                                                                      self.j.supply.salience,
                                                                      self.j.supply.power,
                                                                      self.model.nbs_denominators[
                                                                          self.j.supply.issue])

                # supply exchange ratio for j, demand for i
                exchange_ratio_j_demand = calculations.exchange_ratio_by_expected_utility(exchange_ratio_j_supply,
                                                                                          self.j.supply.salience,
                                                                                          self.j.demand.salience,
                                                                                          utility=euj)

                exchange_ratio_i_supply = exchange_ratio_j_demand
                exchange_ratio_i_demand = exchange_ratio_j_supply

                move_i = calculations.reverse_move(self.model.actor_issues[self.i.supply.issue], self.i,
                                                   exchange_ratio_i_supply)

                delta_x_i_supply = abs(self.i.supply.position - self.i.opposite_actor.demand.position)

                eui = abs(calculations.expected_utility(self.i, exchange_ratio_i_demand, exchange_ratio_i_supply))
                euj_check = abs(
                    calculations.expected_utility(self.j, exchange_ratio_j_supply, exchange_ratio_j_demand))

                if abs(move_i) > delta_x_i_supply:
                    exchange_ratio_i_supply = calculations.exchange_ratio(delta_x_i_supply,
                                                                          self.i.supply.salience,
                                                                          self.i.supply.power,
                                                                          self.model.nbs_denominators[
                                                                              self.i.supply.issue])

                    exchange_ratio_i_demand = calculations.by_exchange_ratio(self.i, exchange_ratio_i_supply)
                    move_i = delta_x_i_supply
                    move_j = calculations.reverse_move(self.model.actor_issues[self.j.supply.issue], self.j,
                                                       exchange_ratio_i_demand)

                    if abs(move_j) < abs(
                                    self.j.supply.position - self.j.opposite_actor.demand.position):
                        eui = abs(
                            calculations.expected_utility(self.i, exchange_ratio_i_supply, exchange_ratio_i_demand))
                        euj_check = abs(
                            calculations.expected_utility(self.j, exchange_ratio_j_supply, exchange_ratio_j_demand))
                    else:
                        raise Exception('Impossible')

                # if move_i < 0 or move_i > 100 or move_j < 0 or move_j > 100:
                #     raise Exception('Impossible')
                #
                # if self.is_valid and abs(euj_check - euj) > 1e-10:
                #     raise Exception('the gain is already calculate, should be the same {0}-{1} {2}'.format(euj_check, euj, self.is_valid))

                self.i.eu = eui
                self.j.eu = euj

                self.i.move = move_i
                self.j.move = move_j

            if z < 1e-10:
                raise Exception('Impossible')

            if self.i.supply.position > self.j.demand.position:
                self.i.move *= -1

            if self.j.supply.position > self.i.demand.position:
                self.j.move *= -1

            self.i.moves.pop()
            self.i.moves.append(self.i.move)

            self.j.moves.pop()
            self.j.moves.append(self.j.move)

            self.i.y = self.i.supply.position + self.i.move
            self.j.y = self.j.supply.position + self.j.move

            b1 = self.i.is_move_valid(self.i.move)
            b2 = self.j.is_move_valid(self.j.move)

            self.is_valid = b1 and b2

            self.i.check_nbs()
            self.j.check_nbs()

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
                "nbs 1"]

        exchange = self

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
            exchange.j.nbs_1]


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
