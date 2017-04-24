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

    def __init__(self, model_ref):
        self.data = model_ref

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

        for issue_id, v in self.data.actor_issues.items():

            issue = self.data.issues[issue_id]

            for actor_name, value in self.data.actor_issues[issue_id].items():
                normalized_position = issue.normalize(self.data.actor_issues[issue_id][actor_name].position)

                self.data.actor_issues[issue_id][actor_name].position = normalized_position

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
        self.data.add_issue(row[1])

    def parse_row_m(self, row):
        """
        Parse the #M row
        :param row:
        """
        from model.helpers.helpers import create_key
        issue_id = create_key(row[1])

        issue = self.data.issues[issue_id]

        value = Decimal(row[2].replace(",", "."))

        issue.expand_lower(value)
        issue.expand_upper(value)

    def create_issues(self):
        """
        Create the issues
        """
        for issue_id, actor_issues in self.data.actor_issues.items():

            if issue_id in self.data.issues:

                if self.data.issues[issue_id].upper is None or self.data.issues[issue_id].lower is None:

                    for actor_name, actor_issue in actor_issues.items():
                        self.data.issues[issue_id].expand_lower(actor_issue.position)
                        self.data.issues[issue_id].expand_upper(actor_issue.position)

                self.data.issues[issue_id].calculate_delta()
                self.data.issues[issue_id].calculate_step_size()
            else:
                raise Exception('fix this!')


    def parse_row_d(self, row):
        """
        The #D row contains the ... TODO
        :param row:
        """
        from model.helpers.helpers import create_key
        actor_id = create_key(row[self.rActor])
        issue_id = create_key(row[self.rIssue])

        self.data.add_actor_issue(actor_id=actor_id, issue_id=issue_id, power=row[self.rPower].replace(",", "."),
                                  salience=row[self.rSalience].replace(",", "."),
                                  position=row[self.rPosition].replace(",", "."))
