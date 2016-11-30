import csv
from typing import List

from objects.EqualExchange import Exchange


class csvWriter:
	def __init__(self):
		self.var = "x"
		self.file = "output"

	def write(self, filename, realized: List[Exchange]):
		with open(filename, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile, delimiter=';')

			writer.writerow(self.create_heading(realized[0]))

			for exchange in realized:
				writer.writerow(self.create_row(exchange))

	def create_row(self, exchange: Exchange):

		if isinstance(exchange, Exchange):
			return [
				# the actors
				exchange.i.actor_name,
				exchange.i.supply,
				exchange.j.actor_name,
				exchange.j.supply,
				exchange.gain,
				# the move of i
				exchange.i.x,
				exchange.i.move,
				exchange.i.y,
				exchange.i.opposite_actor.x_demand,
				# the move of j
				exchange.j.x,
				exchange.j.move,
				exchange.j.y,
				exchange.j.opposite_actor.x_demand,
				# other info.
				exchange.dp,
				exchange.dq,
				exchange.i.nbs_0,
				exchange.i.nbs_1,
				exchange.j.nbs_0,
				exchange.j.nbs_1]
		else:
			return [
				# the actors
				exchange.i.actor_name,
				exchange.i.supply,
				exchange.i.eu,
				exchange.i.is_highest_gain,
				exchange.j.actor_name,
				exchange.j.supply,
				exchange.j.eu,
				exchange.j.is_highest_gain,
				# the move of i
				exchange.i.x,
				exchange.i.move,
				exchange.i.y,
				exchange.i.opposite_actor.x_demand,
				# the move of j
				exchange.j.x,
				exchange.j.move,
				exchange.j.y,
				exchange.j.opposite_actor.x_demand,
				# other info.
				exchange.dp,
				exchange.dq,
				exchange.i.nbs_0,
				exchange.i.nbs_1,
				exchange.j.nbs_0,
				exchange.j.nbs_1]

	@staticmethod
	def create_heading(exchange: Exchange):

		if isinstance(exchange, Exchange):
			return [
				# the actors
				"actor_name",  # exchange.i.actor_name,
				"supply",  # exchange.i.supply,
				"actor_name",  # exchange.j.actor_name,
				"supply",  # exchange.j.supply,
				"gain",  # exchange.gain,
				# the move of i
				"supply",  # exchange.i.x,
				"move",  # exchange.i.move,
				"y",  # exchange.i.y,
				"demand",  # exchange.i.opposite_actor.x_demand,
				# the move of j
				"supply",  # exchange.j.x,
				"move",  # exchange.j.move,
				"y",  # exchange.j.y,
				"demand",  # exchange.j.opposite_actor.x_demand,
				# other info.
				"dp",  # exchange.dp,
				"dq",  # exchange.dq,
				"nbs_0",  # exchange.i.nbs_0,
				"nbs_1",  # exchange.i.nbs_1,
				"nbs_0",  # exchange.j.nbs_0,
				"nbs_1"]  # exchange.j.nbs_1]

		return [
			# the actors
			"actor_name",  # exchange.i.actor_name,
			"supply",  # exchange.i.suply,
			"gain",
			"highest",
			"actor_name",  # exchange.j.actor_name,
			"supply",  # exchange.j.supply,
			"gain",
			"highest",
			# the move of i
			"supply",  # exchange.i.x,
			"move",  # exchange.i.move,
			"y",  # exchange.i.y,
			"demand",  # exchange.i.opposite_actor.x_demand,
			# the move of j
			"supply",  # exchange.j.x,
			"move",  # exchange.j.move,
			"y",  # exchange.j.y,
			"demand",  # exchange.j.opposite_actor.x_demand,
			# other info.
			"dp",  # exchange.dp,
			"dq",  # exchange.dq,
			"nbs_0",  # exchange.i.nbs_0,
			"nbs_1",  # exchange.i.nbs_1,
			"nbs_0",  # exchange.j.nbs_0,
			"nbs_1"]  # exchange.j.nbs_1]

# nbs info
