# -*- coding: utf-8 -*-
import csv
import os
from decimal import Decimal


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

    model_ref = None

    def __init__(self, model_ref):
        self.model_ref = model_ref

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

        for issue_id, v in self.model_ref.actor_issues.items():

            issue = self.model_ref.issues[issue_id]

            for actor_name, value in self.model_ref.actor_issues[issue_id].items():
                normalized_position = issue.normalize(self.model_ref.actor_issues[issue_id][actor_name].position)

                self.model_ref.actor_issues[issue_id][actor_name].position = normalized_position

        return self.model_ref

    def parse_row_actor(self, row):
        """
        Parse the actor row
        :param row:
        """
        from model.helpers.helpers import create_key
        self.model_ref.add_actor(create_key(row[1]))

    def parse_row_issue(self, row):
        """
        The csv row
        :param row:
        """
        self.model_ref.add_issue(row[1])

    def parse_row_m(self, row):
        """
        Parse the #M row
        :param row:
        """
        from model.helpers.helpers import create_key
        issue_id = create_key(row[1])

        issue = self.model_ref.issues[issue_id]

        value = Decimal(row[2].replace(",", "."))

        issue.expand_lower(value)
        issue.expand_upper(value)

    def create_issues(self):
        """
        Create the issues
        """
        for issue_id, actor_issues in self.model_ref.actor_issues.items():

            if issue_id in self.model_ref.issues:

                if self.model_ref.issues[issue_id].upper is None or self.model_ref.issues[issue_id].lower is None:

                    for actor_name, actor_issue in actor_issues.items():
                        self.model_ref.issues[issue_id].expand_lower(actor_issue.position)
                        self.model_ref.issues[issue_id].expand_upper(actor_issue.position)

                self.model_ref.issues[issue_id].calculate_delta()
                self.model_ref.issues[issue_id].calculate_step_size()
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

        self.model_ref.add_actor_issue(actor=actor_id, issue=issue_id, power=row[self.rPower].replace(",", "."),
                                       salience=row[self.rSalience].replace(",", "."),
                                       position=row[self.rPosition].replace(",", "."))
