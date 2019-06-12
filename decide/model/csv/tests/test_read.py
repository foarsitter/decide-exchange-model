import os

from decide import input_folder
from .. import reader, types


def test_cop2():
    data = reader.read(os.path.join(input_folder, 'CoP21.csv'))
    print(data)
    assert len(data.keys()) == 4


def test_parse_actor_issue_row():
    data = [types.ActorIssue.starts_with, 'Actor', 'Issue', 50, 0.5, 0.5, 'Comment', '2']
    obj = reader.parse_row(data)  # type: types.ActorIssue

    assert obj.issue == 'Issue'
    assert obj.comment == 'Comment 2', obj.comment


def test_squash():
    data = ['x', 'y', 'z']
    squash = reader.squash(1, data)

    reader.squash(1, [])

    assert squash[-1] == 'y z', squash

    assert reader.squash(3, data) == data, reader.squash(3, data)

