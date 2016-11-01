class Observable:
    REMOVED = "REMOVED"
    EXECUTED = "EXECUTED"
    LOG = "LOG"
    FINISHED_ROUND = "FR"
    CLOSE = "CLOSE"

    def __init__(self):
        self.__observers = []

    def register(self, observer):
        self.__observers.append(observer)

    def notify(self, *args, **kwargs):
        for observer in self.__observers:
            observer.update(self, *args, **kwargs)


class Observer:
    def __init__(self, observable):
        observable.register(self)

    def update(self, observable, *args, **kwargs):
        pass
