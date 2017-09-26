from unittest import TestCase

from model.base import Actor


class TestIssue(TestCase):

    def test___eq__(self):

        actor = Actor("test")
        actor2 = Actor("test")

        self.assertTrue(actor == actor)
        self.assertTrue(actor2 == actor)
