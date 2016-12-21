from unittest import TestCase

from model.helpers import csvParser


class TestParser(TestCase):
    def setUp(self):
        self.parser = csvParser.Parser()

    def test_read(self):
        model = self.parser.read("data/data_short.csv")

        self.assertEqual(len(model.Actors), 15)
        self.assertEqual(len(model.Issues), 3)
        self.assertEqual(len(model.ActorIssues), 3)
        self.assertEqual(len(model.ActorIssues[model.Issues[0]]), 15)
