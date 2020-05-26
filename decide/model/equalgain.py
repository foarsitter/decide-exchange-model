import decimal
import logging
import random
from operator import attrgetter
from typing import List

from decide.model import base, calculations


class EqualGainExchangeActor(base.AbstractExchangeActor):
    """
    AbstractExchangeActor is the same actor...
    """

    def __init__(
        self,
        model: "EqualGainModel",
        actor: base.Actor,
        demand_issue: base.Issue,
        supply_issue: base.Issue,
        exchange: "EqualGainExchange",
    ):
        super().__init__(model, actor, demand_issue, supply_issue, exchange)

        self.equal_gain_voting = "-"
        self.z = "-"
        self.u = "-"
        self.v = "-"
        self.eu_max = "-"

    def randomized_gain(self, u, v, z):

        p = self.exchange.model.randomized_value

        eu = self.exchange.gain

        self.z = z
        self.u = u
        self.v = v

        self.opposite_actor.u = u
        self.opposite_actor.v = v
        self.opposite_actor.z = z

        if v < 0.5:  # V < 0.5:
            # wins
            eui = eu + p * z * (self.eu_max - eu)
        else:
            # loses
            eui = eu - p * z * eu

        # calculate the expected utility of J
        move_i = abs(self.supply.position - self.opposite_actor.demand.position)

        # supply exchange ratio for i = q, supply for j = p
        exchange_ratio_q = calculations.exchange_ratio(
            move_i,
            self.supply.salience,
            self.supply.power,
            self.model.nbs_denominators[self.supply.issue],
        )

        # supply exchange ratio for j, demand for i
        exchange_ratio_p = (
            eui + exchange_ratio_q * self.supply.salience
        ) / self.demand.salience

        eui_check = abs(
            calculations.expected_utility(self, exchange_ratio_q, exchange_ratio_p)
        )

        if abs(eui_check - abs(eui)) > 1e-10:
            print("This should be equal.", abs(eui_check - eui))

        move_j = calculations.reverse_move(
            actor_issues=self.opposite_actor.actor_issues(),
            actor=self.opposite_actor,
            exchange_ratio=exchange_ratio_p,
        )

        euj = abs(
            calculations.expected_utility(
                self.opposite_actor, exchange_ratio_p, exchange_ratio_q
            )
        )

        delta_x_j_supply = abs(
            self.opposite_actor.supply.position - self.demand.position
        )

        if abs(move_j) > delta_x_j_supply:
            exchange_ratio_p = calculations.exchange_ratio(
                delta_x_j_supply,
                self.opposite_actor.supply.salience,
                self.opposite_actor.supply.power,
                self.model.nbs_denominators[self.opposite_actor.supply.issue],
            )

            exchange_ratio_q = abs(
                (eui - exchange_ratio_p * self.demand.salience) / self.supply.salience
            )

            move_j = delta_x_j_supply
            move_i = calculations.reverse_move(
                self.actor_issues(), self, exchange_ratio_q
            )

            if abs(move_i) < abs(
                self.supply.position - self.opposite_actor.demand.position
            ):

                euj = abs(
                    calculations.expected_utility(
                        self.opposite_actor, exchange_ratio_p, exchange_ratio_q
                    )
                )
                eui_check = abs(
                    calculations.expected_utility(
                        self, exchange_ratio_q, exchange_ratio_p
                    )
                )

                # check if the shift does not exceed the NBS.
                if self.opposite_actor.supply.position > self.demand.position:
                    move_j_a = move_j * -1
                else:
                    move_j_a = move_j

                nbs_adjusted = self.opposite_actor.adjust_nbs(
                    position=self.opposite_actor.supply.position + move_j_a
                )
                self.opposite_actor.nbs_0 = nbs_adjusted

                if (
                    self.demand.position >= self.opposite_actor.nbs_0
                    and self.demand.position >= nbs_adjusted
                ):
                    pass
                elif (
                    self.demand.position <= self.opposite_actor.nbs_0
                    and self.demand.position <= nbs_adjusted
                ):
                    pass
                else:

                    delta = abs(
                        calculations.adjusted_nbs_by_position(
                            actor_issues=self.opposite_actor.actor_issues(),
                            updates=self.opposite_actor.exchange.updates[
                                self.opposite_actor.supply.issue
                            ],
                            actor=self.opposite_actor.actor,
                            x_pos=self.opposite_actor.supply.position,
                            new_nbs=self.demand.position,
                            denominator=self.model.nbs_denominators[
                                self.opposite_actor.supply.issue
                            ],
                        )
                    )

                    exchange_ratio_p = calculations.exchange_ratio(
                        delta_x=delta,
                        salience=self.opposite_actor.supply.salience,
                        power=self.opposite_actor.supply.power,
                        denominator=self.model.nbs_denominators[
                            self.opposite_actor.supply.issue
                        ],
                    )

                    exchange_ratio_q = abs(
                        (eui - exchange_ratio_p * self.demand.salience)
                        / self.supply.salience
                    )

                    move_i_b = calculations.reverse_move(
                        actor_issues=self.actor_issues(),
                        actor=self,
                        exchange_ratio=exchange_ratio_p,
                    )

                    euj = abs(
                        calculations.expected_utility(
                            self.opposite_actor, exchange_ratio_p, exchange_ratio_q
                        )
                    )
                    eui_check = abs(
                        calculations.expected_utility(
                            self, exchange_ratio_q, exchange_ratio_p
                        )
                    )

                    move_i = move_i_b
                    move_j = move_j_a

                    self.opposite_actor.is_adjusted_by_nbs = True

            else:
                logging.info(
                    "SoftFail: when the shift for j is to large by a maximum shift of i, "
                    "the maximum shift of j has to result in a lower shift for i. data="
                    + str(self.exchange)
                )

        else:
            # check if the shift does not exceed the NBS.
            if self.supply.position > self.opposite_actor.demand.position:
                move_i_a = move_i * -1
            else:
                move_i_a = move_i

            nbs_adjusted = self.adjust_nbs(position=self.supply.position + move_i_a)

            # the nbs shifts beyond the position of the demand position

            if (
                self.opposite_actor.demand.position >= self.nbs_0
                and self.opposite_actor.demand.position >= nbs_adjusted
            ):
                pass
            elif (
                self.opposite_actor.demand.position <= self.nbs_0
                and self.opposite_actor.demand.position <= nbs_adjusted
            ):
                pass
            else:

                delta = abs(
                    calculations.adjusted_nbs_by_position(
                        actor_issues=self.actor_issues(),
                        updates=self.exchange.updates[self.supply.issue],
                        actor=self.actor,
                        x_pos=self.supply.position,
                        new_nbs=self.opposite_actor.demand.position,
                        denominator=self.model.nbs_denominators[self.supply.issue],
                    )
                )

                exchange_ratio_q = calculations.exchange_ratio(
                    delta,
                    self.supply.salience,
                    self.supply.power,
                    self.model.nbs_denominators[self.supply.issue],
                )

                exchange_ratio_p = (
                    eui + exchange_ratio_q * self.supply.salience
                ) / self.demand.salience

                move_j_b = calculations.reverse_move(
                    actor_issues=self.opposite_actor.actor_issues(),
                    actor=self.opposite_actor,
                    exchange_ratio=exchange_ratio_p,
                )

                euj = abs(
                    calculations.expected_utility(
                        actor=self.opposite_actor,
                        demand_exchange_ratio=exchange_ratio_p,
                        supply_exchange_ratio=exchange_ratio_q,
                    )
                )

                eui_check = abs(
                    calculations.expected_utility(
                        actor=self,
                        demand_exchange_ratio=exchange_ratio_q,
                        supply_exchange_ratio=exchange_ratio_p,
                    )
                )

                if p == 0 and abs(eui - euj) > 1e-10:
                    raise Exception("Fail: adjusting nbs.")

                move_i = move_i_a
                move_j = move_j_b

                self.is_adjusted_by_nbs = True

        if abs(abs(eui) - abs(eui_check)) > 1e-10:
            x = abs(eui - eui_check)
            logging.info(f"fail: {x}")
            # raise Exception('Fail: the expected utility of the check ({0})'
            #                 ' does not match the expected utility ({1}), {2}.'
            #                 .format(eui_check, eui,
            #                         self.opposite_actor.is_adjusted_by_nbs))

        if self.eu_max is None:
            # if they are not equal (occurs by p=0.0)
            if not abs(euj - eui) < 1e-10:
                if (euj - eui) < 1e-10:
                    raise Exception(
                        "Fail: when eui_max is none (v=False), euj should be larger in this case. {0}".format(
                            self.opposite_actor.is_adjusted_by_nbs
                        )
                    )

        if p == 0 and abs(eui - euj) > 1e-10:
            raise Exception(
                "Fail: Equal Gain not equal with p=0.0 and nbs_adjusted={0}".format(
                    self.opposite_actor.is_adjusted_by_nbs
                )
            )

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
        self.opposite_actor.y = (
            self.opposite_actor.supply.position + self.opposite_actor.move
        )

        b1 = self.is_move_valid(self.move)
        b2 = self.opposite_actor.is_move_valid(self.opposite_actor.move)

        self.exchange.is_valid = b1 and b2

        self.nbs_0 = self.adjust_nbs(self.supply.position)
        self.nbs_1 = self.adjust_nbs(self.y)

        self.opposite_actor.nbs_0 = self.opposite_actor.adjust_nbs(
            self.opposite_actor.supply.position
        )
        self.opposite_actor.nbs_1 = self.opposite_actor.adjust_nbs(
            self.opposite_actor.y
        )


class EqualGainExchange(base.AbstractExchange):
    actor_class = EqualGainExchangeActor

    def __init__(self, i, j, p, q, m, groups):
        self.i: EqualGainExchangeActor
        self.j: EqualGainExchangeActor
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
            self.j.move = calculations.reverse_move(
                self.j.actor_issues(), self.j, self.dp
            )

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
            self.i.eu = self.gain
            self.j.eu = self.gain

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

        if (
            self.model.randomized_value is not None
            and self.model.randomized_value > 0.0
        ):

            u = random.uniform(0, 1)
            v = random.uniform(0, 1)
            z = decimal.Decimal(random.uniform(0, 1))

            self.calculate_maximum_utility()

            if u < 0.5:
                self.i.randomized_gain(u, v, z)
            else:
                self.j.randomized_gain(u, v, z)

    def calculate_maximum_utility(self):

        nbs_supply_i_adjusted = self.i.adjust_nbs(self.i.opposite_actor.demand.position)
        nbs_supply_j_adjusted = self.j.adjust_nbs(self.j.opposite_actor.demand.position)

        nbs_supply_i_delta = abs(self.i.nbs_0 - nbs_supply_i_adjusted)
        nbs_supply_j_delta = abs(self.j.nbs_0 - nbs_supply_j_adjusted)

        loss_actor_1_supply_issue = nbs_supply_j_delta * self.j.supply.salience
        gain_actor_2_demand_issue = nbs_supply_j_delta * self.i.demand.salience

        loss_actor_2_supply_issue = nbs_supply_i_delta * self.i.supply.salience
        gain_actor_1_demand_issue = nbs_supply_i_delta * self.j.demand.salience

        if gain_actor_2_demand_issue > gain_actor_1_demand_issue:
            actor = self.j
            gain = gain_actor_1_demand_issue
            loss = loss_actor_2_supply_issue
        else:
            actor = self.i

            gain = gain_actor_2_demand_issue
            loss = loss_actor_1_supply_issue

        s = actor.supply.salience / (actor.supply.salience + actor.opposite_actor.demand.salience)

        delta_2_u1 = loss / (s * actor.opposite_actor.demand.salience)
        delta_2_u2 = gain / (s * actor.supply.salience)

        actor.eu_max = gain - (s * actor.supply.salience * delta_2_u1)
        actor.opposite_actor.eu_max = s * actor.opposite_actor.demand.salience * delta_2_u2 - loss

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
                "u",
                "v",
                "z",
                "max eu",
                "eu",
                "gain p=0",
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
                "u",
                "v",
                "z",
                "max eu",
                "eu",
                "gain p=0",
                "nbs 0",
                "nbs 1",
                "delta nbs",
                "check",
            ]

        exchange = self

        delta_nbs_i = abs(exchange.i.nbs_0 - exchange.i.nbs_1)
        delta_nbs_j = abs(exchange.j.nbs_0 - exchange.j.nbs_1)

        eu_i = abs(
            delta_nbs_i * exchange.i.supply.salience
            - delta_nbs_j * exchange.i.demand.salience
        )
        eu_j = abs(
            delta_nbs_j * exchange.j.supply.salience
            - delta_nbs_i * exchange.j.demand.salience
        )

        check_i = abs(eu_i - exchange.i.eu) < 1e-10
        check_j = abs(eu_j - exchange.j.eu) < 1e-10

        return [
            # the actors
            exchange.i.actor.name,
            exchange.i.supply.issue,
            exchange.i.supply.power,
            exchange.i.supply.salience,
            exchange.i.demand.salience,
            zero_on_exception(exchange.i.supply.salience, exchange.i.demand.salience),
            exchange.i.supply.position,
            exchange.i.move,
            exchange.i.y,
            exchange.i.equal_gain_voting,
            exchange.i.opposite_actor.demand.position,
            exchange.i.u,
            exchange.i.v,
            exchange.i.z,
            exchange.i.eu_max,
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
            zero_on_exception(exchange.j.supply.salience , exchange.j.demand.salience),
            exchange.j.supply.position,
            exchange.j.move,
            exchange.j.y,
            exchange.j.equal_gain_voting,
            exchange.j.opposite_actor.demand.position,
            exchange.j.u,
            exchange.j.v,
            exchange.j.z,
            exchange.j.eu_max,
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

    def __init__(self, randomized_value=None):
        super().__init__()
        self.exchanges: List[EqualGainExchange]

        if isinstance(randomized_value, str):
            randomized_value = decimal.Decimal(randomized_value)

        self.randomized_value = randomized_value

        self.model_name = "equal"

        if randomized_value:
            self.model_name += "-" + str(round(randomized_value, 2))

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

            # in some cases the exchanges have an equal gain, choice randomly between them
            if EqualGainModel.ALLOW_RANDOM:

                next_exchange = self.exchanges[0]

                if abs(realize.gain - next_exchange.gain) < 1e-20:
                    self.tie_count += 1

                    if random.random() >= 0.5:
                        self.exchanges.append(realize)
                        realize = self.exchanges.pop(0)
                    else:
                        self.exchanges.append(next_exchange)

        return realize

    @staticmethod
    def new_exchange_factory(i, j, p, q, model, groups):
        return EqualGainExchange(i, j, p, q, model, groups)


def zero_on_exception(a, b):
    try:
        return a / b
    except:
        return 0