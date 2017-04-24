from typing import List

from model.base import AbstractModel, AbstractExchange
from model.equalgain import EqualGainExchange
from model.randomrate import RandomRateExchange


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

    def before_loop(self, iteration: int, repetition: int = None):
        """
        The start event.
        :param iteration: int the current iteration number
        :param repetition: int only used in the RandRate model, represents the current number of repetition.
        """
        pass

    def after_loop(self, realized: List[AbstractExchange], iteration: int):
        pass

    def end_loop(self, iteration: int):
        pass

    def before_execution(self, repetition):
        pass

    def after_execution(self, repetition):
        pass

    @staticmethod
    def log(message: str):
        print(message)

    def execute_exchange(self, exchange: AbstractExchange):
        if isinstance(exchange, EqualGainExchange):
            return self._execute_equal_exchange(exchange)
        elif isinstance(exchange, RandomRateExchange):
            return self._execute_random_exchange(exchange)

    def _execute_equal_exchange(self, exchange: EqualGainExchange):
        pass

    def _execute_random_exchange(self, exchange: RandomRateExchange):
        pass

    def removed_exchanges(self, exchanges: List[AbstractExchange]):
        pass

    def finish_round(self, realized: List[AbstractExchange], iteration: int):
        pass


class Observable(Observer):
    """
    Even the Observable is and Observer, this gives us the possibility to call the right method with the correct params
    """

    def __init__(self, model_ref: AbstractModel, output_directory: str):
        self.__observers = []
        self.model_ref = model_ref
        self.output_directory = output_directory

    def register(self, observer):
        self.__observers.append(observer)

    def before_loop(self, iteration: int, repetition: int = None):
        for observer in self.__observers:
            observer.before_loop(iteration, repetition)

    def execute_exchange(self, exchange: AbstractExchange):
        for observer in self.__observers:
            observer.execute_exchange(exchange)

    def after_loop(self, realized: List[AbstractExchange], iteration: int):
        for observer in self.__observers:
            observer.after_loop(realized, iteration)

    def end_loop(self, iteration: int):
        for observer in self.__observers:
            observer.end_loop(iteration)

    def before_execution(self, repetition):
        for observer in self.__observers:
            observer.before_execution(repetition)

    def after_execution(self, repetition):
        for observer in self.__observers:
            observer.after_execution(repetition)
