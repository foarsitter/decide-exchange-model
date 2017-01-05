from decimal import Decimal
from itertools import combinations

from model import calculations


class ActorIssue:
	def __init__(self, actor_name: str, issue_name: str, position: Decimal, salience: Decimal, power: Decimal):
		self.power = Decimal(power)
		self.position = Decimal(position)
		self.salience = Decimal(salience)
		self.left = False
		self.actor_name = actor_name
		self.group = ""
		self.issue_name = issue_name

	def is_left_to_nbs(self, nbs: Decimal) -> bool:
		self.left = self.position < nbs
		return self.left

	def __str__(self):
		return "Actor {0} with position={1}, salience={2}, power={3}".format(self.actor_name,
																			 self.position, self.salience,
																			 self.power)


class AbstractExchangeActor(object):
	"""
	Represents and actor of an exchange
	"""

	def __init__(self, model, actor_name: str, demand: str, supply: str, group: str):
		"""
		Constructor, must be invoked

		:param model:
		:param actor_name:
		:param demand:
		:param supply:
		:param group:
		"""
		self.c = model.get_value(actor_name, supply, "c")
		self.s = model.get_value(actor_name, supply, "s")
		self.x = model.get_value(actor_name, supply, "x")
		self.y = 0
		self.eu = 0
		self.c_demand = model.get_value(actor_name, demand, "c")
		self.s_demand = model.get_value(actor_name, demand, "s")
		self.x_demand = model.get_value(actor_name, demand, "x")
		self.is_highest_gain = False
		self.start_position = self.x

		self.demand = demand
		self.supply = supply

		self.group = group

		self.actor_name = actor_name

		self.opposite_actor = None
		self.move = 0
		self.moves = []

		self.nbs_0 = 0
		self.nbs_1 = 0

	def is_move_valid(self, move: int) -> bool:

		"""
		Cheks if a move not exceeds the interval [0,100]

		:param move:
		:return:
		"""
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
		"""
		The String representation of the object
		:return: String representation of the object
		"""
		return "{0} {1} {2} {3} ({4})".format(self.actor_name, self.supply, self.x, self.y,
											  self.opposite_actor.x_demand)

	def new_start_position(self):
		"""
		Calculate the new starting postion for the next round
		:return:
		"""
		sw = Decimal(0.4)
		fw = Decimal(0.1)
		swv = (1 - self.s) * sw * self.y
		fwv = fw * self.y
		pv = (1 - (1 - self.s) * sw - fw) * self.start_position
		x_t1 = swv + fwv + pv

		return x_t1

	def equals_with_supply_obj(self, exchange_actor: 'AbstractExchangeActor') -> bool:
		"""
		Compares the actor with the given
		:param exchange_actor:
		:return:
		"""
		if self.actor_name == exchange_actor.actor_name and self.supply == exchange_actor.supply:
			return True
		return False

	def equals_with_supply_str(self, actor_name, supply):

		if self.actor_name == actor_name and self.supply == supply:
			return True
		return False


class AbstractExchange(object):
	"""
	An exchange between two actors and two issues. Each actor has a demand and supply issue
	"""

	actor_class = AbstractExchangeActor

	def __init__(self, i: str, j: str, p: str, q: str, m: 'AbstractModel', groups: list):
		"""
		An exchange between two actors and two issues. Each actor has a demand and supply issue
		:param i: the first actor
		:param j: the second actor
		:param p: the first issue
		:param q: the second issue
		:param m: reference to the model object
		:param groups: list of the two groups each actor is in
		"""
		self.model = m
		self.gain = 0
		self.is_valid = True
		self.re_calc = False
		self.p = p
		self.q = q

		self.dp = 0
		self.dq = 0

		self.updates = {p: dict(), q: dict()}
		# c.	If (1) holds, i shifts his position on issue p in the direction of j,
		# whereas j shifts his position on issue q in the direction of i.
		# Issue p is then called the supply issue of i and the demand issue of j,
		# whereas issue q is the demand issue of i and the supply issue of j.
		# If (2) holds,
		# issue q is the supply issue of i and issue p is the supply issue of j.
		# if ( (model$s_matrix[p, i] / model$s_matrix[q, i]) < (model$s_matrix[p, j] / model$s_matrix[q, j]))
		if (m.get_value(i, p, "s") / m.get_value(i, q, "s")) < (m.get_value(j, p, "s") / m.get_value(j, q, "s")):
			self.i = AbstractExchange.actor_class(m, j, supply=q, demand=p, group=groups[0])
			self.j = AbstractExchange.actor_class(m, i, supply=p, demand=q, group=groups[1])
		else:
			self.i = AbstractExchange.actor_class(m, i, supply=q, demand=p, group=groups[0])
			self.j = AbstractExchange.actor_class(m, j, supply=p, demand=q, group=groups[1])

		self.j.opposite_actor = self.i
		self.i.opposite_actor = self.j

	def calculate(self):
		"""Method stub to be overriden"""
		pass

	def check_nbs_i(self):  # TODO: create universal method because of code duplication in self.check_nbs_j
		"""
		Calculate if the NBS/outcome doesn't shifts over the original position of actor i
		TODO: create universal method because of code duplication in self.check_nbs_j
		:return:
		"""
		self.i.nbs_0 = calculations.adjusted_nbs(self.model.ActorIssues[self.i.supply],
												 self.updates[self.i.supply],
												 self.i.actor_name, self.i.x,
												 self.model.nbs_denominators[self.i.supply])

		self.i.nbs_1 = calculations.adjusted_nbs(self.model.ActorIssues[self.i.supply],
												 self.updates[self.i.supply],
												 self.i.actor_name, self.i.y,
												 self.model.nbs_denominators[self.i.supply])

		# TODO this should be a method
		if self.j.x_demand >= self.i.nbs_0 and self.j.x_demand >= self.i.nbs_1:
			pass
		elif self.j.x_demand <= self.i.nbs_0 and self.j.x_demand <= self.i.nbs_1:
			pass
		else:
			new_pos = calculations.adjusted_nbs_by_position(self.model.ActorIssues[self.i.supply],
															self.updates[self.i.supply],
															self.i.actor_name, self.i.x, self.j.x_demand,
															self.model.nbs_denominators[self.i.supply])

			self.dq = (abs(new_pos - self.i.x) * self.i.s * self.i.c) / self.model.nbs_denominators[self.i.supply]
			self.dp = calculations.by_exchange_ratio(self.i, self.dq)

			self.i.move = abs(new_pos - self.i.x)
			self.j.move = calculations.reverse_move(self.model.ActorIssues[self.j.supply], self.j, self.dp)

			if self.i.x > self.j.x_demand:
				self.i.move *= -1

			if self.j.x > self.i.x_demand:
				self.j.move *= -1

			self.i.moves.pop()
			self.j.moves.pop()
			self.i.moves.append(self.i.move)
			self.j.moves.append(self.j.move)

			self.i.y = self.i.x + self.i.move
			self.j.y = self.j.x + self.j.move

			eui = calculations.expected_utility(self.i, self.dq, self.dp)
			euj = calculations.expected_utility(self.j, self.dp, self.dq)

			if abs(eui - euj) > 0.0001:
				raise Exception("Expected equal gain")
			else:
				self.gain = abs(eui)

			b1 = self.i.is_move_valid(self.i.move)
			b2 = self.j.is_move_valid(self.j.move)

			self.is_valid = b1 and b2

	def check_nbs_j(self):
		"""
		Calculate if the NBS/outcome doesn't shifts over the original position of actor i
		TODO: create universal method because of code duplication in self.check_nbs_i
		:return:
		"""
		self.j.nbs_0 = calculations.adjusted_nbs(self.model.ActorIssues[self.j.supply],
												 self.updates[self.j.supply],
												 self.j.actor_name, self.j.x,
												 self.model.nbs_denominators[self.j.supply])

		self.j.nbs_1 = calculations.adjusted_nbs(self.model.ActorIssues[self.j.supply],
												 self.updates[self.j.supply],
												 self.j.actor_name, self.j.y,
												 self.model.nbs_denominators[self.j.supply])

		if self.i.x_demand >= self.j.nbs_0 and self.i.x_demand >= self.j.nbs_1:
			pass
		elif self.i.x_demand <= self.j.nbs_0 and self.i.x_demand <= self.j.nbs_1:
			pass
		else:

			new_pos = calculations.adjusted_nbs_by_position(self.model.ActorIssues[self.j.supply],
															self.updates[self.j.supply],
															self.j.actor_name, self.j.x, self.i.x_demand,
															self.model.nbs_denominators[self.j.supply])

			self.dp = (abs(new_pos - self.j.x) * self.j.s * self.j.c) / self.model.nbs_denominators[
				self.j.supply]
			self.dq = calculations.by_exchange_ratio(self.j, self.dp)

			self.i.move = calculations.reverse_move(self.model.ActorIssues[self.i.supply], self.i, self.dq)
			self.j.move = abs(new_pos - self.j.x)

			if self.i.x > self.j.x_demand:
				self.i.move *= -1

			if self.j.x > self.i.x_demand:
				self.j.move *= -1

			self.i.moves.pop()
			self.j.moves.pop()
			self.i.moves.append(self.i.move)
			self.j.moves.append(self.j.move)

			self.i.y = self.i.x + self.i.move
			self.j.y = self.j.x + self.j.move

			nbs_1 = calculations.adjusted_nbs(self.model.ActorIssues[self.j.supply],
											  self.updates[self.j.supply],
											  self.j.actor_name, self.j.y,
											  self.model.nbs_denominators[self.j.supply])

			if abs(nbs_1 - self.i.x_demand) > 0.000001:
				new_pos = calculations.adjusted_nbs_by_position(self.model.ActorIssues[self.j.supply],
																self.updates[self.j.supply],
																self.j.actor_name, self.j.x, self.i.x_demand,
																self.model.nbs_denominators[self.j.supply])

				# self.is_valid = False
				# raise Exception("Not Posible!")
				return

			eui = calculations.expected_utility(self.i, self.dq, self.dp)
			euj = calculations.expected_utility(self.j, self.dp, self.dq)

			if abs(eui - euj) > 0.0001:
				raise Exception("Expected equal gain")
			else:
				self.gain = abs(eui)

			b1 = self.i.is_move_valid(self.i.move)
			b2 = self.j.is_move_valid(self.j.move)

			self.is_valid = b1 and b2

	def equal_str(self, i: str, j: str, p: str, q: str) -> bool:
		"""
		Compare the given values
		"""
		return self.i.equals_with_supply_str(i, q) and self.j.equals_with_supply_str(j, p) or \
			   self.i.equals_with_supply_str(j, p) and self.j.equals_with_supply_str(i, q)

	def equal_obj(self, exchange: 'AbstractExchange') -> bool:
		"""
		Compare the both objects
		"""
		return self.equal_obj(i=exchange.i, j=exchange.j, p=exchange.p, q=exchange.q)

	def contains_actor_with_supply(self, actor: 'AbstractExchangeActor', issue: str) -> bool:
		"""
		Check if the actors has the given issue as supply issue
		"""
		return self.i.equals_with_supply_str(actor, issue) or self.j.equals_with_supply_str(actor, issue)

	def recalculate(self, exchange: 'AbstractExchange'):
		"""
		This exchange needs to be recalculated because the given exchange is performed
		and has an influence on this (self) exchange
		:param exchange:
		"""
		self.re_calc = False

		if self.i.equals_with_supply_obj(exchange.i):
			self.i.x = exchange.i.y
			self.i.moves.pop()
			self.j.moves.pop()
			move = exchange.i.moves[-1]

			self.i.moves.append(move)
			self.re_calc = True
		elif self.i.equals_with_supply_obj(exchange.j):
			self.i.x = exchange.j.y
			self.i.moves.pop()
			self.j.moves.pop()
			self.i.moves.append(exchange.j.moves[-1])
			self.re_calc = True

		if self.j.equals_with_supply_obj(exchange.i):
			self.j.x = exchange.i.y
			self.i.moves.pop()
			self.j.moves.pop()
			self.j.moves.append(exchange.i.moves[-1])
			self.re_calc = True
		elif self.j.equals_with_supply_obj(exchange.j):
			self.j.x = exchange.j.y
			self.i.moves.pop()
			self.j.moves.pop()
			self.j.moves.append(exchange.j.moves[-1])
			self.re_calc = True

		# update the positions for the demand actors...
		if (self.j.actor_name == exchange.j.actor_name and self.j.demand == exchange.j.demand) or (
						self.i.actor_name == exchange.j.actor_name and self.i.demand == exchange.j.demand):

			if exchange.i.actor_name in self.updates[exchange.j.demand]:

				exchangeActor = exchange.i
				demand = exchange.j.demand
				x_updated = self.updates[exchange.j.demand][exchangeActor.actor_name]

				if exchangeActor.start_position <= x_updated:
					if x_updated < exchangeActor.y:
						self.updates[demand][exchangeActor.actor_name] = x_updated
					else:
						self.updates[demand][exchangeActor.actor_name] = exchangeActor.y
				else:
					if x_updated > exchangeActor.y:
						self.updates[demand][exchangeActor.actor_name] = x_updated
					else:
						self.updates[demand][exchangeActor.actor_name] = exchangeActor.y
			else:
				self.updates[exchange.j.demand][exchange.i.actor_name] = exchange.i.y

			if not self.re_calc:
				self.i.moves.pop()
				self.j.moves.pop()
				self.re_calc = True

		if (self.i.actor_name == exchange.i.actor_name and self.i.demand == exchange.i.demand) or (
						self.j.actor_name == exchange.i.actor_name and self.j.demand == exchange.i.demand):

			if exchange.j.actor_name in self.updates[exchange.i.demand]:

				exchangeActor = exchange.j
				demand = exchange.i.demand
				x_updated = self.updates[exchange.i.demand][exchangeActor.actor_name]

				if exchangeActor.start_position <= x_updated:
					if x_updated < exchangeActor.y:
						self.updates[demand][exchangeActor.actor_name] = x_updated
					else:
						self.updates[demand][exchangeActor.actor_name] = exchangeActor.y
				else:
					if x_updated > exchangeActor.y:
						self.updates[demand][exchangeActor.actor_name] = x_updated
					else:
						self.updates[demand][exchangeActor.actor_name] = exchangeActor.y

			else:
				self.updates[exchange.i.demand][exchange.j.actor_name] = exchange.j.y

			if not self.re_calc:
				self.i.moves.pop()
				self.j.moves.pop()
				self.re_calc = True

		if self.re_calc:
			self.calculate()

	def __str__(self):
		return "{0}: {1}, {2}".format(round(self.gain, 9), str(self.i), str(self.j))


class AbstractModel(object):
	def __init__(self):
		self.Issues = []
		self.ActorIssues = {}
		self.Actors = {}
		self.Exchanges = []
		self.nbs = {}
		self.issue_combinations = []
		self.groups = {}
		self.moves = {}  # dict with issue,actor[move_1,move_2,move_3]
		self.nbs_denominators = {}

	def get_actor_issue(self, actor_name: str, issue: str) -> 'ActorIssue':  # TODO move to abstract class
		"""
		Getter function for an ActorIssue
		:param actor_name: the name of the actor
		:param issue: the issue to select
		:return:
		"""
		if actor_name in self.ActorIssues[issue]:
			return self.ActorIssues[issue][actor_name]
		else:
			return False

	def get_value(self, actor_name: str, issue: str, field: str):  # TODO move to abstract
		"""
		Get the value of an value for an actor/issue set
		:param actor_name:
		:param issue:
		:param field:
		:return:
		"""
		a = self.ActorIssues[issue][actor_name]

		if a is not False:

			if field is "c":
				return a.power
			if field is "s":
				return a.salience
			if field is "x":
				return a.position

	def add_actor(self, actor_name: str) -> str:
		"""
		Add an actor to the model
		:param actor_name:
		:return:
		"""
		self.Actors[actor_name] = actor_name
		return self.Actors[actor_name]

	def add_issue(self, issue_name: str):
		"""
		Add an issue to the model
		:param issue_name:
		"""
		self.Issues.append(issue_name)
		self.ActorIssues[issue_name] = {}

	def add_actor_issue(self, actor_name: str, issue_name: str, position: Decimal, salience: Decimal,
						power: Decimal) -> ActorIssue:
		"""
		Add an actor issue to the model
		:param actor_name:
		:param issue_name:
		:param position:
		:param salience:
		:param power:
		:return:
		"""
		self.ActorIssues[issue_name][actor_name] = ActorIssue(actor_name, issue_name, position, salience, power)

		return self.ActorIssues[issue_name][actor_name]

	def add_exchange(self, i: str, j: str, p: str, q: str, groups) -> None:
		"""
		Add an exchange pair to the model
		:param i:
		:param j:
		:param p:
		:param q:
		:param groups:
		:return:
		"""
		e = self.new_exchange_factory(i, j, p, q, self, groups)
		e.calculate()
		self.Exchanges.append(e)
		return e

	def calc_nbs(self):
		"""
		Calculate the nash bargaining solution for all the issue
		"""
		for issue, actor_issues in self.ActorIssues.items():
			self.nbs_denominators[issue] = calculations.calc_nbs_denominator(actor_issues)

			self.nbs[issue] = calculations.calc_nbs(actor_issues, self.nbs_denominators[issue])

	def determine_positions(self):
		"""
		Determine if the position of an actor is left or right of the Nash Bargaining Solution on an issue
		"""
		for issue, issue_nbs in self.nbs.items():
			for actorIssue in self.ActorIssues[issue].values():
				actorIssue.is_left_to_nbs(issue_nbs)

	def calc_combinations(self):
		"""
		Create a list of all possible combinations for the issues
		"""
		self.issue_combinations = combinations(self.Issues, 2)

	def determine_groups(self):
		"""
		There are 4 groups: A, B, C, and D.
		An actor is member of group A if his position on both issues is left of the NBS.
		Each actor of group A can exchange with the actors of Group D, the actors of B with C.
		"""
		for combination in self.issue_combinations:

			pos = [[], [], [], []]

			for k, actor in self.Actors.items():

				a0 = self.get_actor_issue(actor_name=actor, issue=combination[0])
				a1 = self.get_actor_issue(actor_name=actor, issue=combination[1])

				# some magic happens here: we have four possibilities and two bytes, so
				# A = 00 = 0
				# B = 01 = 1
				# C = 10 = 2
				# D = 11 = 3

				if a0 is not False and a1 is not False:
					position = a0.left | a1.left * 2
					pos[position].append(actor)

			combination_id = "{0}-{1}".format(combination[0], combination[1])

			self.groups[combination_id] = {"a": pos[0], "b": pos[1], "c": pos[2], "d": pos[3]}

			# all actors of group A and D
			for i in pos[0]:
				for j in pos[3]:
					self.add_exchange(i, j, combination[0], combination[1], groups=['a', 'd'])

					self.ActorIssues[str(combination[0])][i].group = "a"
					self.ActorIssues[str(combination[1])][j].group = "d"

			# all actors of group B and C
			for i in pos[1]:
				for j in pos[2]:
					self.add_exchange(i, j, combination[0], combination[1], groups=['b', 'c'])
					self.ActorIssues[combination[0]][i].group = "b"
					self.ActorIssues[combination[1]][j].group = "c"

	def remove_invalid_exchanges(self, res: list()) -> list():
		"""
		Removes all the invalid exchanges from a list
		:param res: a list of exchanges
		:return: a list with online valid exchanges
		"""
		length = len(self.Exchanges)

		valid_exchanges = []
		invalid_exchanges = []
		for i in range(length):

			if self.Exchanges[i].is_valid:
				self.Exchanges[i].recalculate(res)

				if self.Exchanges[i].is_valid:
					valid_exchanges.append(self.Exchanges[i])
				else:
					invalid_exchanges.append(self.Exchanges[i])

		self.Exchanges = valid_exchanges

		return invalid_exchanges

	def sort_exchanges(self):
		"""
		Abstract method
		:return:
		"""
		pass

	def highest_gain(self):
		"""
		Abstract method
		:return:
		"""
		pass
