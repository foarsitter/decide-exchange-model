from unittest import TestCase

from objects.Actor import Actor


class TestActor(TestCase):
    def test_init(self):
        name = "TestActor"
        actor = Actor(name)

        self.assertEqual(actor.Name, name)
        self.assertEqual(str(actor), name)
