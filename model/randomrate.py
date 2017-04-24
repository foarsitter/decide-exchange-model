import random
import uuid
from collections import defaultdict
from decimal import *
from operator import attrgetter
from typing import List

from model import calculations
from model.base import AbstractExchangeActor, AbstractExchange, AbstractModel, Actor, Issue


class RandomRateExchangeActor(AbstractExchangeActor):
    """
    Random Rate solution of the model.
    Where the expected utility in de Equal Gain solution are equal, the utility here is calculated on a random exchange ratio.
    """

    def __init__(self, model_ref: 'AbstractExchange', actor: Actor, demand_issue: Issue, supply_issue: Issue, group):
        """
        Constructor, needs to call super()
        :param model_ref:
        :param actor:
        :param demand_issue:
        :param supply_issue:
        :param group:
        """
        super().__init__(model_ref, actor, demand_issue, supply_issue, group)
        self.eu = 0
        self.exchange = None

    def __str__(self):
        return "{1} {2} {3:.1f} {4:.1f} ({5:.1f}) {0:.10f} ".format(self.eu, self.actor_name, self.supply_issue, self.x, self.y,
                                                  self.opposite_actor.x_demand)

    def recalculate(self, delta_eu, increase, recursive=True):

        # we should not need the opposite actor, because the move isnt effecting the other actors position
        # opposite = self.exchange.opposite_actor

        delta_O = delta_eu / self.s

        # determine in which direction the nbs is moving

        if self.nbs_1 < self.nbs_0:
            delta_O *= -1

        # we can also decrease the shift.
        delta_O = delta_O if increase else delta_O * -1

        self.adjust_position_by_outcome(delta_O, recursive=recursive)

    def adjust_position_by_outcome(self, delta_O, recursive=True):
        new_outcome = self.nbs_1 + delta_O  # we have to use nbs_1 here, because it is an incremental shift.

        position = calculations.position_by_nbs(actor_issues=self.exchange.model.actor_issues[self.supply_issue],
                                                exchange_actor=self,
                                                nbs=new_outcome,
                                                denominator=self.exchange.model.nbs_denominators[self.supply_issue])

        if delta_O < 0 and position < self.opposite_actor.x_demand or delta_O > 0 and position > self.opposite_actor.x_demand:

            if not recursive:
                print('the gap is to small to close')
                self.exchange.model.remove_exchange_by_key(self.exchange.key)
            else:
                position = self.opposite_actor.x_demand

                adjusted_nbs = calculations.adjusted_nbs(actor_issues=self.exchange.model.actor_issues[self.supply_issue],
                                                         updates=self.exchange.updates,
                                                         actor=self.actor_name,
                                                         new_position=position,
                                                         denominator=self.exchange.model.nbs_denominators[self.supply_issue])

                new_outcome = adjusted_nbs
                delta_O_consumed = abs(new_outcome - self.nbs_1) - delta_O
                delta_O_left = delta_O - delta_O_consumed
                delta_O = delta_O_consumed
                self.opposite_actor.recalculate(delta_O_left, increase=False, recursive=False)

        self.moves.pop()
        self.moves.append(position)
        self.y = position
        self.nbs_1 = new_outcome
        # self.adjust_utility(delta_O)

    def adjust_utility(self, delta_O):

        self.eu += abs(delta_O) * self.s
        self.opposite_actor.eu -= delta_O


class RandomRateExchange(AbstractExchange):
    """
    An exchange for the random rate model
    """

    actor_class = RandomRateExchangeActor
    """ For the factory, so the Abstract know's which type he has to create  """

    def __init__(self, i, j, p, q, m, groups):
        super().__init__(i, j, p, q, m, groups)

        self.i.exchange = self
        self.j.exchange = self
        self.key = uuid.uuid4()

    def to_list(self):
        return [self.i, self.j]

    def calculate(self):
        # first we try to move j to the position of i on issue p
        # we start with the calculation for j

        a = float(self.j.s_demand / self.i.s)
        b = float(self.i.s_demand / self.j.s)

        if b > a:
            a, b = b, a

        self.dp = Decimal(random.uniform(a, b))
        self.dq = Decimal(random.uniform(a, b))

        self.i.move = calculations.reverse_move(self.model.actor_issues[self.i.supply_issue], self.i, self.dq)
        self.j.move = abs(self.i.x_demand - self.j.x)

        if abs(self.i.move) > abs(self.j.x_demand - self.i.x):
            self.dq = calculations.by_absolute_move(self.model.actor_issues[self.i.supply_issue], self.i)
            self.dp = calculations.by_exchange_ratio(self.i, self.dq)

            self.i.move = abs(self.j.x_demand - self.i.x)
            self.j.move = calculations.reverse_move(self.model.actor_issues[self.j.supply_issue], self.j, self.dp)

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

    def __str__(self):
        return "{0}, {1}".format(str(self.i), str(self.j))

    def __getitem__(self, item):
        if item == self.i.actor_name:
            return self.i
        elif item == self.j.actor_name:
            return self.j

        raise Exception("Actor {0} not in exchange".format(item))


class RandomRateModel(AbstractModel):
    """
    The Random Rate implementation
    """

    def _get_sorted_exchange_actor_list(self):
        all_exchange_actors = []
        for exchange in self.exchanges:  # type: RandomRateExchange
            all_exchange_actors.append(exchange.i)
            all_exchange_actors.append(exchange.j)

        all_exchange_actors.sort(key=attrgetter("eu"), reverse=True)

        return all_exchange_actors

    def sort_exchanges(self):
        print('sort_exchanges on RandomRateModel is unused')

    def highest_gain(self):

        exchange_actors = self._get_sorted_exchange_actor_list()

        # place each ExchangeActor in a dict where al his exchanges are ordered by the utility
        exchange_actors_by_gain = defaultdict(lambda: defaultdict(list))

        # sort all the gains by actor in a dict
        # so we can sort this DESC
        # now its possible to check which gain is the next in line to be lowered.
        # this is always the second element, because the first element is the highest gain.
        exchange_actors_by_actor = defaultdict(list)

        highest = {}
        exchange_by_key = defaultdict()

        highest_exchanges = []

        for exchange_actor in exchange_actors:  # type: RandomRateExchangeActor

            if exchange_actor.actor_name not in highest:
                highest[exchange_actor.actor_name] = exchange_actor

                if exchange_actor.exchange.key not in exchange_by_key:
                    exchange_by_key[exchange_actor.exchange.key] = exchange_actor.exchange
                else:
                    highest_exchanges.append(exchange_actor.exchange)

            exchange_actors_by_actor[exchange_actor.actor_name].append(exchange_actor.eu)
            exchange_actors_by_gain[exchange_actor.actor_name][exchange_actor.eu].append(exchange_actor)

        if len(highest_exchanges) > 0:
            #  we have exchanges that are for both actors the highest one

            # execute this exchange
            # remove it from self.exchanges
            # and start over with this function

            return_value = highest_exchanges[0]  # TODO STOKMAN alle ruilen uitvoeren?

            self.remove_exchange_by_key(return_value.key)
            # print('Valid move {0}'.format(return_value))
            return return_value
        else:
            # we have the highest and second highest.
            # highest[key] needs to be lowered to second[key]

            for actor_name, values in exchange_actors_by_actor.items():
                if len(values) > 1:
                    highest = values[0]
                    second_highest = self._find_first_element_not_equal(values)

                    if second_highest is not None:

                        delta_eu = highest - second_highest

                        highest_exchanges = exchange_actors_by_gain[actor_name][highest]

                        for highest_exchange_actor in highest_exchanges:

                            if delta_eu < 0:
                                print('delta eu cannot be lower than zero')

                            highest_exchange = highest_exchange_actor.exchange  # type: RandomRateExchange
                            opposite_actor_name = highest_exchange_actor.opposite_actor.actor_name

                            if highest_exchange[actor_name].y == highest_exchange[opposite_actor_name].x_demand:
                                highest_exchange[opposite_actor_name].recalculate(delta_eu, increase=True)
                            elif highest_exchange[opposite_actor_name].y == highest_exchange[actor_name].x_demand:
                                highest_exchange[actor_name].recalculate(delta_eu, increase=False)
                            else:
                                highest_exchange[opposite_actor_name].recalculate(delta_eu, increase=True)

                            highest_exchange[opposite_actor_name].adjust_utility(delta_eu)

                            print(highest_exchange_actor)

                    return self.highest_gain()

        # second = {}
        # third = {}
        # fourth = {}

        # # diagnostic
        # for actor in exchange_actors_by_gain.keys():
        #     for gain in exchange_actors_by_gain[actor].keys():
        #         if len(exchange_actors_by_gain[actor][gain]) > 1:
        #             print('There are equal gains!')

    def _lower_highest_gain(self, highest, second):
        """
        Lowers the highest gain to de second gain 
        :param highest: 
        :param second: 
        :return: 
        """

        for actor_name, highest_exchange_actor in highest.items():  # type: RandomRateExchangeActor

                opposite_actor_name = highest_exchange_actor.opposite_actor.actor_name

                second_exchange_actor = second.get(actor_name, None)  # type: RandomRateExchangeActor

                if second_exchange_actor:
                    delta_eu = highest_exchange_actor.eu - second_exchange_actor.eu

                    if delta_eu < 0:
                        print('delta eu cannot be lower than zero')

                    highest_exchange = highest_exchange_actor.exchange  # type: RandomRateExchange

                    if highest_exchange[actor_name].y == highest_exchange[opposite_actor_name].x_demand:
                        highest_exchange[opposite_actor_name].recalculate(delta_eu, increase=True)
                    elif highest_exchange[opposite_actor_name].y == highest_exchange[actor_name].x_demand:
                        highest_exchange[actor_name].recalculate(delta_eu, increase=False)
                    else:
                        highest_exchange[opposite_actor_name].recalculate(delta_eu, increase=True)

                    highest_exchange[opposite_actor_name].adjust_utility(delta_eu)

    @staticmethod
    def new_exchange_factory(i, j, p, q, model, groups):
        """
        Creates a new instance of the RandomRateExchange
        """
        return RandomRateExchange(i, j, p, q, model, groups)

    def remove_exchange_by_key(self, key):

        for __, exchange in enumerate(self.exchanges):

            if key == exchange.key:
                del self.exchanges[__]
                return

        raise Exception('item not in list')

    def _find_first_element_not_equal(self, exchange_utility_list: List[Decimal]):

        previous_value = exchange_utility_list.pop(0)
        for value in exchange_utility_list:
            if abs(value - previous_value) > 0:
                return value

