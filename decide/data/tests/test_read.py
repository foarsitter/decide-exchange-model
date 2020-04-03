import os

import pytest
import typesystem
from decide import input_folder
from typesystem import ValidationError

from .. import reader, types


def test_cop2():
    data_file = reader.InputDataFile.open(os.path.join(input_folder, "cop21.csv"))

    assert len(data_file.errors) == 0
    assert len(data_file.rows) == 235


def test_validation_error():
    data = [
        [types.PartialActor.starts_with, "Actor", "Actor description"],
        [types.PartialIssue.starts_with, 'Issue', 'Issue description'],
        [types.IssuePosition.starts_with, 'Issue', 0, 'Issue position description'],
        [types.IssuePosition.starts_with, 'Issue', 100, 'Issue position description'],
        [types.ActorIssue.starts_with, "Actor", "Issue", 150, 0.5, 0.5, "Comment", "2", ],
    ]

    input_file = reader.InputDataFile()
    input_file.parse_rows(data)

    assert len(input_file.errors) == 0

    issue = input_file.issues['Issue']

    input_file.update_issues_with_positions()

    assert issue.lower == 0
    assert issue.upper == 100

    input_file.validate_actor_issue_positions()

    assert len(input_file.errors) == 1


def test_hash():
    issue = types.PartialIssue()
    issue.name = 'x'

    data = {issue: issue}

    assert data['x'] == issue


def test_parse_actor_issue_row():
    data = [
        types.ActorIssue.starts_with,
        "Actor",
        "Issue",
        50,
        0.5,
        0.5,
        "Comment",
        "2",
    ]
    obj = reader.csv_row_to_type(data)  # type: types.ActorIssue

    assert obj.issue == "Issue"
    assert obj.comment == "Comment 2", obj.comment


def test_parse_actor_issue_row_power_to_high():
    data = [
        types.ActorIssue.starts_with,
        "Actor",
        "Issue",
        50,
        111.5,
        100.5,
        "Comment",
        "2",
    ]

    with pytest.raises(typesystem.ValidationError):
        reader.csv_row_to_type(data)  # type: types.ActorIssue


def test_parse_actor_issue_row_power_to_low():
    data = [
        types.ActorIssue.starts_with,
        "Actor",
        "Issue",
        50,
        -1.5,
        0.5,
        "Comment",
        "2",
    ]

    with pytest.raises(typesystem.ValidationError):
        reader.csv_row_to_type(data)  # type: types.ActorIssue


def test_squash():
    data = ["x", "y", "z"]

    reader.squash(2, [])

    squash = reader.squash(2, data)

    assert squash[-1] == "y z", squash[-1]

    assert reader.squash(3, data) == data, reader.squash(3, data)


def test_issue_validate_interval():
    issue = types.PartialIssue()
    issue.lower = 0
    issue.upper = 100

    issue.validate_interval()

    with pytest.raises(ValidationError):
        issue.lower = 120
        issue.validate_interval()


def test_actor_issue_validate_position():
    issue = types.PartialIssue()
    issue.lower = 0
    issue.upper = 100

    actor_issue = types.ActorIssue()
    actor_issue.position = 5

    actor_issue.validate_position(issue)

    with pytest.raises(ValidationError):
        actor_issue.position = 999
        actor_issue.validate_position(issue)
