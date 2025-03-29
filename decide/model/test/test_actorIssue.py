from unittest import TestCase

from decide.model import base


class TestActorIssue(TestCase):
    def test_determinePosition(self) -> None:
        position = 50
        salience = 0.25
        power = 0.10

        actor = base.Actor("Test")
        issue = base.Issue("Test")

        actorIssue = base.ActorIssue(
            actor=actor,
            issue=issue,
            position=position,
            power=power,
            salience=salience,
        )

        assert actorIssue.power == power
        assert actorIssue.salience == salience
        assert actorIssue.position == position

        assert actorIssue.is_left_to_nbs(51), position
