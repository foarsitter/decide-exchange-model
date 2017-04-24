import os
from typing import List

from model.base import AbstractExchange
from model.helpers.CsvWriter import CsvWriter
from model.observers.observer import Observer, Observable


class ExchangesWriter(Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable: Observable):
        super().__init__(observable)

    def _create_directory(self):
        if not os.path.exists("{0}/exchanges".format(self.output_directory)):
            os.makedirs("{0}/exchanges".format(self.output_directory))

        if not os.path.exists("{0}/exchanges/initial".format(self.output_directory)):
            os.makedirs("{0}/exchanges/initial".format(self.output_directory))

    def before_loop(self, iteration: int, repetition: int = None):
        """
        Writes all the possible exchanges to the filesystem
        :param iteration: 
        :param repetition:
        """
        self._create_directory()

        self.model_ref.sort_exchanges()

        writer = CsvWriter()
        writer.write('{0}/exchanges/initial/before.{1}.csv'.format(self.output_directory, iteration),
                     self.model_ref.exchanges)

    def after_loop(self, realized: List[AbstractExchange], iteration: int):
        """
        Writes al the executed exchanges to the filesystem
        :param realized: 
        :param iteration:
        """
        self._create_directory()

        writer = CsvWriter()
        writer.write("{0}/exchanges/round.{1}.csv".format(self.output_directory, iteration + 1), realized)
