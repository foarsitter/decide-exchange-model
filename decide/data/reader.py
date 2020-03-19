# -*- coding: utf-8 -*-
from __future__ import absolute_import

import csv
from copy import copy
from typing import List, Dict

import typesystem

from .types import PartialActor, ActorIssue, PartialIssue, IssuePosition, IssueDescription, Comment

types = {
    PartialActor.starts_with: PartialActor,
    ActorIssue.starts_with: ActorIssue,
    PartialIssue.starts_with: PartialIssue,
    IssuePosition.starts_with: IssuePosition,
    IssueDescription.starts_with: IssueDescription,
    Comment.starts_with: Comment,
}


class InputDataFile:
    def __init__(self):
        self.errors = {}
        self.rows = {}
        self.data = {}

    def add_typed_object(self, obj):

        klass = obj.__class__

        if klass in self.data:
            self.data[klass][obj] = obj
        else:
            self.data[klass] = {obj: obj}

    @classmethod
    def open(cls, filename: str) -> "InputDataFile":
        """
        Transforms a file with comma separated values to a dictionary where the key is the row number
        """

        data = cls()

        with open(filename, "rt", encoding="utf-8", errors="replace") as csv_file:
            # guess the document format
            dialect = csv.Sniffer().sniff(csv_file.read(1024))
            csv_file.seek(0)

            reader = csv.reader(csv_file, dialect=dialect)

            InputDataFile.open_reader(reader, data)

        return data

    @classmethod
    def open_reader(cls, reader, data=None):

        if not data:
            data = cls()

        data.parse_rows(reader)
        data.update_issues_with_positions()
        if data.is_valid:
            data.validate_actor_issue_positions()

        return data

    def parse_rows(self, items):
        for index, row in enumerate(items):

            # keep the original data
            self.rows[index] = row

            try:
                type_obj = csv_row_to_type(row)
                self.add_typed_object(type_obj)
            except typesystem.ValidationError as e:
                self.errors[index] = e  # collect the error for displaying purpose

    @property
    def is_valid(self):
        return len(self.errors) == 0

    @property
    def actors(self) -> Dict[str, PartialActor]:
        return self.data[PartialActor]

    @property
    def issues(self) -> Dict[str, PartialIssue]:
        return self.data[PartialIssue]

    @property
    def actor_issues(self) -> Dict[str, ActorIssue]:
        return self.data[ActorIssue]

    @property
    def issue_positions(self) -> Dict[str, IssuePosition]:
        return self.data[IssuePosition]

    def update_issues_with_positions(self):
        """
        Once the file is complete, we can update the lower an upper positions of the issue
        """

        if IssuePosition in self.data:

            for issue_position in self.issue_positions.values():

                if issue_position.issue in self.issues:

                    issue = self.issues[issue_position.issue]

                    if issue.lower is None:
                        issue.lower = issue_position.position
                    elif issue_position.position < issue.lower:
                        issue.lower = issue_position

                    if issue.upper is None:
                        issue.upper = issue_position.position
                    elif issue_position.position > issue.upper:
                        issue.upper = issue_position.position

        self.set_default_issue_positions()

    def set_default_issue_positions(self):
        for issue in self.issues.values():

            if issue.lower is None:
                issue.lower = 0

            if issue.upper is None:
                issue.upper = 100

    def validate_actor_issue_positions(self):
        """
        Validate the positions of the actor issues against the lower & upper issue bounds
        """

        # find the starting position of the actor issues, so we can show the error at the correct position
        row_index_correction = 0

        for type_class in types.values():
            if type_class in self.data and type_class != ActorIssue:
                row_index_correction += len(self.data[type_class])

        for index, actor_issue in enumerate(self.actor_issues.values(), row_index_correction + 1):

            if actor_issue.actor not in self.actors:
                self.errors[index] = typesystem.ValidationError(
                    key='actor',
                    text='{} not found in document'.format(actor_issue.actor)
                )

            if actor_issue.issue in self.issues:
                issue = self.issues[actor_issue.issue]

                try:
                    actor_issue.validate_position(issue)
                except typesystem.ValidationError as e:

                    if index in self.errors:
                        self.errors[index] = e
                    else:
                        self.errors[index] = e
            else:
                self.errors[index] = typesystem.ValidationError(
                    key='issue',
                    text='{} not found document'.format(actor_issue.issue)
                )


def csv_row_to_type(row: List[str]):
    """
    Translate a list of values to the corresponding object
    """
    key = row[0]  # the first element contains the #id field
    row = row[1:]  # the rest the row

    if key not in types.keys():
        raise Exception(f"Add key {key} to Reader.types (row row: {row}")

    row_type = types[key]

    field_names = row_type.fields.keys()

    row = squash(len(row_type.fields), row)

    obj = row_type.validate(dict(zip(field_names, row)))

    return obj


def squash(fields: int, data: List[str], delimiter=" ") -> List[str]:
    """
    Finds out how many fields there are and joins the overhead in to the lasted field

    i.e:
        The object x, y, z contains 3 field.
        The row x,y,z,a,b has 5 values.
        The values a & b will be squashed to z with the given delimiter
    """

    if fields >= len(data):
        return data

    output = copy(data)
    del output[-1]
    output[-1] = delimiter.join(data[fields - 1:])

    return output
