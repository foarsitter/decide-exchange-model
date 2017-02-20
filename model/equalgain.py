from operator import attrgetter
from random import random

from model import calculations
from model.base import AbstractModel, AbstractExchange, AbstractExchangeActor


class EqualGainExchangeActor(AbstractExchangeActor):
    def __init__(self, model, actor_name, demand, supply, group):
        super.__init__(model, actor_name, demand, supply, group)


class EqualGainExchange(AbstractExchange):

    def calculate(self):
        # TODO REWRITE
        # smaller functions
        # less repeating

        # first we try to move j to the position of i on issue p
        # we start with the calculation for j
        self.dp = calculations.by_absolute_move(self.model.ActorIssues[self.j.supply_issue], self.j)
        self.dq = calculations.by_exchange_ratio(self.j, self.dp)

        self.i.move = calculations.reverse_move(self.model.ActorIssues[self.i.supply_issue], self.i, self.dq)
        self.j.move = abs(self.i.x_demand - self.j.x)

        if abs(self.i.move) > abs(self.j.x_demand - self.i.x):
            self.dq = calculations.by_absolute_move(self.model.ActorIssues[self.i.supply_issue], self.i)
            self.dp = calculations.by_exchange_ratio(self.i, self.dq)

            self.i.move = abs(self.j.x_demand - self.i.x)
            self.j.move = calculations.reverse_move(self.model.ActorIssues[self.j.supply_issue], self.j, self.dp)

        # TODO add check of NBS.
        # this check is only necessary for the smallest exchange,
        # because if the smallest exchange exceeds the limit the larger one will definitely do so

        if self.i.x > self.j.x_demand:
            self.i.move *= -1

        if self.j.x > self.i.x_demand:
            self.j.move *= -1

        self.i.moves.append(self.i.move)
        self.j.moves.append(self.j.move)

        self.i.y = self.i.x + self.i.move
        self.j.y = self.j.x + self.j.move

        eui = calculations.expected_utility(self.i, self.dq, self.dp)
        euj = calculations.expected_utility(self.j, self.dp, self.dq)

        if abs(eui - euj) > 0.0001:
            raise Exception("Expected equal gain")
        else:
            self.gain = abs(eui)

        b1 = self.i.is_move_valid(self.i.move)
        b2 = self.j.is_move_valid(self.j.move)

        self.is_valid = b1 and b2

        if self.gain < 1e-10:
            self.is_valid = False

        if self.is_valid:  # TODO and self.re_calc:

            self.check_nbs_j()
            self.check_nbs_i()


class EqualGainModel(AbstractModel):
    """
    Equal Gain implementation
    """

    ALLOW_RANDOM = True  # there can be a random component added tot the model but this gives not equal outcomes for testing purpose

    def sort_exchanges(self):
        """
        Overrides Abstract
        """
        self.Exchanges.sort(key=attrgetter("gain"), reverse=True)  # .sort(key=lambda x: x.count, reverse=True)

    def highest_gain(self):
        """
        Overrides Abstract # To sort the list in place...
        :return:
        """
        self.sort_exchanges()

        realize = self.Exchanges.pop(0)

        if len(self.Exchanges) > 0:

            if EqualGainModel.ALLOW_RANDOM:

                next_exchange = self.Exchanges[0]

                if abs(realize.gain - next_exchange.gain) < 1e-10:
                    if random() >= 0.5:
                        self.Exchanges.append(realize)
                        realize = self.Exchanges.pop(0)
                    else:
                        self.Exchanges.append(next_exchange)

        return realize

    def new_exchange_factory(self, i, j, p, q, model, groups):
        return EqualGainExchange(i, j, p, q, model, groups)
