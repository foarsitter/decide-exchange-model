import os
from typing import List

from .. import base
from ..helpers import csvwriter
from ..observers import observer


class ExchangesWriter(observer.Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable: observer.Observable):
        super().__init__(observable)

    def _create_directory(self, repetition: int):
        if not os.path.exists("{0}/exchanges/{1}".format(self.output_directory, repetition)):
            os.makedirs("{0}/exchanges/{1}".format(self.output_directory, repetition))

        if not os.path.exists("{0}/exchanges/{1}/initial".format(self.output_directory, repetition)):
            os.makedirs("{0}/exchanges/{1}/initial".format(self.output_directory, repetition))

    def before_iterations(self, repetition):
        self._create_directory(repetition)

    def before_loop(self, iteration: int, repetition: int = None):
        """
        Writes all the possible exchanges to the filesystem
        :param iteration: 
        :param repetition:`
        """

        self.model_ref.sort_exchanges()

        salt = self._get_salt

        writer = csvwriter.CsvWriter()
        writer.write(
            '{0}/exchanges/{2}/initial/before.{1}.{2}.csv'.format(self.output_directory, iteration, repetition, salt),
            self.model_ref.exchanges)

    def after_loop(self, realized: List[base.AbstractExchange], iteration: int, repetition: int):
        """
        Writes al the executed exchanges to the filesystem
        :param repetition: 
        :param realized: 
        :param iteration:
        """

        salt = self._get_salt

        writer = csvwriter.CsvWriter()
        writer.write(
            "{0}/exchanges/{2}/round.{1}.{3}.csv".format(self.output_directory, iteration + 1, repetition, salt),
            realized)

    @property
    def _get_salt(self):
        model_name = 'random'
        from decide.model.equalgain import EqualGainModel
        if isinstance(self.model_ref, EqualGainModel):
            model_name = 'equal'
            if self.model_ref.randomized_value is not None:
                model_name += '-' + str(round(self.model_ref.randomized_value, 2))

        return model_name