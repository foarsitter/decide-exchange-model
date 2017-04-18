from unittest import TestCase

from model.equalgain import EqualGainModel
from model.helpers import csvParser


class TestParser(TestCase):
    def setUp(self):
        self.parser = csvParser.Parser(EqualGainModel())

    def test_read(self):
        model = self.parser.read('data/input/data_short.csv')

        self.assertEqual(len(model.actors), 15)
        self.assertEqual(len(model.issues), 3)
        self.assertEqual(len(model.actor_issues), 3)
        self.assertEqual(len(model.actor_issues[model.issues['mrv'].id]), 15)
