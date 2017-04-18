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
        self.voting_loss = {}
        self.preference_loss = {}

        for issue in model.actor_issues:

            issue_list = {}

            for key, actor_issue in model.actor_issues[issue].items():
                issue_list[actor_issue.actor_name] = []

            issue_list["nbs"] = []

            self.preference_history[issue] = copy.deepcopy(issue_list)
            self.voting_history[issue] = copy.deepcopy(issue_list)
            self.voting_loss[issue] = copy.deepcopy(issue_list)
            self.preference_loss[issue] = copy.deepcopy(issue_list)

    def update(self, observable, notification_type, **kwargs):
        if notification_type == Observable.CLOSE:
            self.close(**kwargs)
        elif notification_type == Observable.FINISHED_ROUND:
            self.finish_round(**kwargs)
        elif notification_type == Observable.PREPARE_NEXT_ROUND:
            self.prepare_next(**kwargs)

    def finish_round(self, **kwargs):

        model = kwargs["model"]

        for issue in model.actor_issues:

            nbs = model.nbs[issue]
            sum_var = 0

            for key, actor_issue in model.actor_issues[issue].items():
                position = actor_issue.position
                sum_var += ((position - nbs) ** 2)

                self.preference_history[issue][key].append(actor_issue.position)
                self.preference_loss[issue][key].append(abs(actor_issue.position - nbs) * actor_issue.salience)

            nbs_var = sum_var / len(model.actor_issues[issue])

            self.preference_history[issue]["nbs"].append(nbs)
            self.preference_loss[issue]["nbs"].append(nbs_var)

    def prepare_next(self, **kwargs):

        model = kwargs["model"]

        for issue in model.actor_issues:

            nbs = model.nbs[issue]
            sum_var = 0

            for key, actor_issue in model.actor_issues[issue].items():
                position = actor_issue.position
                sum_var += ((position - nbs) ** 2)

                self.voting_history[issue][key].append(position)
                self.voting_loss[issue][key].append(abs(actor_issue.position - nbs) * actor_issue.salience)

            nbs_var = sum_var / len(model.actor_issues[issue])

            self.voting_history[issue]["nbs"].append(nbs)
            self.voting_loss[issue]["nbs"].append(nbs_var)

    def loss(self):
        pass

    def number_value(self, value):

        return str(value)

    def close(self, **kwargs):
        for issue in self.preference_history:
            with open("{0}/issue.{1}.csv".format(self.output_dir, issue), 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')

                heading = ["rnd-" + str(x) for x in range(len(self.voting_history[issue]["nbs"]))]

                writer.writerow([issue])
                writer.writerow(["Overview issue"])
                writer.writerow(["round","nbs","voting nbs","nbs var", "vot vat"])

                preference_nbs = self.preference_history[issue]["nbs"]
                del self.preference_history[issue]["nbs"]

                voting_nbs = self.voting_history[issue]["nbs"]
                del self.voting_history[issue]["nbs"]

                preference_nbs_var = self.preference_loss[issue]["nbs"]
                del self.preference_loss[issue]["nbs"]

                voting_nbs_var = self.voting_loss[issue]["nbs"]
                del self.voting_loss[issue]["nbs"]

                for x in range(len(preference_nbs)):

                    row = ["rn-" + str(x)]
                    row.append(self.number_value(preference_nbs[x]))
                    row.append(self.number_value(voting_nbs[x]))
                    row.append(self.number_value(preference_nbs_var[x]))
                    row.append(self.number_value(voting_nbs_var[x]))
                    writer.writerow(row)

                writer.writerow([])
                writer.writerow(["Preference development NBS and all actors"])
                writer.writerow(["actor"] + heading)

                writer.writerow(["nbs"] + preference_nbs)

                for key, value in self.preference_history[issue].items():
                    writer.writerow([key] + value)

                writer.writerow([])
                writer.writerow(["Voting development NBS and all actors"])
                writer.writerow(["actor"] + heading)

                writer.writerow(["nbs"] + voting_nbs)

                for key, value in self.voting_history[issue].items():
                    writer.writerow([key] + value)

                writer.writerow([])
                writer.writerow(["Preference variance and loss of all actors"])

                writer.writerow(["nbs-var"] + preference_nbs_var)

                for key, value in self.preference_loss[issue].items():
                    writer.writerow([key] + value)

                writer.writerow([])
                writer.writerow(["Voting variance and loss of all actors"])

                writer.writerow(["nbs-var"] + voting_nbs_var)

                for key, value in self.voting_loss[issue].items():
                    writer.writerow([key] + value)
