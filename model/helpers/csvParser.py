# -*- coding: utf-8 -*-
import csv
import os
from decimal import Decimal

import model.base


class Parser:
    # csv row identifiers
    cA = "#A"  # A = actor
    # P = issues
    cP = "#P"
    # D = the position, salience & power of an actor of an issue
    cD = "#D"
    # M = issue dimensions
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
        self.issues = {}
        self.actors = {}
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
                    self.parseRowM(row)
                    pass

        self.createIssues()

        for issue_id, v in self.data.ActorIssues.items():

            issue = self.issues.get(issue_id, model.base.Issue(name=issue_id))

            for actor_name, value in self.data.ActorIssues[issue_id].items():

                norm = issue.normalize(self.data.ActorIssues[issue_id][actor_name].position)

                self.data.ActorIssues[issue_id][actor_name].position = norm

        return self.data

    def parseRowActor(self, row):
        from model.helpers.helpers import create_key
        self.data.add_actor(create_key(row[1]))

    def parseRowIssue(self, row):

        from model.helpers.helpers import create_key
        self.data.add_issue(create_key(row[1]))

    def parseRowM(self, row):

        from model.helpers.helpers import create_key
        issue_id = create_key(row[1])

        stub = {"lower": None, "upper": None}

        s = self.issues.get(issue_id, stub)

        value = Decimal(row[2])

        if s["lower"] is None or value < s["lower"]:
            s["lower"] = value

        if s["upper"] is None or value > s["upper"]:
            s["upper"] = value

        self.issues[issue_id] = s

    def createIssues(self):

        for key, v in self.issues.items():
            i = model.base.Issue(name=key, lower=v["lower"], upper=v["upper"])
            i.calculate_delta()
            i.calculate_step_size()
            self.issues[i.id] = i

    def parseRowD(self, row):
        from model.helpers.helpers import create_key
        actor_name = create_key(row[self.rActor])
        issue_key = create_key(row[self.rIssue])

        self.data.add_actor_issue(actor_name=actor_name, issue_name=issue_key, power=row[self.rPower],
                                  salience=row[self.rSalience],
                                  position=row[self.rPosition])

    def info(self):

        print("This program accepts input with a dot (.) as decimal separator. \n"
              "Parameters:\n{0} is for defining an actor,\n"
              "{1} for an issue,\n"
              "{2} for actor values for each issue.\n"
              "We expect for {2} the following order in values: "
              "actor, issue, position, salience, power".format(self.cA, self.cP, self.cD))