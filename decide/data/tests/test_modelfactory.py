from decide.data import types, reader
from decide.data.modelfactory import ModelFactory
from decide.model.equalgain import EqualGainModel


def test_issue_filter():
    data_file = reader.InputDataFile()
    data_file.parse_rows([
        [types.PartialIssue.starts_with, 'Issue #1', 'description'],
        [types.PartialIssue.starts_with, 'Issue #2', 'description'],
        [types.PartialIssue.starts_with, 'Issue #3', 'description'],
    ])

    factory = ModelFactory(data_file, issue_whitelist=['Issue #2', 'Issue #3'])

    assert len(factory.filter_issues()) == 2
    assert 'Issue #1' not in factory.filter_issues()


def test_actor_filter():
    data_file = reader.InputDataFile()
    data_file.parse_rows([
        [types.PartialActor.starts_with, 'Actor #1', 'description'],
        [types.PartialActor.starts_with, 'Actor #2', 'description'],
        [types.PartialActor.starts_with, 'Actor #3', 'description'],
    ])

    factory = ModelFactory(data_file, actor_whitelist=['Actor #2', 'Actor #3'])

    assert len(factory.filter_actors()) == 2
    assert 'Actor #1' not in factory.filter_actors()


def test_actor_issue_filter():
    actor_1 = 'Actor #1'
    actor_2 = 'Actor #2'
    actor_3 = 'Actor #3'

    actors = [actor_1, actor_2, actor_3]
    actor_whitelist = actors[1:]

    issue_1 = 'Issue #1'
    issue_2 = 'Issue #2'
    issue_3 = 'Issue #3'

    issues = [issue_1, issue_2, issue_3]
    issue_whitelist = issues[1:]

    data = []

    for issue in issues:
        data.append([types.PartialIssue.starts_with, issue, issue])

    for actor in actors:
        data.append([types.PartialActor.starts_with, actor, actor])

        for issue in issues:
            data.append([types.ActorIssue.starts_with, actor, issue, 100, 1, 1])

    data_file = reader.InputDataFile()
    data_file.parse_rows(data)
    data_file.update_issues_with_positions()

    assert len(data_file.errors) == 0
    assert len(data_file.actors) == 3
    assert len(data_file.issues) == 3
    assert len(data_file.actor_issues) == 9

    factory = ModelFactory(
        date_file=data_file,
        actor_whitelist=actor_whitelist,
        issue_whitelist=issue_whitelist
    )

    filtered_issues = factory.filter_issues()
    filtered_actors = factory.filter_actors()

    assert len(filtered_issues) == 2
    assert len(filtered_actors) == 2

    filtered_actor_issues = factory.filter_actor_issues(filtered_actors, filtered_issues)

    assert len(filtered_actor_issues) == 4

    model = factory(EqualGainModel)

    assert len(model.issues) == len(filtered_issues)
    assert len(model.actors) == len(filtered_actors)
    assert len(model.actor_issues) == 2

    count = sum(len(x) for x in model.actor_issues.values())

    assert count == len(filtered_actor_issues)
    assert isinstance(model, EqualGainModel)
