import decimal

from model.ActorIssue import ActorIssue


def calc_nbs(actor_issues, denominator):
	numerator = 0

	for k, v in actor_issues.items():
		numerator += (v.position * v.salience * v.power)

	if denominator == 0:
		return 0

	return numerator / denominator


def calc_nbs_denominator(actor_issues):
	denominator = 0
	for k, v in actor_issues.items():
		denominator += (v.salience * v.power)

	return denominator


def calc_adjusted_nbs(actor_issues, updates, actor: str, new_position: decimal.Decimal, denominator: decimal.Decimal):
	copy_ai = {}

	for k, v in actor_issues.items():
		copy_ai[v.actor_name] = ActorIssue(v.actor_name, v.issue_name, position=v.position, power=v.power,
										   salience=v.salience)

	for key, value in updates.items():
		if key in copy_ai:  # TODO: this should not be possible
			copy_ai[key].position = value

	copy_ai[actor].position = new_position

	return calc_nbs(copy_ai, denominator)


def calc_adjusted_nbs_by_position(actor_issues, updates, actor: str, x_pos, new_nbs: decimal.Decimal,
								  denominator: decimal.Decimal):
	copy_ai = {}

	for k, v in actor_issues.items():
		copy_ai[v.actor_name] = ActorIssue(v.actor_name, v.issue_name, position=v.position, power=v.power,
										   salience=v.salience)

	# to be calculate:
	copy_ai[actor].position = x_pos

	for key, value in updates.items():
		# if key not in copy_ai: #todo should always be the case
		#     raise Exception("Fail!")
		copy_ai[key].position = value

	nominator = 0

	for key, value in copy_ai.items():
		if key is not actor:
			nominator += value.position * value.salience * value.power

	left = (new_nbs * denominator) - nominator

	right = left / (copy_ai[actor].salience * copy_ai[actor].power)

	return right


def reverse_move(actor_issues, actor: 'model.AbstractExchange.AbstractExchangeActor', exchange_ratio):
	si = actor.s
	ci = actor.c

	return (exchange_ratio * sum_salience_power(actor_issues)) / (ci * si)


def by_exchange_ratio(supply_actor: 'model.AbstractExchange.AbstractExchangeActor', exchange_ratio: decimal.Decimal):
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


def by_absolute_move(actor_issues, s_actor: 'model.AbstractExchange.AbstractExchangeActor'):
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
	return sum(c.power * c.salience for k, c in actor_issues.items())


def gain(actor: 'ExchangeActor', demand_exchange_ratio, supply_exchange_ratio):
	return demand_exchange_ratio * actor.s - supply_exchange_ratio * actor.s_demand


def calc_actor_externalities(actor_name, model, realized):
	if actor_name in model.ActorIssues[realized.j.supply] and actor_name in model.ActorIssues[realized.i.supply]:
		xp = model.ActorIssues[realized.j.supply][actor_name].position
		sp = model.ActorIssues[realized.j.supply][actor_name].salience

		xq = model.ActorIssues[realized.i.supply][actor_name].position
		sq = model.ActorIssues[realized.i.supply][actor_name].salience

		l0 = abs(realized.j.nbs_0 - xp)
		l1 = abs(realized.j.nbs_1 - xp)
		r0 = abs(realized.i.nbs_0 - xq)
		r1 = abs(realized.i.nbs_1 - xq)

		l = (l0 - l1)
		r = (r0 - r1)
		ext = l * sp + r * sq

		return ext
	return 0
