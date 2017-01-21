from unittest import TestCase

from model.base import ActorIssue


class TestActorIssue(TestCase):
    def test_determinePosition(self):
        position = 50
        salience = 0.25
        power = 0.10

        actorIssue = ActorIssue(actor_name="Test",issue_name="", position=position, power=power, salience=salience)

        self.assertEqual(actorIssue.power, power)
        self.assertEqual(actorIssue.salience, salience)
        self.assertEqual(actorIssue.position, position)

        self.assertTrue(actorIssue.is_left_to_nbs(51), position)

        self.assertEqual(str(actorIssue),
                         "Actor {0} with position={1}, salience={2}, power={3}".format(actorIssue.actor_name,
                                                                                       actorIssue.position,
                                                                                       actorIssue.salience,
                                                                                       actorIssue.power))
