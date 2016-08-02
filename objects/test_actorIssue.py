from unittest import TestCase

from objects.ActorIssue import ActorIssue


class TestActorIssue(TestCase):
    def test_determinePosition(self):
        position = 50
        salience = 0.25
        power = 0.10

        actorIssue = ActorIssue(position=position, power=power, salience=salience)

        self.assertEqual(actorIssue.Power, power)
        self.assertEqual(actorIssue.Salience, salience)
        self.assertEqual(actorIssue.Position, position)

        self.assertTrue(actorIssue.is_left_to_nbs(51), position)

        self.assertEqual(str(actorIssue),
                         "Actor {0} on issue {1} with position={2}, salience={3}, power={4}".format(actorIssue.Actor,
                                                                                                    actorIssue.Issue,
                                                                                                    actorIssue.Position,
                                                                                                    actorIssue.Salience,
                                                                                                    actorIssue.Power))
