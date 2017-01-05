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

	def __init__(self, model, actor_name: str, demand: str, supply: str, group: str):
		"""
		Constructor, needs to call super()

		:param model:
		:param actor_name:
		:param demand:
		:param supply:
		:param group:
		"""
		super().__init__(model, actor_name, demand, supply, group)

		self.eu = 0
		self.is_highest_gain = False


class RandomRateExchange(AbstractExchange):
	"""
	An exchange for the random rate model
	"""

	actor_class = RandomRateExchangeActor
	""" For the factory, so the Abstract know's which type he has to create  """

	def __init__(self, i: str, j: str, p: str, q: str, m, groups):
		super().__init__(i, j, p, q, m, groups)
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

	def highest_gain(self) -> RandomRateExchange:

		"""
		Returns the exchange where **both** actors expect the highest gain.
		In most of the cases there is only one actor of an exchange expecting the highest gain.
		These need to be re-calculated in _recalc_hihgest_
		"""
		self.sort_exchanges()

		highest = self.Exchanges.pop(0)

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

		for exchange in self.Exchanges:
			if exchange.i.is_highest_gain or exchange.j.is_highest_gain:
				highest.append(exchange)
			else:
				left_over.append(exchange)

		second_highest_gains = dict()
		second_highest_gain_exchange = dict()

		for actor in self.Actors:
			second_highest_gains[actor] = 0

		for exchange in left_over:

			if exchange.i.eu > second_highest_gains[exchange.i.actor_name]:
				second_highest_gains[exchange.i.actor_name] = exchange.i.eu
				second_highest_gain_exchange[exchange.i.actor_name] = exchange.i

			if exchange.j.eu > second_highest_gains[exchange.j.actor_name]:
				second_highest_gains[exchange.j.actor_name] = exchange.j.eu
				second_highest_gain_exchange[exchange.j.actor_name] = exchange.j

		for exchange_pair in highest:
			if exchange_pair.i.is_highest_gain:
				eu = second_highest_gain_exchange[exchange_pair.i.actor_name].eu

				delta_eu = exchange_pair.i.eu - eu

				if exchange_pair.i.y == exchange_pair.j.x_demand:  # i moves to j completely on q

					delta_nbs = delta_eu / exchange_pair.j.s
					nbs_adjusted = exchange_pair.j.nbs_1 - delta_nbs
					actor = exchange_pair.j

					position = calculations.position_by_nbs(self.ActorIssues[actor.supply],
															exchange_actor=actor,
															nbs=nbs_adjusted,
															denominator=self.nbs_denominators[actor.supply])

					exchange_pair.j.x = position

				elif exchange_pair.j.y == exchange_pair.i.x_demand:  # j moves to i completely on p

					delta_nbs = (delta_eu / exchange_pair.i.s)
					nbs_adjusted = exchange_pair.i.nbs_1 - delta_nbs
					actor = exchange_pair.i

					position = calculations.position_by_nbs(self.ActorIssues[actor.supply],
															exchange_actor=actor,
															nbs=nbs_adjusted,
															denominator=self.nbs_denominators[actor.supply])

					exchange_pair.i.x = position

				else:
					# TODO is there a third option that both exchanges are possible?
					pass

				exchange_pair.i.eu -= delta_eu
				exchange_pair.j.eu += delta_eu

				if abs(exchange_pair.i.eu - eu) < 1e-10:
					raise Exception("Should be equal")



			# # should be absolute?
			#
			#
			# delta_nbs = delta_eu * exchange_pair.i.s
			#
			# gain_j = (delta_nbs * exchange_pair.j.s)
			#
			# # exchange_pair.i.eu = exchange_pair.i.eu - delta_eu
			# # exchange_pair.j.eu = exchange_pair.j.eu + gain_j
			#
			# dominator =
			# increase = exchange_pair.i.x < exchange_pair.i.y
			# nbs_adjusted = 0
			#
			# if increase:
			# 	nbs_adjusted = exchange_pair.i.nbs_1 + delta_nbs
			# else:
			# 	nbs_adjusted = exchange_pair.i.nbs_1 - delta_nbs
			#
			# sum_c_s_x = 0
			#
			# x = 0
			#
			# for actor_name, actor_issue in self.ActorIssues[exchange_pair.i.supply].items():
			#
			# 	if actor_name == exchange_pair.i.actor_name:
			# 		x = actor_issue.position
			# 	else:
			# 		sum_c_s_x += actor_issue.salience * actor_issue.power * actor_issue.position
			#
			# yiq = (nbs_adjusted * dominator - sum_c_s_x) / (exchange_pair.i.c * exchange_pair.i.s)
			#
			# dq = calculations.exchange_ratio(abs(x - yiq), exchange_pair.i.s, exchange_pair.i.c, dominator)
			# dp = calculations.by_exchange_ratio(exchange_pair.i, dq)
			#
			# dq_old = exchange_pair.dq
			# dp_old = exchange_pair.dp
			#
			# eui_old = exchange_pair.i.eu
			# euj_old = exchange_pair.j.eu
			#
			# eui_new = eu
			# euj_new = exchange_pair.j.eu + gain_j
			#
			# if eui_old > eui_new and euj_old < euj_new:
			# 	print(True)
			#
			# print(dp)
