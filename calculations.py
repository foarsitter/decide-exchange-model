from decimal import *

from objects.ActorIssue import ActorIssue


def calc_nbs(actor_issues, denominator):
    numerator = 0
    # denominator = 0

    for k, v in actor_issues.items():
        numerator += (v.position * v.salience * v.power)
        # denominator += (v.Salience * v.Power)

    return numerator / denominator


def calc_nbs_denominator(actor_issues):
    denominator = 0
    for k, v in actor_issues.items():
        denominator += (v.salience * v.power)

    return denominator


def calc_adjusted_nbs(actor_issues, updates, actor: 'Actor', new_position: Decimal, denominator: Decimal):
    copy_ai = {}

    for k, v in actor_issues.items():
        copy_ai[v.actor.Name] = ActorIssue(v.actor, position=v.position, power=v.power, salience=v.salience)

    for key, value in updates.items():
        if key in copy_ai:  # todo not posible
            copy_ai[key].position = value

    copy_ai[actor.Name].position = new_position

    return calc_nbs(copy_ai, denominator)


def calc_adjusted_nbs_by_position(actor_issues, updates, actor: 'Actor', x_pos, new_nbs: Decimal, denominator: Decimal):
    copy_ai = {}

    for k, v in actor_issues.items():
        copy_ai[v.actor.Name] = ActorIssue(v.actor, position=v.position, power=v.power, salience=v.salience)

    # to be calculate:
    copy_ai[actor.Name].position = x_pos

    for key, value in updates.items():
        # if key not in copy_ai: #todo should always be the case
        #     raise Exception("Fail!")
        copy_ai[key].position = value

    nominator = 0

    for key, value in copy_ai.items():
        if key is not actor.Name:
            nominator += value.position * value.salience * value.power

    left = (new_nbs * denominator) - nominator

    right = left / (copy_ai[actor.Name].salience * copy_ai[actor.Name].power)

    return right


def reverse_move(actor_issues, actor: 'ExchangeActor', exchange_ratio):
    si = actor.s
    ci = actor.c

    return (exchange_ratio * sum_salience_power(actor_issues)) / (ci * si)


def by_exchange_ratio(s_actor: 'ExchangeActor', exchange_ratio: Decimal):
    """

    :param s_actor: ExchangeActor
    :param exchange_ratio: Decimal
    :return: Decimal
    """

    d_actor = s_actor.opposite_actor

    sip = s_actor.s_demand  # model.get(s_actor.actor, s_actor.demand, "s")
    sjp = d_actor.s  # model.get(d_actor.actor, s_actor.demand, "s")

    sj_supply = d_actor.s_demand  # model.get(d_actor.actor, s_actor.supply, "s")
    si_supply = s_actor.s  # model.get(s_actor.actor, s_actor.supply, "s")

    return ((si_supply + sj_supply) / (sip + sjp)) * exchange_ratio


def by_absolute_move(actor_issues, s_actor: 'ExchangeActor'):
    d_actor = s_actor.opposite_actor

    xip = d_actor.x_demand
    xjp = s_actor.x

    sjp = s_actor.s
    cjp = s_actor.c

    sum_sc = sum_salience_power(actor_issues)

    dp = (abs(xip - xjp) * sjp * cjp) / sum_sc

    return dp


def sum_salience_power(actor_issues):
    return sum(c.power * c.salience for k, c in actor_issues.items())


def gain(actor: 'ExchangeActor', demand_exchange_ratio, supply_exchange_ratio):
    return demand_exchange_ratio * actor.s - supply_exchange_ratio * actor.s_demand


def externalities(actor_issue, nbs_0, nbs_1, exchange):
    shift = (nbs_0 - actor_issue.position) - (nbs_1 - actor_issue.position)
    eu_k = shift * actor_issue.salience

    e_type = ""

    if exchange.i.actor.Name == actor_issue.actor.Name or exchange.j.actor.Name == actor_issue.actor.Name:
        e_type = "own"
    else:
        if exchange.i.group == actor_issue.group or exchange.j.group == actor_issue.group:
            if eu_k > 0:
                e_type = 'ip'
            else:
                e_type = 'in'
        else:
            if eu_k > 0:
                e_type = 'op'
            else:
                e_type = 'on'

    return {"type": e_type, "value": eu_k}
