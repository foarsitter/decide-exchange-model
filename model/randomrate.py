import random
from decimal import *
from operator import attrgetter

from model import calculations
from model.base import AbstractExchangeActor, AbstractExchange, AbstractModel


class RandomRateExchangeActor(AbstractExchangeActor):
    """
    Random Rate solution of the model.
    Where the expected utility in de Equal Gain solution are equal, the utility here is calculated on a random exchange ratio.
    """

    def __init__(self, model, actor_name, demand, supply, group):
        """
        Constructor, needs to call super()

        :param model:
        :param actor_name:
        :param demand:
        :param supply:
        :param group:
        """
        super(RandomRateExchangeActor, self).__init__(model, actor_name, demand, supply, group)

        self.eu = 0
        self.is_highest_gain = False


class RandomRateExchange(AbstractExchange):
    """
    An exchange for the random rate model
    """

    actor_class = RandomRateExchangeActor
    """ For the factory, so the Abstract know's which type he has to create  """

    def __init__(self, i, j, p, q, m, groups):
        super(RandomRateExchange, self).__init__(i, j, p, q, m, groups)
        self.highest_gain = 0
        self.lowest_gain = 0
        self.total_gain = 0
        self.is_highest_highest = False
        self.is_lowest_highest = False

    def calculate(self):
        # TODO REWRITE
        # smaller functions
        # less repeating

        # first we try to move j to the position of i on issue p
        # we start with the calculation for j

        a = float(self.j.s_demand / self.i.s)
        b = float(self.i.s_demand / self.j.s)

        if b > a:
            a, b = b, a

        self.dp = Decimal(random.uniform(a, b))
        self.dq = Decimal(random.uniform(a, b))

        self.i.move = calculations.reverse_move(self.model.ActorIssues[self.i.supply], self.i, self.dq)
        self.j.move = abs(self.i.x_demand - self.j.x)

        if abs(self.i.move) > abs(self.j.x_demand - self.i.x):
            self.dq = calculations.by_absolute_move(self.model.ActorIssues[self.i.supply], self.i)
            self.dp = calculations.by_exchange_ratio(self.i, self.dq)

            self.i.move = abs(self.j.x_demand - self.i.x)
            self.j.move = calculations.reverse_move(self.model.ActorIssues[self.j.supply], self.j, self.dp)

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

        self.i.eu = abs(calculations.expected_utility(self.i, self.dq, self.dp))
        self.j.eu = abs(calculations.expected_utility(self.j, self.dp, self.dq))

        b1 = self.i.is_move_valid(self.i.move)
        b2 = self.j.is_move_valid(self.j.move)

        self.is_valid = b1 and b2

        if self.is_valid:  # TODO and self.re_calc:

            self.check_nbs_j()
            self.check_nbs_i()

        if self.i.eu > self.j.eu:
            self.highest_gain = self.i.eu
            self.lowest_gain = self.j.eu
        else:
            self.highest_gain = self.j.eu
            self.lowest_gain = self.i.eu

        self.total_gain = self.i.eu + self.j.eu


class RandomRateModel(AbstractModel):
    """
    The Random Rate implementation
    """

    @staticmethod
    def new_exchange_factory(i, j, p, q, model, groups):
        """
        Creates a new instance of the RandomRateExchange
        """
        return RandomRateExchange(i, j, p, q, model, groups)

    def sort_exchanges(self):

        """
        In the Random Rate solution the list is sorted on booleans.
        Each actor can have a bool true for the highest gain
        Each exchange can have a bool true for both highest gains are highest.
        We are especially interested in those exchanges where both actors expect to get there highest gain.
        """
        highest_gains = dict()
        highest_gain_exchange = dict()

        for actor in self.Actors:
            highest_gains[actor] = 0

        for exchange in self.Exchanges:

            if exchange.i.eu > highest_gains[exchange.i.actor_name]:
                highest_gains[exchange.i.actor_name] = exchange.i.eu
                highest_gain_exchange[exchange.i.actor_name] = exchange.i

            if exchange.j.eu > highest_gains[exchange.j.actor_name]:
                highest_gains[exchange.j.actor_name] = exchange.j.eu
                highest_gain_exchange[exchange.j.actor_name] = exchange.j

        for exchange in highest_gain_exchange.values():
            exchange.is_highest_gain = True

        for exchange in self.Exchanges:

            if exchange.i.is_highest_gain:
                if exchange.highest_gain == exchange.i.eu:
                    exchange.is_highest_highest = True
                else:
                    exchange.is_lowest_highest = True

            if exchange.j.is_highest_gain:
                if exchange.highest_gain == exchange.j.eu:
                    exchange.is_highest_highest = True
                else:
                    exchange.is_lowest_highest = True

        self.Exchanges.sort(
            key=attrgetter("is_highest_highest", "is_lowest_highest", "highest_gain", "lowest_gain"),
            reverse=True)

    def highest_gain(self):

        """
        Returns the exchange where **both** actors expect the highest gain.
        In most of the cases there is only one actor of an exchange expecting the highest gain.
        These need to be re-calculated in _recalc_hihgest_
        """
        self.sort_exchanges()

        highest = self.Exchanges[0]

        # proceed or recalc
        if highest.i.is_highest_gain and highest.j.is_highest_gain:
            return highest
        else:
            return self._recalculate_highest()

    def _recalculate_highest(self):
        """
        This method calculates the combinations of each highest gain and his second highest gain.
        The gain of the highest exchange gets altered to the gain of the second.
        Therefore the highest exchange results in a lower gain for the actor,
        which is the result of a higher shift towards the other actor or an lower demand.

        :return:
        """
        self.sort_exchanges()

        highest = []
        left_over = []

        # select the exchanges where either i or j has the highest gain
        for exchange in self.Exchanges:
            if exchange.i.is_highest_gain or exchange.j.is_highest_gain:
                highest.append(exchange)
            else:
                left_over.append(exchange)  # if there is no highest_gain flag, we need them later

        # init the buckets
        second_highest_gains = dict()
        second_highest_gain_exchange = dict()

        for actor in self.Actors:
            second_highest_gains[actor] = 0

        # select the exchange where i or j has his highest gain
        for exchange in left_over:

            if exchange.i.eu > second_highest_gains[exchange.i.actor_name]:
                second_highest_gains[exchange.i.actor_name] = exchange.i.eu
                second_highest_gain_exchange[exchange.i.actor_name] = exchange.i

            if exchange.j.eu > second_highest_gains[exchange.j.actor_name]:
                second_highest_gains[exchange.j.actor_name] = exchange.j.eu
                second_highest_gain_exchange[exchange.j.actor_name] = exchange.j

        # for each highest gain lower the gain of the actor to his second highest exchange
        for exchange_pair in highest:

            if exchange_pair.i.is_highest_gain:
                eu = second_highest_gain_exchange[exchange_pair.i.actor_name].eu

                delta_eu = exchange_pair.i.eu - eu

                if exchange_pair.i.y == exchange_pair.j.x_demand:  # i moves to j completely on q

                    delta_nbs = delta_eu / exchange_pair.j.s

                    factor = 1 if exchange_pair.j.move > 0 else -1

                    nbs_adjusted = exchange_pair.j.nbs_1 + (delta_nbs * exchange_pair.j.s_demand) * factor
                    actor = exchange_pair.j

                    position = calculations.position_by_nbs(self.ActorIssues[actor.supply],
                                                            exchange_actor=actor,
                                                            nbs=nbs_adjusted,
                                                            denominator=self.nbs_denominators[actor.supply])

                    exchange_pair.j.moves.append(exchange_pair.j.x - position)

                    exchange_pair.j.x = position

                elif exchange_pair.j.y == exchange_pair.i.x_demand:  # j moves to i completely on p, so there is room on i to j.

                    delta_nbs = (delta_eu / exchange_pair.i.s)

                    factor = 1 if exchange_pair.i.move > 0 else -1

                    nbs_adjusted = exchange_pair.i.nbs_1 + (delta_nbs * factor)

                    actor = exchange_pair.i

                    position = calculations.position_by_nbs(self.ActorIssues[actor.supply],
                                                            exchange_actor=actor,
                                                            nbs=nbs_adjusted,
                                                            denominator=self.nbs_denominators[actor.supply])

                    exchange_pair.i.moves.append(exchange_pair.i.x - position)

                    exchange_pair.i.x = position

                else:
                    # TODO is there a third option that both exchanges are possible?
                    pass

                exchange_pair.i.eu -= delta_eu
                exchange_pair.j.eu += delta_eu

                if abs(exchange_pair.i.eu - eu) > 1e-10:
                    raise Exception("Should be equal")
            elif exchange_pair.j.is_highest_gain:
                eu = second_highest_gain_exchange[exchange_pair.j.actor_name].eu

                delta_eu = exchange_pair.j.eu - eu

                if exchange_pair.i.y == exchange_pair.j.x_demand:  # i moves to j completely on q

                    delta_nbs = delta_eu / exchange_pair.j.s

                    factor = 1 if exchange_pair.j.move > 0 else -1

                    nbs_adjusted = exchange_pair.j.nbs_1 + (delta_nbs * exchange_pair.j.s_demand) * factor
                    actor = exchange_pair.j

                    position = calculations.position_by_nbs(self.ActorIssues[actor.supply],
                                                            exchange_actor=actor,
                                                            nbs=nbs_adjusted,
                                                            denominator=self.nbs_denominators[actor.supply])

                    exchange_pair.j.moves.append(exchange_pair.j.x - position)

                    exchange_pair.j.x = position

                elif exchange_pair.j.y == exchange_pair.i.x_demand:  # j moves to i completely on p, so there is room for i.

                    delta_nbs = (delta_eu / exchange_pair.i.s)

                    factor = 1 if exchange_pair.j.move > 0 else -1

                    nbs_adjusted = exchange_pair.i.nbs_1 + (delta_nbs * factor)
                    actor = exchange_pair.i

                    position = calculations.position_by_nbs(self.ActorIssues[actor.supply],
                                                            exchange_actor=actor,
                                                            nbs=nbs_adjusted,
                                                            denominator=self.nbs_denominators[actor.supply])

                    exchange_pair.i.moves.append(exchange_pair.i.x - position)

                    exchange_pair.i.x = position

                else:
                    # TODO is there a third option that both exchanges are possible?
                    pass

                exchange_pair.i.eu -= delta_eu
                exchange_pair.j.eu += delta_eu


                # if abs(exchange_pair.i.eu - eu) > 1e-10:
                #     raise Exception("Should be equal")

        exchange_pair.i.is_highest_gain = False
        exchange_pair.j.is_highest_gain = False
        exchange_pair.is_highest_highest = False
        exchange_pair.is_lowest_highest = False

        return self.highest_gain()





