import logging
import random
import uuid
from collections import defaultdict
from decimal import *
from operator import attrgetter
from typing import List

from . import base
from . import calculations


class RandomRateExchangeActor(base.AbstractExchangeActor):
    """
    Random Rate solution of the model.
    Where the expected utility in de Equal Gain solution are equal,
    the utility here is calculated on a random exchange ratio.
    """

    def __str__(self):
        return "{1} {2} {3:.1f} {4:.1f} ({5:.1f}) {0:.10f} ".format(
            self.eu,
            self.actor.name,
            self.supply.issue,
            self.supply.position,
            self.y,
            self.opposite_actor.demand.position,
        )

    def recalculate(self, delta_eu, increase):

        # we should not need the opposite actor, because the move isn't effecting the other actors position
        # opposite = self.exchange.opposite_actor

        delta_o = delta_eu / self.supply.salience

        # determine in which direction the nbs is moving

        if self.nbs_1 < self.nbs_0:
            delta_o *= -1

        # we can also decrease the shift.
        delta_o = delta_o if increase else delta_o * -1

        self.adjust_position_by_outcome(delta_o, increase=increase)

    def adjust_position_by_outcome(self, delta_o, increase):
        new_outcome = (
            self.nbs_1 + delta_o
        )  # we have to use nbs_1 here, because it is an incremental shift.

        position = calculations.position_by_nbs(
            actor_issues=self.exchange.model.actor_issues[self.supply.issue],
            exchange_actor=self,
            nbs=new_outcome,
            denominator=self.exchange.model.nbs_denominators[self.supply.issue],
        )

        if increase and (
            delta_o < 0
            and position < self.opposite_actor.demand.position
            or delta_o > 0
            and position > self.opposite_actor.demand.position
        ):
            position = self.opposite_actor.demand.position

            adjusted_nbs = calculations.adjusted_nbs(
                actor_issues=self.exchange.model.actor_issues[self.supply.issue],
                updates=self.exchange.updates,
                actor=self.actor,
                new_position=position,
                denominator=self.exchange.model.nbs_denominators[self.supply.issue],
            )

            new_outcome = adjusted_nbs
            delta_o_consumed = abs(new_outcome - self.nbs_1) - delta_o
            delta_o_left = delta_o - delta_o_consumed

            self.opposite_actor.recalculate(delta_o_left, increase=False)

        previous_move = self.moves.pop()

        # calculate the move in the right direction
        if previous_move < 0:
            move = abs(self.supply.position - position) * -1
        else:
            move = abs(self.supply.position - position)

        self.moves.append(move)
        self.exchange.is_valid = self.is_move_valid(move)
        if self.exchange.is_valid:
            self.y = position
            if self.exchange.i.y > 100 or self.exchange.j.y > 100:
                self.exchange.is_valid = False
            if self.exchange.i.y < 0 or self.exchange.j.y < 0:
                self.exchange.is_valid = False
            self.nbs_1 = new_outcome

    def adjust_utility(self, delta_o):

        self.eu += abs(delta_o) * self.supply.salience
        self.opposite_actor.eu -= delta_o


class RandomRateExchange(base.AbstractExchange):
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

        if not self.re_calc:
            a = float(self.j.s_demand / self.i.s)
            b = float(self.i.s_demand / self.j.s)

            if b > a:
                a, b = b, a

            self.dp = Decimal(random.uniform(a, b))
            self.dq = Decimal(random.uniform(a, b))

        self.i.move = calculations.reverse_move(
            self.model.actor_issues[self.i.supply_issue], self.i, self.dq
        )
        self.j.move = abs(self.i.x_demand - self.j.x)

        if abs(self.i.move) > abs(self.j.x_demand - self.i.x):
            self.dq = calculations.by_absolute_move(
                self.model.actor_issues[self.i.supply_issue], self.i
            )
            self.dp = calculations.by_exchange_ratio(self.i, self.dq)

            self.i.move = abs(self.j.x_demand - self.i.x)
            self.j.move = calculations.reverse_move(
                self.model.actor_issues[self.j.supply_issue], self.j, self.dp
            )

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

        if self.is_valid:
            self.i.check_nbs()
            self.j.check_nbs()

    def __str__(self):
        return "{0}, {1}".format(str(self.i), str(self.j))

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        if item == self.i.actor_name:
            return self.i
        elif item == self.j.actor_name:
            return self.j

        raise Exception("Actor {0} not in exchange".format(item))

    def csv_row(self, head=False):

        if head:
            return [
                # the actors
                "actor",
                "issue",
                "power",
                "sal s/d",
                "start",
                "move",
                "voting",
                "demand",
                "gain",
                "exchange ratio",
                "",
                "actor",
                "issue",
                "power",
                "sal s/d",
                "start",
                "move",
                "voting",
                "demand",
                "gain",
                "exchange ratio",
            ]

        exchange = self

        return [
            # the actors
            exchange.i.actor_name,
            exchange.i.supply_issue,
            exchange.i.c,
            exchange.i.s / exchange.i.s_demand,
            exchange.i.x,
            exchange.i.move,
            exchange.i.y,
            exchange.i.opposite_actor.x_demand,
            exchange.i.eu,
            exchange.dp,
            "",
            exchange.j.actor_name,
            exchange.j.supply_issue,
            exchange.j.c,
            exchange.j.s / exchange.j.s_demand,
            exchange.j.x,
            exchange.j.move,
            exchange.j.y,
            exchange.j.opposite_actor.x_demand,
            exchange.j.eu,
            exchange.dq,
        ]


class RandomRateModel(base.AbstractModel):
    """
    The Random Rate implementation
    """

    def __init__(self):
        super().__init__()
        self.model_name = "random"

    def _get_sorted_exchange_actor_list(self):
        all_exchange_actors = []
        for exchange in self.exchanges:  # type: RandomRateExchange

            if exchange.is_valid:
                all_exchange_actors.append(exchange.i)
                all_exchange_actors.append(exchange.j)

        all_exchange_actors.sort(key=attrgetter("eu"), reverse=True)

        return all_exchange_actors

    def sort_exchanges(self):
        pass

    def highest_gain(self):

        deadlock = defaultdict(int)

        while len(self.exchanges) > 0:

            exchange_actors = self._get_sorted_exchange_actor_list()

            # place each ExchangeActor in a dict where al his exchanges are ordered by the utility
            exchange_actors_by_gain = defaultdict(lambda: defaultdict(list))

            # sort all the gains by actor in a dict
            # so we can sort this DESC
            # now its possible to check which gain is the next in line to be lowered.
            # this is always the second element, because the first element is the highest gain.
            exchange_actors_by_actor = defaultdict(list)

            highest_actors = {}
            exchange_by_key = {}

            deadlock[len(self.exchanges)] += 1

            for exchange_actor in exchange_actors:  # type: RandomRateExchangeActor

                exchange_actors_by_actor[exchange_actor.actor.name].append(
                    exchange_actor.eu
                )
                exchange_actors_by_gain[exchange_actor.actor.name][
                    exchange_actor.eu
                ].append(exchange_actor)

            if deadlock[len(self.exchanges)] > 1024:
                # this should never happen?
                logging.info("deadlock")

                for ex in self.exchanges:
                    logging.info(ex)

                self.exchanges.clear()
                return None

            # is there an exchange where both actors archive their highest gain
            for exchange_actor in exchange_actors:
                # if an actor is not yet in the list, add him
                # the list is sorted by gain so the first result is the exchange with the highest gain
                # elif, if the actor experience a gain that is equal to the previous highest gain, mark the exchange
                # to the highest also, return the exchange when this already is the case.
                if exchange_actor.actor_name not in highest_actors:
                    highest_actors[exchange_actor.actor_name] = exchange_actor

                    # if the exchange is not yet present, mark this exchange as an exchange where on of the both actors
                    # achieves his highest gain
                    # otherwise this exchange is already marked, then we have found an exchange where both actors
                    # achieve there highest gain
                    if exchange_actor.exchange.key not in exchange_by_key:
                        exchange_by_key[
                            exchange_actor.exchange.key
                        ] = exchange_actor.exchange
                    else:
                        self.remove_exchange_by_key(exchange_actor.exchange.key)
                        return exchange_actor.exchange

                elif highest_actors[exchange_actor.actor_name].eu == exchange_actor.eu:
                    if exchange_actor.exchange.key not in exchange_by_key:
                        exchange_by_key[
                            exchange_actor.exchange.key
                        ] = exchange_actor.exchange
                    else:
                        self.remove_exchange_by_key(exchange_actor.exchange.key)
                        return exchange_actor.exchange

            # lower highest gains
            for actor_name, values in exchange_actors_by_actor.items():
                # do nothing when the actor has one exchange left because this exchange is automatically his highest
                if len(values) > 1:
                    highest = values[0]

                    second_highest = self._find_first_element_not_equal(values)
                    # if all the exchanges have the same gain, do nothing
                    if second_highest is not None:

                        delta_eu = highest - second_highest

                        highest_exchanges = exchange_actors_by_gain[actor_name][highest]
                        # lower ALL the exchanges with the highest gain
                        for highest_exchange_actor in highest_exchanges:

                            highest_exchange = (
                                highest_exchange_actor.exchange
                            )  # type: RandomRateExchange
                            opposite_actor_name = (
                                highest_exchange_actor.opposite_actor.actor_name
                            )

                            if (
                                highest_exchange[actor_name].y
                                == highest_exchange[opposite_actor_name].x_demand
                            ):
                                highest_exchange[opposite_actor_name].recalculate(
                                    delta_eu, increase=False
                                )
                            elif (
                                highest_exchange[opposite_actor_name].y
                                == highest_exchange[actor_name].x_demand
                            ):
                                highest_exchange[actor_name].recalculate(
                                    delta_eu, increase=True
                                )
                            else:
                                highest_exchange[opposite_actor_name].recalculate(
                                    delta_eu, increase=False
                                )

                            highest_exchange[opposite_actor_name].adjust_utility(
                                delta_eu
                            )

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

    @staticmethod
    def _find_first_element_not_equal(exchange_utility_list: List[Decimal]):

        previous_value = exchange_utility_list.pop(0)
        for value in exchange_utility_list:
            if abs(value - previous_value) > 0:
                return value
