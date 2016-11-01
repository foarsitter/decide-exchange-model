from unittest import TestCase

from objects.Actor import Actor


class TestActor(TestCase):
    def test_init(self):
        name = "TestActor"
        actor = Actor(name)

        self.assertEqual(actor.Name, name.lower())
        self.assertEqual(str(actor), name.lower())
