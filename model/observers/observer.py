from typing import List

from .. import base
from .. import equalgain
from .. import randomrate


class Observer(object):
    """
    The main event Object containing all the event methods. 
    """

    def __init__(self, observable: 'Observable'):
        """
        Init
        :param observable: Observable reference to the main event handler
        :param model_ref:  AbstractModel this reference is almost always needed
        """
        observable.register(self)
        self.model_ref = observable.model_ref
        self.output_directory = observable.output_directory

    def update(self, observable, notification_type, **kwargs):
        pass

    def before_loop(self, iteration: int, repetition: int):
        """
        The start event.
        :param iteration: int the current iteration number
        :param repetition: int only used in the RandRate model, represents the current number of repetition.
        """
        pass

    def finish_round(self, realized: List[base.AbstractExchange], iteration: int, repetition: int):
        pass

    def after_loop(self, realized: List[base.AbstractExchange], iteration: int, repetition: int):
        pass

    def end_loop(self, iteration: int, repetition: int):
        pass

    def before_iterations(self, repetition):
        pass

    def after_iterations(self, repetition):
        pass

    def before_repetitions(self):
        pass

    def after_repetitions(self):
        pass

    @staticmethod
    def log(message: str):
        print(message)

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

    def register(self, observer):
        self.__observers.append(observer)

    def before_loop(self, iteration: int, repetition: int = None):
        for observer in self.__observers:
            observer.before_loop(iteration, repetition)

    def execute_exchange(self, exchange: base.AbstractExchange):
        for observer in self.__observers:
            observer.execute_exchange(exchange)

    def after_loop(self, realized: List[base.AbstractExchange], iteration: int, repetition: int):
        for observer in self.__observers:
            observer.after_loop(realized, iteration, repetition)

    def end_loop(self, iteration: int, repetition: int):
        for observer in self.__observers:
            observer.end_loop(iteration, repetition)

    def before_iterations(self, repetition):
        for observer in self.__observers:
            observer.before_iterations(repetition)

    def after_iterations(self, repetition):
        for observer in self.__observers:
            observer.after_iterations(repetition)

    def after_repetitions(self):
        for observer in self.__observers:
            observer.after_repetitions()

    def before_repetitions(self):
        for observer in self.__observers:
            observer.before_repetitions()
