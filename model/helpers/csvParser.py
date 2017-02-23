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

    def read(self, filename):
        """
        The file to read
        :param filename:
        :return:
        """
        if not filename.startswith("/"):
            filename = "{1}".format(os.path.dirname(os.path.abspath(__file__)), filename)

        with open(filename, 'rt') as csv_file:

            # guess the document format
            dialect = csv.Sniffer().sniff(csv_file.read(1024))
            csv_file.seek(0)

            reader = csv.reader(csv_file, dialect=dialect)

            for row in reader:

                if row[0] == self.cA:
                    self.parse_row_actor(row)
                elif row[0] == self.cP:
                    self.parse_row_issue(row)
                elif row[0] == self.cD:
                    self.parse_row_d(row)
                elif row[0] == self.cM:
                    self.parse_row_m(row)
                    pass

        self.create_issues()

        for issue_id, v in self.data.ActorIssues.items():

            issue = self.issues.get(issue_id, model.base.Issue(name=issue_id))

            for actor_name, value in self.data.ActorIssues[issue_id].items():
                norm = issue.normalize(self.data.ActorIssues[issue_id][actor_name].position)

                self.data.ActorIssues[issue_id][actor_name].position = norm

        return self.data

    def parse_row_actor(self, row):
        """
        Parse the actor row
        :param row:
        """
        from model.helpers.helpers import create_key
        self.data.add_actor(create_key(row[1]))

    def parse_row_issue(self, row):
        """
        The csv row
        :param row:
        """
        from model.helpers.helpers import create_key
        self.data.add_issue(create_key(row[1]))

    def parse_row_m(self, row):
        """
        Parse the #M row
        :param row:
        """
        from model.helpers.helpers import create_key
        issue_id = create_key(row[1])

        stub = {"lower": None, "upper": None}

        s = self.issues.get(issue_id, stub)

        value = Decimal(row[2].replace(",", "."))

        if s["lower"] is None or value < s["lower"]:
            s["lower"] = value

        if s["upper"] is None or value > s["upper"]:
            s["upper"] = value

        self.issues[issue_id] = s

    def create_issues(self):
        """
        Create the issues
        """
        for key, v in self.issues.items():
            i = model.base.Issue(name=key, lower=v["lower"], upper=v["upper"])
            i.calculate_delta()
            i.calculate_step_size()
            self.issues[i.id] = i

    def parse_row_d(self, row):
        """
        The #D row contains the ... TODO
        :param row:
        """
        from model.helpers.helpers import create_key
        actor_name = create_key(row[self.rActor])
        issue_key = create_key(row[self.rIssue])

        self.data.add_actor_issue(actor_name=actor_name, issue_name=issue_key, power=row[self.rPower].replace(",", "."),
                                  salience=row[self.rSalience].replace(",", "."),
                                  position=row[self.rPosition].replace(",", "."))
