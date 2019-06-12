import os

import pytest
import typesystem

from decide import input_folder
from .. import reader, types


def test_cop2():
    data, errors = reader.read(os.path.join(input_folder, 'CoP21.csv'))
    print(data)
    assert len(data) == 283


def test_parse_actor_issue_row():
    data = [types.ActorIssue.starts_with, 'Actor', 'Issue', 50, 0.5, 0.5, 'Comment', '2']
    obj = reader.parse_row(data)  # type: types.ActorIssue

    assert obj.issue == 'Issue'
    assert obj.comment == 'Comment 2', obj.comment


def test_parse_actor_issue_row_power_to_high():
    data = [types.ActorIssue.starts_with, 'Actor', 'Issue', 50, 1.5, 0.5, 'Comment', '2']

    with pytest.raises(typesystem.ValidationError):
        reader.parse_row(data)  # type: types.ActorIssue


def test_parse_actor_issue_row_power_to_low():
    data = [types.ActorIssue.starts_with, 'Actor', 'Issue', 50, -1.5, 0.5, 'Comment', '2']

    with pytest.raises(typesystem.ValidationError):
        reader.parse_row(data)  # type: types.ActorIssue

def test_squash():
    data = ['x', 'y', 'z']

    reader.squash(2, [])

    squash = reader.squash(2, data)

    assert squash[-1] == 'y z', squash[-1]

    assert reader.squash(3, data) == data, reader.squash(3, data)

