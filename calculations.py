def calc_nbs(actor_issues):
    numerator = 0
    denominator = 0

    for k, v in actor_issues.items():
        numerator += (v.Position * v.Salience * v.Power)
        denominator += (v.Salience * v.Power)

    return numerator / denominator


def calc_adjusted_nbs(actor_issues, actor: 'Actor', new_position: float):
    import copy

    copy_ai = copy.deepcopy(actor_issues)

    copy_ai[actor.Name].Position = new_position

    return calc_nbs(copy_ai)


def reverse_move(actor_issues, actor: 'ExchangeActor', exchange_ratio):
    si = actor.s
    ci = actor.c

    return (exchange_ratio * sum_salience_power(actor_issues)) / (ci * si)


def by_exchange_ratio(s_actor: 'ExchangeActor', exchange_ratio: float):
    """

    :param s_actor: ExchangeActor
    :param exchange_ratio: float
    :return: float
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
    return sum(c.Power * c.Salience for k, c in actor_issues.items())


def gain(actor: 'ExchangeActor', demand_exchange_ratio, supply_exchange_ratio):
    return demand_exchange_ratio * actor.s - supply_exchange_ratio * actor.s_demand
