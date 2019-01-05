from unittest import TestCase

from decide.model.base import Actor, Issue


class TestIssue(TestCase):
    def test_actor_functions(self):
        actor1 = Actor("Test")
        actor2 = Actor("test")
        actor3 = Actor("Test 123")

        # actor comparison happens on the key attribute. So the following is correct
        self.assertEqual(actor1, actor1)
        self.assertEqual(actor1, actor2)
        self.assertNotEqual(actor1, actor3)

        # naming functions
        self.assertEqual(actor1.name, "Test")
        self.assertEqual(actor1.actor_id, "test")
        self.assertEqual(actor2, "test")
        self.assertEqual(actor3.name, "Test 123")
        self.assertEqual(actor3.actor_id, "test123")
        self.assertEqual(str(actor3), actor3.name)

        self.assertFalse(actor1 is None)

        with self.assertRaises(NotImplementedError):
            self.assertEqual(actor1, Issue("mock"))

        # testing hash index functions
        store = {actor1: actor1, actor2: actor2, actor3: actor3}

        self.assertEqual(store[actor1], actor1)
        self.assertEqual(store[actor2], actor1)
        self.assertNotEqual(store[actor3], actor1)

        self.assertTrue(actor1 < actor3)

        with self.assertRaises(ValueError):
            self.assertTrue(actor1 < Issue("Mock"))
