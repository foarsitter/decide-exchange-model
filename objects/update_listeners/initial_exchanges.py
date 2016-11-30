from csvWriter import csvWriter
from objects.update_listeners.observer import Observer, Observable


class InitialExchanges(Observer):
	def __init__(self, observable):
		super(InitialExchanges, self).__init__(observable)
		self.has_written = False

	def update(self, observable, notification_type: int, **kwargs):

		if notification_type == Observable.START_ROUND:
			self.write_round(kwargs["model"])

	def write_round(self, model):

		model.sort_exchanges()

		if not self.has_written:
			csvwriter = csvWriter()

			csvwriter.write("random.csv", model.Exchanges)
			self.has_written = True
