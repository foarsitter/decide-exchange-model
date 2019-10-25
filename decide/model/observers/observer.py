import logging
from typing import List

from .. import base
from .. import equalgain
from .. import randomrate


class Observer(object):
    """
    The main event Object containing all the event methods.

    Order of events:

    before_repetitions()
    before_iterations()
    before_loop()
    after_loop()
    end_loop()
    after_iterations()
    after_repetitions()

    """

    def __init__(self, observable: "Observable"):
        """
        :type observable: Observable reference to the main event handler
        """
        observable.register(self)
        self.model_ref = observable.model_ref
        self.output_directory = observable.output_directory

    def update(self, observable, notification_type, **kwargs):
        pass

    def before_model(self):
        pass

    def after_model(self):
        pass

    def before_loop(self, iteration: int, repetition: int):
        """
        Before the start of a single round.
        The actors are still on there starting position.
        Next event: after_loop
        :param iteration: int the current iteration number
        :param repetition: int only used in the RandRate model, represents the current number of repetition.
        """
        pass

    def after_loop(
        self, realized: List[base.AbstractExchange], iteration: int, repetition: int
    ):
        """
        After all exchanges are executed. There are no potential exchanges left, but the model reference to actor
        issues is still on there starting position.
        Next event: end_loop
        :param realized:
        :param iteration:
        :param repetition:
        :return:
        """
        pass

    def end_loop(self, iteration: int, repetition: int):
        """
        At the end of a loop with the final positions of the actors, but before the new_start_position()'s are calculated.
        The next event: before_loop.
        """
        pass

    def before_iterations(self, repetition):
        """
        Before a set of loops starts
        """
        pass

    def after_iterations(self, repetition):
        """
        After a set of loops are finished
        """
        pass

    def before_repetitions(self, repetitions, iterations, randomized_value=None):
        """
        First event
        :return:
        """
        pass

    def after_repetitions(self):
        """
        Last event
        """
        pass

    @staticmethod
    def log(message: str):
        logging.info(message)

    def execute_exchange(self, exchange: base.AbstractExchange):
        if isinstance(exchange, equalgain.EqualGainExchange):
            return self._execute_equal_exchange(exchange)
        elif isinstance(exchange, randomrate.RandomRateExchange):
            return self._execute_random_exchange(exchange)

    def _execute_equal_exchange(self, exchange: equalgain.EqualGainExchange):
        pass

    def _execute_random_exchange(self, exchange: randomrate.RandomRateExchange):
        pass

    def removed_exchanges(self, exchanges: List[base.AbstractExchange]):
        pass


class Observable(Observer):
    """
    Even the Observable is and Observer, this gives us the possibility to call the right method with the correct params
    """

    def __init__(self, model_ref: base.AbstractModel, output_directory: str):
        self.__observers = []
        self.model_ref = model_ref
        self.output_directory = output_directory

    def update_model_ref(self, model):
        self.model_ref = model
        for observer in self.__observers:
            observer.model_ref = model

    def update_output_directory(self, output_directory):
        self.output_directory = output_directory

        for observer in self.__observers:
            observer.output_directory = output_directory

    def register(self, observer):
        self.__observers.append(observer)

    def before_model(self):
        for observer in self.__observers:
            observer.before_model()

    def before_repetitions(self, repetitions, iterations, randomized_value=None):
        for observer in self.__observers:
            observer.before_repetitions(repetitions, iterations, randomized_value)

    def before_iterations(self, repetition):
        for observer in self.__observers:
            observer.before_iterations(repetition)

    def before_loop(self, iteration: int, repetition: int = None):
        for observer in self.__observers:
            observer.before_loop(iteration, repetition)

    def execute_exchange(self, exchange: base.AbstractExchange):
        for observer in self.__observers:
            observer.execute_exchange(exchange)

    def after_loop(
        self, realized: List[base.AbstractExchange], iteration: int, repetition: int
    ):
        for observer in self.__observers:
            observer.after_loop(realized, iteration, repetition)

    def end_loop(self, iteration: int, repetition: int):
        for observer in self.__observers:
            observer.end_loop(iteration, repetition)

    def after_iterations(self, repetition):
        for observer in self.__observers:
            observer.after_iterations(repetition)

    def after_repetitions(self):
        for observer in self.__observers:
            observer.after_repetitions()

    def after_model(self):
        for observer in self.__observers:
            observer.after_model()
