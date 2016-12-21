import csv

from model.observers.observer import Observer, Observable


class HistoryWriter(Observer):
	"""
	There are three stages of externalities
	By exchange, by issue set and by actor
	"""

	def __init__(self, observable, model, current_file):
		super(HistoryWriter, self).__init__(observable=observable)
		self.current_file = current_file

		self.realized = []
		self.deleted = []
		self.history = {}

		for issue in model.ActorIssues:

			issue_list = {}

			for key, actor_issue in model.ActorIssues[issue].items():
				issue_list[actor_issue.actor_name] = []
				issue_list[actor_issue.actor_name].append(actor_issue.position)

			issue_list["nbs"] = []
			self.history[issue] = issue_list

	def setup(self):
		self.realized = []
		self.deleted = []

	def update(self, observable, notification_type, **kwargs):

		if notification_type == Observable.EXECUTED:
			self.add_exchange(**kwargs)
		elif notification_type == Observable.REMOVED:
			self.add_removed(**kwargs)
		elif notification_type == Observable.CLOSE:
			self.close(**kwargs)
			pass
		elif notification_type == Observable.FINISHED_ROUND:
			self.write(**kwargs)

	def add_exchange(self, **kwargs):
		# self.realized.append(realized)
		pass

	def add_removed(self, **kwargs):
		# self.deleted.append(removed)
		pass

	def write(self, **kwargs):

		model = kwargs["model"]

		for issue in model.ActorIssues:
			for key, actor_issue in model.ActorIssues[issue].items():
				self.history[issue][key].append(actor_issue.position)

			self.history[issue]["nbs"].append(model.nbs[issue])
		# end for

	def close(self, **kwargs):
		for issue in self.history:
			with open("output/{3}/{0}.{1}.{2}".format("output", issue, "csv", self.current_file), 'w',
					  newline='') as csv_file:
				writer = csv.writer(csv_file, delimiter=';')

				writer.writerow(["Actor I", "Supply I", "Actor J", "Supply J"])

				for key, value in self.history[issue].items():
					writer.writerow([key] + value)
				# end for

				# end with

				# end for
