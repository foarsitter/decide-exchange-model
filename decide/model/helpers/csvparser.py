# -*- coding: utf-8 -*-
import csv
from decimal import Decimal

from .. import base


class CsvParser:
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

    def __init__(self, model_ref: "base.AbstractModel"):
        self.model_ref = model_ref

    def read(self, filename, actor_whitelist=list(), issue_whitelist=list()):
        """
        The file to read
        :param issue_whitelist:
        :param actor_whitelist:
        :param filename:
        :return:
        """

        with open(filename, "rt", encoding="utf-8") as csv_file:

            # guess the document format
            dialect = csv.Sniffer().sniff(csv_file.read(1024))
            csv_file.seek(0)

            reader = csv.reader(csv_file, dialect=dialect)

            for row in reader:

                if row[0] == self.cA:
                    self.parse_row_actor(row, actor_whitelist)
                elif row[0] == self.cP:
                    self.parse_row_issue(row, issue_whitelist)
                elif row[0] == self.cD:
                    self.parse_row_d(row, actor_whitelist, issue_whitelist)
                elif row[0] == self.cM:
                    self.parse_row_m(row, issue_whitelist)
                    pass

        self.create_issues()

        for issue_id, v in self.model_ref.actor_issues.items():

            issue = self.model_ref.issues[issue_id]

            for actor_name, value in self.model_ref.actor_issues[issue_id].items():
                normalized_position = issue.normalize(
                    self.model_ref.actor_issues[issue_id][actor_name].position
                )

                self.model_ref.actor_issues[issue_id][
                    actor_name
                ].position = normalized_position

        return self.model_ref

    def parse_row_actor(self, row, whitelist=list()):
        """
        Parse the actor row
        :param whitelist: list of actors to parse, or empty list to accept all
        :param row:
        """
        from decide.model.helpers.helpers import create_key

        actor_id = create_key(row[1])

        if len(whitelist) == 0 or actor_id in whitelist:
            self.model_ref.add_actor(row[1], actor_id, comment=row[3])

    def parse_row_issue(self, row, whitelist=list()):
        """
        The csv row
        :param whitelist:
        :param row:
        """
        from decide.model.helpers.helpers import create_key

        issue_id = create_key(row[1])

        if len(whitelist) == 0 or issue_id in whitelist:
            self.model_ref.add_issue(row[1], issue_id=issue_id, comment=row[3])

    def parse_row_m(self, row, whitelist=list()):
        """
        Parse the #M row containing the dimensions of the issues
        :param whitelist:
        :param row:
        """

        from decide.model.helpers.helpers import create_key

        issue_id = create_key(row[1])

        if len(whitelist) == 0 or issue_id in whitelist:

            issue = None

            for obj in self.model_ref.issues.values():
                if obj.issue_id == issue_id:
                    issue = obj

            if not isinstance(issue, base.Issue):
                raise Exception("The issue variable it not the correct type")

            value = Decimal(row[2].replace(",", "."))

            issue.expand_lower(value)
            issue.expand_upper(value)

    def create_issues(self):
        """
        Create the issues
        """
        for issue_id, actor_issues in self.model_ref.actor_issues.items():

            if issue_id in self.model_ref.issues:

                if (
                    self.model_ref.issues[issue_id].upper is None
                    or self.model_ref.issues[issue_id].lower is None
                ):

                    for actor_name, actor_issue in actor_issues.items():
                        self.model_ref.issues[issue_id].expand_lower(
                            actor_issue.position
                        )
                        self.model_ref.issues[issue_id].expand_upper(
                            actor_issue.position
                        )

                self.model_ref.issues[issue_id].calculate_delta()
                self.model_ref.issues[issue_id].calculate_step_size()


    def parse_row_d(self, row, actor_whitelist=list(), issue_whitelist=list()):
        """
        The #D row contains the data for each actor on each issue
        :param issue_whitelist:
        :param actor_whitelist:
        :param row:
        """
        from decide.model.helpers.helpers import create_key

        actor_id = create_key(row[self.rActor])
        issue_id = create_key(row[self.rIssue])

        if (len(actor_whitelist) == 0 or actor_id in actor_whitelist) and (
            len(issue_whitelist) == 0 or issue_id in issue_whitelist
        ):

            if str(row[self.rSalience]) != "0":
                self.model_ref.add_actor_issue(
                    actor=actor_id,
                    issue=issue_id,
                    power=row[self.rPower].replace(",", "."),
                    salience=row[self.rSalience].replace(",", "."),
                    position=row[self.rPosition].replace(",", "."),
                )
