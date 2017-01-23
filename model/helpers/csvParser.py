# -*- coding: utf-8 -*-
import csv
import os


class Parser:
	# csv row identifiers
	cA = "#A"  # A = actor
	# P = issues
	cP = "#P"
	# D = the position, salience & power of an actor of an issue
	cD = "#D"
	# M = issue dimensions (not used in the program)
	cM = "#M"

	cI = "#/"

	# /	actor	issue	position	salience	power
	rActor = 1
	rIssue = 2
	rPosition = 3
	rSalience = 4
	rPower = 5

	data = None

	def __init__(self, model):
		self.data = model

		print(self.info())

	def read(self, filename):

		if not filename.startswith("/"):
			filename = "{1}".format(os.path.dirname(os.path.abspath(__file__)), filename)

		with open(filename, 'rt') as csv_file:
			reader = csv.reader(csv_file, delimiter=';')

			for row in reader:

				if row[0] == self.cA:
					self.parseRowActor(row)
				elif row[0] == self.cP:
					self.parseRowIssue(row)
				elif row[0] == self.cD:
					self.parseRowD(row)
				elif row[0] == self.cM:
					pass

		return self.data

	def parseRowActor(self, row):
		self.data.add_actor(row[1])

	def parseRowIssue(self, row):
		self.data.add_issue(row[1])

	def parseRowD(self, row):
		self.data.add_actor_issue(actor_name=row[self.rActor], issue_name=row[self.rIssue], power=row[self.rPower],
								  salience=row[self.rSalience],
								  position=row[self.rPosition])

	def info(self):

		print("This program accepts input with a dot (.) as decimal separator. \n"
			  "Parameters:\n{0} is for defining an actor,\n"
			  "{1} for an issue,\n"
			  "{2} for actor values for each issue.\n"
			  "We expect for {2} the following order in values: "
			  "actor, issue, position, salience, power".format(self.cA, self.cP, self.cD))
