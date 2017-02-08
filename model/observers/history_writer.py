import csv

import copy

from model.observers.observer import Observer, Observable


class HistoryWriter(Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable, model, output_dir):
        super(HistoryWriter, self).__init__(observable=observable)
        self.output_dir = output_dir

        self.preference_history = {}
        self.voting_history = {}

        for issue in model.ActorIssues:

            issue_list = {}

            for key, actor_issue in model.ActorIssues[issue].items():
                issue_list[actor_issue.actor_name] = []

            issue_list["nbs"] = []
            issue_list["nbs-var"] = []

            self.preference_history[issue] = copy.deepcopy(issue_list)
            self.voting_history[issue] = copy.deepcopy(issue_list)

    def update(self, observable, notification_type, **kwargs):
        if notification_type == Observable.CLOSE:
            self.close(**kwargs)
        elif notification_type == Observable.FINISHED_ROUND:
            self.finish_round(**kwargs)
        elif notification_type == Observable.PREPARE_NEXT_ROUND:
            self.prepare_next(**kwargs)

    def finish_round(self, **kwargs):

        model = kwargs["model"]

        for issue in model.ActorIssues:

            nbs = model.nbs[issue]
            sum_var = 0

            for key, actor_issue in model.ActorIssues[issue].items():

                position = actor_issue.position
                sum_var += (position - nbs) ** 2

                self.preference_history[issue][key].append(actor_issue.position)

            nbs_var = sum_var / len(model.ActorIssues[issue])

            self.preference_history[issue]["nbs"].append(nbs)
            self.preference_history[issue]["nbs-var"].append(nbs_var)

    def prepare_next(self, **kwargs):

        model = kwargs["model"]

        for issue in model.ActorIssues:

            nbs = model.nbs[issue]
            sum_var = 0

            for key, actor_issue in model.ActorIssues[issue].items():

                position = actor_issue.position
                sum_var += (position - nbs)**2

                self.voting_history[issue][key].append(position)

            nbs_var = sum_var / len(model.ActorIssues[issue])

            self.voting_history[issue]["nbs"].append(nbs)
            self.voting_history[issue]["nbs-var"].append(nbs_var)


    def close(self, **kwargs):
        for issue in self.preference_history:
            with open("{0}/output.{1}.csv".format(self.output_dir, issue), 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=';')

                writer.writerow(["Preference"])

                heading = ["rnd-" + str(x) for x in range(len(self.preference_history[issue]["nbs"]))]

                writer.writerow(["actor"] + heading)

                for key, value in self.preference_history[issue].items():
                    writer.writerow([key] + value)

                heading = ["rnd-" + str(x) for x in range(len(self.voting_history[issue]["nbs"]))]

                writer.writerow([])
                writer.writerow(["Voting"])
                writer.writerow(["actor"] + heading)

                for key, value in self.voting_history[issue].items():
                    writer.writerow([key] + value)
