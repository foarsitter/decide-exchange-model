from objects.update_listeners.observer import Observable, Observer
import calculations
import itertools
from csvWriter import csvWriter
import os

class ExchangesWriter(Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable, model, current_file):
        super(ExchangesWriter, self).__init__(observable=observable)
        self.current_file = current_file

        self.realized = []
        self.deleted = []

    def setup(self):
        self.realized = []
        self.deleted = []

    def update(self, observable, *args, **kwargs):

        if args[0] == Observable.EXECUTED:
            self.add_exchange(args[2])
        elif args[0] == Observable.REMOVED:
            self.add_removed(args[2])
        elif args[0] == Observable.CLOSE:
            #self.write()
            pass
        elif args[0] == Observable.FINISHED_ROUND:
            self.write(args[3])

    def add_exchange(self, realized):
        self.realized.append(realized)

    def add_removed(self, removed):
        self.deleted.append(removed)

    def write(self, iteration_number):

        if not os.path.exists("output/{0}/exchanges".format(self.current_file)):
            os.makedirs("output/{0}/exchanges".format(self.current_file))

        writer = csvWriter()
        writer.write("output/{2}/exchanges/{0}.{1}".format(iteration_number, "output.csv", self.current_file),
                     self.realized)

        self.setup()
