import random
from decimal import *

import calculations
from objects.AbstractExchange import AbstractExchange, AbstractExchangeActor


class ExchangeActor(AbstractExchangeActor):
	def __init__(self, model, actor_name: str, demand: str, supply: str, group: str):
		super.__init__(model, actor_name, demand, supply, group)

		self.eu = 0
		self.is_highest_gain = False

	def is_move_valid(self, move):
		# a move cannot exceed the interval [0,100]
		if abs(move) > 100 or abs(move) <= 1e-10:
			return False

		# if an exchange is on the edges there is no move posible
		if self.x + move < 0 or self.x + move > 100:
			return False

		if sum(self.moves) > 100:
			return False

		moves_min = min(self.moves)
		moves_max = max(self.moves)

		if moves_min < 0 and moves_max < 0 or moves_min > 0 and moves_max > 0:
			return True

	def __str__(self):
		return "{0} {1} {2} {3} ({4})".format(self.actor_name, self.supply, self.x, self.y,
											  self.opposite_actor.x_demand)

	def new_start_position(self):

		sw = Decimal(0.4)
		fw = Decimal(0.1)
		swv = (1 - self.s) * sw * self.y
		fwv = fw * self.y
		pv = (1 - (1 - self.s) * sw - fw) * self.start_position
		x_t1 = swv + fwv + pv

		return x_t1

	def equals_with_supply_obj(self, exchange_actor):

		if self.actor_name == exchange_actor.actor_name and self.supply == exchange_actor.supply:
			return True
		return False

	def equals_with_supply_str(self, actor_name, supply):

		if self.actor_name == actor_name and self.supply == supply:
			return True
		return False


class Exchange(AbstractExchange):
	actor_class = ExchangeActor

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

		self.i.eu = abs(calculations.gain(self.i, self.dq, self.dp))
		self.j.eu = abs(calculations.gain(self.j, self.dp, self.dq))

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
