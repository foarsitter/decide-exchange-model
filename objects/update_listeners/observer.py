class Observable:
    REMOVED = "REMOVED"
    EXECUTED = "EXECUTED"
    LOG = "LOG"
    FINISHED_ROUND = "FR"
    CLOSE = "CLOSE"
    START_ROUND = "SR"

    def __init__(self):
        self.__observers = []

    def register(self, observer):
        self.__observers.append(observer)

    def notify(self, *args, **kwargs):
        for observer in self.__observers:
            observer.update(self, args[0], **kwargs)


class Observer:
    def __init__(self, observable):
        observable.register(self)

    def update(self, observable, notification_type: int, **kwargs):
        pass
