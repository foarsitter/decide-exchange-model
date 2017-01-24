import os

from model.helpers.CsvWriter import CsvWriter
from model.observers.observer import Observer, Observable


class ExchangesWriter(Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable, model, dataset_name):
        super(ExchangesWriter, self).__init__(observable=observable)
        self.dataset_name = dataset_name

        self.realized = []
        self.deleted = []

    def setup(self):
        self.realized = []
        self.deleted = []

    def update(self, observable, notification_type, **kwargs):

        if notification_type == Observable.EXECUTED:
            self.add_exchange(**kwargs)
        elif notification_type == Observable.REMOVED:
            self.add_removed(**kwargs)
        elif notification_type == Observable.CLOSE:
            # self.write()
            pass
        elif notification_type == Observable.FINISHED_ROUND:
            self.write(**kwargs)

    def add_exchange(self, **kwargs):
        self.realized.append(kwargs["realized"])

    def add_removed(self, **kwargs):
        removed = kwargs["removed"]
        self.deleted.append(removed)

    def write(self, **kwargs):

        if not os.path.exists("output/{0}/exchanges".format(self.dataset_name)):
            os.makedirs("output/{0}/exchanges".format(self.dataset_name))

        writer = CsvWriter()
        writer.write("output/{2}/exchanges/{0}.{1}".format(kwargs["iteration"], "output.csv", self.dataset_name),
                     self.realized)

        self.setup()
