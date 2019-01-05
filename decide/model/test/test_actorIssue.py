from unittest import TestCase

from decide.model import base


class TestActorIssue(TestCase):
    def test_determinePosition(self):
        position = 50
        salience = 0.25
        power = 0.10

        actor = base.Actor("Test")
        issue = base.Issue("Test")

        actorIssue = base.ActorIssue(
            actor=actor, issue=issue, position=position, power=power, salience=salience
        )

        self.assertEqual(actorIssue.power, power)
        self.assertEqual(actorIssue.salience, salience)
        self.assertEqual(actorIssue.position, position)

        self.assertTrue(actorIssue.is_left_to_nbs(51), position)
