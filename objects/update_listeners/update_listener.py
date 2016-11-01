from objects.update_listeners.observer import Observer, Observable


class Updater(Observer):
    def update(self, observable, *args, **kwargs):

        if args[0] == Observable.EXECUTED:
            self.executed_exchange(args[1], args[2])
        elif args[0] == Observable.REMOVED:
            self.removed_exchanges(args[1], args[2])

    def executed_exchange(self, model, exchange):
        pass

    def removed_exchanges(self, model, exchanges):
        pass


class Logger(Observer):
    def update(self, observable, *args, **kwargs):
        if args[0] == Observable.LOG:
            print('LOG:', args[1])
