import random
from operator import attrgetter

import decimal

from . import base
from . import calculations


class EqualGainExchangeActor(base.AbstractExchangeActor):
    """
    AbstractExchangeActor is the same actor...
    """
    pass


class EqualGainExchange(base.AbstractExchange):

    def calculate(self):
        # TODO REWRITE
        # smaller functions
        # less repeating

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

        if self.is_valid:  # TODO and self.re_calc:

            self.i.check_nbs()
            self.j.check_nbs()

        p = decimal.Decimal(0)

        # if self.i.supply.position > self.i.y:
        #     if self.j.demand.position > self.i.y:
        #         print('I cannot move beyond J')

        # if self.is_valid and p > 0:
        #
        #     eu = self.gain
        #
        #     U = decimal.Decimal(random.uniform(0, 1))
        #     V = decimal.Decimal(random.uniform(0, 1))
        #     Z = decimal.Decimal(random.uniform(0, 1))
        #
        #     if U < 0.5:
        #         if V < 0.5:
        #             exchange_ratio_zero_i = calculations.exchange_ratio_by_expected_utility(self.dp,
        #                                                                                     self.i.supply.salience,
        #                                                                                     self.i.demand.salience)
        #             eui = p * Z * (abs(calculations.expected_utility(self.i, exchange_ratio_zero_i, self.dp)) - eu) + eu
        #         else:
        #             eui = eu - p * Z * eu
        #
        #         # calculate the expected utility of J
        #
        #         move_i = abs(self.i.supply.position - self.i.opposite_actor.demand.position)
        #         # supply exchange ratio for i, demand for j
        #         exchange_ratio_i_supply = calculations.exchange_ratio(move_i,
        #                                                               self.i.supply.salience,
        #                                                               self.i.supply.power,
        #                                                               self.model.nbs_denominators[self.i.supply.issue])
        #
        #         # supply exchange ratio for j, demand for i
        #         exchange_ratio_i_demand = calculations.exchange_ratio_by_expected_utility(exchange_ratio_i_supply,
        #                                                                                   self.i.supply.salience,
        #                                                                                   self.i.demand.salience,
        #                                                                                   utility=eui)
        #
        #         exchange_ratio_j_supply = exchange_ratio_i_demand
        #         exchange_ratio_j_demand = exchange_ratio_i_supply
        #
        #         move_j = calculations.reverse_move(self.j.actor_issues(), self.j, exchange_ratio_j_supply)
        #
        #         delta_x_j_supply = abs(self.j.supply.position - self.j.opposite_actor.demand.position)
        #
        #         euj = abs(calculations.expected_utility(self.j, exchange_ratio_j_demand, exchange_ratio_j_supply))
        #         eui_check = abs(calculations.expected_utility(self.i, exchange_ratio_i_supply, exchange_ratio_i_demand))
        #
        #         if abs(move_j) > delta_x_j_supply:
        #             exchange_ratio_j_supply = calculations.exchange_ratio(delta_x_j_supply,
        #                                                                   self.j.supply.salience,
        #                                                                   self.j.supply.power,
        #                                                                   self.model.nbs_denominators[
        #                                                                       self.j.supply.issue])
        #
        #             exchange_ratio_j_demand = calculations.by_exchange_ratio(self.j, exchange_ratio_j_supply)
        #
        #             move_i = calculations.reverse_move(self.i.actor_issues(), self.i, exchange_ratio_j_demand)
        #
        #             if abs(move_i) < abs(self.i.supply.position - self.i.opposite_actor.demand.position):  # TODO remove extra check, since it will never occur
        #                 euj = abs(calculations.expected_utility(self.j, exchange_ratio_j_supply, exchange_ratio_j_demand))
        #                 eui_check = abs(calculations.expected_utility(self.i, exchange_ratio_i_supply, exchange_ratio_i_demand))
        #             else:
        #                 raise Exception('Impossible')
        #         else:
        #             pass  # proceed with exchange
        #
        #         if abs(eui_check - eui) > 1e-10:
        #             raise Exception('the gain is already calculate, should be the same')
        #
        #         self.i.eu = eui
        #         self.j.eu = euj
        #
        #         self.i.move = move_i
        #         self.j.move = move_j
        #         print('h')
        #     else:
        #         if V < 0.5:
        #             exchange_ratio_zero_j = calculations.exchange_ratio_by_expected_utility(self.dq,
        #                                                                                     self.j.supply.salience,
        #                                                                                     self.j.demand.salience)
        #             euj_max = calculations.expected_utility(self.i, self.dp, exchange_ratio_zero_j)
        #             euj = p * Z * (euj_max - eu) + eu
        #         else:
        #             euj = eu - p * Z * eu
        #
        #         supply_actor = self.j
        #         new_gain = euj
        #
        #         delta_x = abs(supply_actor.supply.position - supply_actor.opposite_actor.demand.position)
        #         # supply exchange ratio for i, demand for j
        #         exchange_ratio = calculations.exchange_ratio(delta_x, supply_actor.supply.salience,
        #                                                      supply_actor.supply.power,
        #                                                      self.model.nbs_denominators[supply_actor.supply.issue])
        #
        #         # supply exchange ratio for j, demand for i
        #         dq = calculations.exchange_ratio_by_expected_utility(exchange_ratio, supply_actor.supply.salience,
        #                                                              supply_actor.demand.salience, utility=new_gain)
        #
        #         euj = calculations.expected_utility(supply_actor.opposite_actor, dq, exchange_ratio)
        #     print(euj)

    def csv_row(self, head=False):

        if head:
            return [
                # the actors
                "actor_name",  # exchange.i.actor_name,
                "supply",  # exchange.i.supply,
                "power",
                "sal s/d",
                "preference",
                "start",
                "move",
                "voting",
                "demand",
                "gain",
                "",
                "actor_name",  # exchange.i.actor_name,
                "supply",  # exchange.i.supply,
                "power",
                "sal s/d",
                "preference",
                "start",
                "move",
                "voting",
                "demand",
                "gain"]

        exchange = self

        return [
            # the actors
            exchange.i.actor.name,
            exchange.i.supply.issue,
            exchange.i.supply.power,
            exchange.i.supply.salience / exchange.i.demand.salience,
            "-",
            exchange.i.supply.position,
            exchange.i.move,
            exchange.i.y,
            exchange.i.opposite_actor.demand.position,
            exchange.gain,
            "",
            exchange.j.actor.name,
            exchange.j.supply.issue,
            exchange.j.supply.power,
            exchange.j.supply.salience / exchange.j.demand.salience,
            "-",
            exchange.j.supply.position,
            exchange.j.move,
            exchange.j.y,
            exchange.j.opposite_actor.demand.position,
            exchange.gain]


class EqualGainModel(base.AbstractModel):
    """
    Equal Gain implementation
    """

    ALLOW_RANDOM = True  # there can be a random component added tot the model but this gives not equal outcomes for testing purpose

    def sort_exchanges(self):
        """
        Overrides Abstract
        """
        self.exchanges.sort(key=attrgetter("gain"), reverse=True)  # .sort(key=lambda x: x.count, reverse=True)

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
