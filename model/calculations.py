import decimal
from typing import List, Tuple

from . import base
from . import equalgain

"""
TODO: This package should be rewritten

It contains references with .base and .equalgain while this is a calculation package

An abstraction layer needs to be provided by the model (abstract, equal or random) with the correct paramters

The calculations are only on numbers, or list of numbers.
 
"""


def calc_nbs_new_2(actors: List[Tuple[decimal.Decimal, decimal.Decimal, decimal.Decimal]]):

    for x in actors:
        x
    pass


def calc_nbs_new(power: List[decimal.Decimal], salience: List[decimal.Decimal], position: List[decimal.Decimal],
                 denominator=None):
    """
    Denominator is for caching
    :param power:
    :param salience:
    :param position:
    :param denominator:
    :return:
    """
    if denominator is None:
        denominator = 1

    numerator = sum([power * salience * position for power, salience, position in zip(power, salience, position)])

    return numerator / denominator


def calc_nbs(actor_issues, denominator):
    """
    TODO: the signature of this function should be different. List/dict salience, power, position
    Calculate the Nash bargaining solution.

    This is calculate in the following way:

    :math:`O_d = \\frac{\\sum_{i=1}^n C_{id} S_{id} X_{id} }{\\sum_{i=1}^n C_{id} S_{id} }`

    :param actor_issues: all the other actors on this issue
    :param denominator: the pre-calculated (and cached) denominator: :math:`\\sum_{i=1}^n C_{id} S_{id}`
    :return: Decimal
    """

    if denominator == 0:
        return 0

    numerator = 0

    for k, v in actor_issues.items():
        numerator += v.position * v.salience * v.power

    return numerator / denominator


def nbs_variance(actor_issues, nbs):
    t = (1 / len(actor_issues))
    t2 = sum([(ai.position - nbs) ** 2 for ai in actor_issues])

    return t * t2


def calc_nbs_denominator(actor_issues):
    """
    Calculate the denominator for this issue

    :math:`\\sum_{i=1}^n C_{id} S_{id}`

    :param actor_issues: all the other actors on this issue
    :return: Decimal
    """
    denominator = 0
    for k, v in actor_issues.items():
        denominator += (v.salience * v.power)

    return denominator


def adjusted_nbs(actor_issues, updates, actor, new_position, denominator):
    """
    Adjust the list over actor_issues and calculates the new nash bargaining solution

    :param actor_issues: List[ActorIssue]
    :param updates: dictionary with key (actor) and value (position)
    :param actor: string, current actor
    :param new_position: int, the new position
    :param denominator: Decimal, the cached denominator
    :return: Decimal, the new nash bargaining solution
    """
    copy_ai = {}

    for k, v in actor_issues.items():
        copy_ai[v.actor.name] = base.ActorIssue(v.actor, v.issue, position=v.position, power=v.power,
                                                salience=v.salience)

    for key, value in updates.items():
        if key in copy_ai:  # TODO: this should not be possible
            copy_ai[key].position = value

    copy_ai[actor].position = new_position

    return calc_nbs(copy_ai, denominator)


def adjusted_nbs_by_position(actor_issues, updates, actor, x_pos, new_nbs, denominator):
    """
    Calculate the new position of the given actor when the NBS is adjusted

    :param actor_issues:
    :param updates:
    :param actor:
    :param x_pos:
    :param new_nbs:
    :param denominator:
    :return:
    """
    # TODO: add the math formula in the docstring

    copy_ai = {}

    for k, v in actor_issues.items():
        copy_ai[v.actor_name] = base.ActorIssue(v.actor, v.issue, position=v.position, power=v.power,
                                                salience=v.salience)

    # to be calculate:
    copy_ai[actor].position = x_pos

    for key, value in updates.items():
        copy_ai[key].position = value

    nominator = 0

    for key, value in copy_ai.items():
        if key is not actor:
            nominator += value.position * value.salience * value.power

    left = (new_nbs * denominator) - nominator

    right = left / (copy_ai[actor].salience * copy_ai[actor].power)

    return right


def reverse_move(actor_issues, actor, exchange_ratio):
    """

    :param actor_issues:
    :param actor:
    :param exchange_ratio:
    :return:
    """
    si = actor.s
    ci = actor.c

    return (exchange_ratio * sum_salience_power(actor_issues)) / (ci * si)


def by_exchange_ratio(supply_actor, exchange_ratio):
    """

    :param supply_actor: ExchangeActor
    :param exchange_ratio: Decimal
    :return: Decimal
    """

    d_actor = supply_actor.opposite_actor

    sip = supply_actor.s_demand  # model.get(s_actor.actor, s_actor.demand, "s")
    sjp = d_actor.s  # model.get(d_actor.actor, s_actor.demand, "s")

    sj_supply = d_actor.s_demand  # model.get(d_actor.actor, s_actor.supply, "s")
    si_supply = supply_actor.s  # model.get(s_actor.actor, s_actor.supply, "s")

    return ((si_supply + sj_supply) / (sip + sjp)) * exchange_ratio


def by_absolute_move(actor_issues, s_actor):
    """

    :param actor_issues:
    :param s_actor:
    :return:
    """
    d_actor = s_actor.opposite_actor

    xip = d_actor.x_demand
    xjp = s_actor.x

    sjp = s_actor.s
    cjp = s_actor.c

    sum_sc = sum_salience_power(actor_issues)

    dp = (abs(xip - xjp) * sjp * cjp) / sum_sc

    return dp


def exchange_ratio(delta_x, salience, power, dominator):
    """
    Calculate the exchange ratio

    :param delta_x: the absolute distance between the old position and the new position
    :param salience: the actor salicen
    :param power:  the actor power
    :param dominator: sum(c*s) for all actors on this issue
    :return: the exchange ratio
    """
    return (delta_x * salience * power) / dominator


def sum_salience_power(actor_issues):
    """

    :param actor_issues:
    :return:
    """
    return sum(c.power * c.salience for k, c in actor_issues.items())


def expected_utility(actor, demand_exchange_ratio, supply_exchange_ratio):
    """

    :param actor:
    :param demand_exchange_ratio:
    :param supply_exchange_ratio:
    :return:
    """
    return demand_exchange_ratio * actor.s - supply_exchange_ratio * actor.s_demand


def is_gain_equal(eui, euj, threshold=1e-25):
    """

    :param eui: The utility gain of actor i
    :param euj: The utility gain of actor j
    :param threshold: The threshold where the diff needs to be below
    :return: True when the gains are (approximately) equal
    """
    if abs(eui - euj) > threshold:
        raise Exception("Expected equal gain but found {0} and {1} results in {2}. "
                        "Adjust the above threshold to a higher value and continue.".format(eui, euj, abs(eui - euj)))

    return True


def actor_externalities(actor_name, model_ref, realized):
    """
    Calculate the externalities from an exchange

    :param actor_name: current actor
    :param model_ref: model
    :param realized: realized exchanges
    :return: the Decimal value of the externality
    """

    if actor_name in model_ref.actor_issues[realized.j.supply_issue] \
            and actor_name in model_ref.actor_issues[realized.i.supply_issue]:
        xp = model_ref.actor_issues[realized.j.supply_issue][actor_name].position
        sp = model_ref.actor_issues[realized.j.supply_issue][actor_name].salience

        xq = model_ref.actor_issues[realized.i.supply_issue][actor_name].position
        sq = model_ref.actor_issues[realized.i.supply_issue][actor_name].salience

        l0 = abs(realized.j.nbs_0 - xp)
        l1 = abs(realized.j.nbs_1 - xp)
        r0 = abs(realized.i.nbs_0 - xq)
        r1 = abs(realized.i.nbs_1 - xq)

        l = (l0 - l1)
        r = (r0 - r1)
        ext = l * sp + r * sq

        return ext

    return 0
    #
    # raise Exception(
    #     'Actor is not in collection. Calculation of the externalities is therefore not possible. Is your data correct?')


def position_by_nbs(actor_issues, exchange_actor, nbs, denominator):
    """
    For the Random Rate implementation the position is need to be calculated where a NBS is given.

    :param actor_issues:
    :param exchange_actor:
    :param nbs:
    :param denominator:
    :return:
    """
    # TODO: add the math formula to the docstring

    sum_c_s_x = 0

    for actor_name, actor_issue in actor_issues.items():
        if actor_name != exchange_actor.actor_name:
            sum_c_s_x += actor_issue.salience * actor_issue.power * actor_issue.position

    return (nbs * denominator - sum_c_s_x) / (exchange_actor.c * exchange_actor.s)


def average_and_variance(values: list):
    count = len(values)
    average = sum(values) / count

    variance = sum([(x - average) ** 2 for x in values]) / count

    return average, variance


def maximum_possible_utility_gain(exchange: 'equalgain.EqualGainExchange', actor: 'equalgain.EqualGainExchangeActor'):
    # a maximum of utility gain is achieved when actor i moves completely to the position of j,
    #  while j does not move at all

    exchange.calculate()

    pass


def exchange_ratio_by_zero_gain(delta_q, sq, sp, utility=0):
    """
    Calculates the exchange ratio by a gain of 0.
    Used for the new model
    :param utility: Always 0
    :param delta_q:  Exchange Ratio
    :param sq: Salience
    :param sp: Salience
    :return:
    """
    return abs((utility - (delta_q * sq)) / sp)
