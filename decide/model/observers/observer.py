from pathlib import Path

from decide.log import logger
from decide.model import base
from decide.model import equalgain
from decide.model import randomrate


class Observer:
    """The main event Object containing all the event methods.

    Order of events:

    before_repetitions()
    before_iterations()
    before_loop()
    after_loop()
    end_loop()
    after_iterations()
    after_repetitions()

    """

    def __init__(self, observable: "Observable") -> None:
        """:type observable: Observable reference to the main event handler"""
        observable.register(self)
        self.model_ref = observable.model_ref
        self.output_directory: Path = observable.output_directory

    def update(self, observable, notification_type, **kwargs) -> None:
        pass

    def before_model(self) -> None:
        pass

    def after_model(self) -> None:
        pass

    def before_loop(self, iteration: int, repetition: int) -> None:
        """Before the start of a single round.
        The actors are still on there starting position.
        Next event: after_loop
        :param iteration: int the current iteration number
        :param repetition: int only used in the RandRate model, represents the current number of repetition.
        """

    def after_loop(
        self,
        realized: list[base.AbstractExchange],
        iteration: int,
        repetition: int,
    ) -> None:
        """After all exchanges are executed. There are no potential exchanges left, but the model reference to actor
        issues is still on there starting position.
        Next event: end_loop
        :param realized:
        :param iteration:
        :param repetition:
        :return:
        """

    def end_loop(self, iteration: int, repetition: int) -> None:
        """At the end of a loop with the final positions of the actors, but before the new_start_position()'s are calculated.
        The next event: before_loop.
        """

    def before_iterations(self, repetition) -> None:
        """Before a set of loops starts."""

    def after_iterations(self, repetition) -> None:
        """After a set of loops are finished."""

    def before_repetitions(self, repetitions, iterations, randomized_value=None) -> None:
        """First event
        :return:
        """

    def after_repetitions(self) -> None:
        """Last event."""

    @staticmethod
    def log(message: str) -> None:
        logger.info(message)

    def execute_exchange(self, exchange: base.AbstractExchange) -> None:
        if isinstance(exchange, equalgain.EqualGainExchange):
            return self._execute_equal_exchange(exchange)
        if isinstance(exchange, randomrate.RandomRateExchange):
            return self._execute_random_exchange(exchange)
        return None

    def _execute_equal_exchange(self, exchange: equalgain.EqualGainExchange) -> None:
        pass

    def _execute_random_exchange(self, exchange: randomrate.RandomRateExchange) -> None:
        pass

    def removed_exchanges(self, exchanges: list[base.AbstractExchange]) -> None:
        pass


class Observable(Observer):
    """Even the Observable is and Observer, this gives us the possibility to call the right method with the correct params."""

    def __init__(self, model_ref: base.AbstractModel, output_directory: Path) -> None:
        self.__observers = []
        self.model_ref = model_ref
        self.output_directory: Path = output_directory

    def update_model_ref(self, model) -> None:
        self.model_ref = model
        for observer in self.__observers:
            observer.model_ref = model

    def update_output_directory(self, output_directory) -> None:
        self.output_directory = output_directory

        for observer in self.__observers:
            observer.output_directory = output_directory

    def register(self, observer) -> None:
        self.__observers.append(observer)

    def before_model(self) -> None:
        for observer in self.__observers:
            observer.before_model()

    def before_repetitions(self, repetitions, iterations, randomized_value=None) -> None:
        for observer in self.__observers:
            observer.before_repetitions(repetitions, iterations, randomized_value)

    def before_iterations(self, repetition) -> None:
        for observer in self.__observers:
            observer.before_iterations(repetition)

    def before_loop(self, iteration: int, repetition: int | None = None) -> None:
        for observer in self.__observers:
            observer.before_loop(iteration, repetition)

    def execute_exchange(self, exchange: base.AbstractExchange) -> None:
        for observer in self.__observers:
            observer.execute_exchange(exchange)

    def after_loop(
        self,
        realized: list[base.AbstractExchange],
        iteration: int,
        repetition: int,
    ) -> None:
        for observer in self.__observers:
            observer.after_loop(realized, iteration, repetition)

    def end_loop(self, iteration: int, repetition: int) -> None:
        for observer in self.__observers:
            observer.end_loop(iteration, repetition)

    def after_iterations(self, repetition) -> None:
        for observer in self.__observers:
            observer.after_iterations(repetition)

    def after_repetitions(self) -> None:
        for observer in self.__observers:
            observer.after_repetitions()

    def after_model(self) -> None:
        for observer in self.__observers:
            observer.after_model()
