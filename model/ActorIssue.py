from decimal import *


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
