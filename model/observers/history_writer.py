import csv

import copy
from typing import List
import matplotlib.pyplot as plt

from model.base import AbstractExchange, Issue
from model.observers.observer import Observer, Observable



class HistoryWriter(Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable: Observable):
        super().__init__(observable=observable)

        self.preference_history = {}
        self.voting_history = {}
        self.voting_loss = {}
        self.preference_loss = {}
        self.issue_obj = None
        self._setup()

    def _setup(self):
        """
        Setup method.          
        """
        for issue in self.model_ref.actor_issues:
            issue_list = {}

            for key, actor_issue in self.model_ref.actor_issues[issue].items():
                issue_list[actor_issue.actor_name] = []

            issue_list["nbs"] = []

            self.preference_history[issue] = copy.deepcopy(issue_list)
            self.voting_history[issue] = copy.deepcopy(issue_list)
            self.voting_loss[issue] = copy.deepcopy(issue_list)
            self.preference_loss[issue] = copy.deepcopy(issue_list)

    def after_loop(self, realized: List[AbstractExchange], iteration: int):

        """
        After each round we calculate the variance
        :param realized:         
        :param iteration: 
        :return: 
        """
        model = self.model_ref

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

    def end_loop(self, iteration: int):
        """
        Before each round we calculate the voting positoin
        :param iteration:
        :return: 
        """

        for issue in self.model_ref.actor_issues:

            nbs = self.model_ref.nbs[issue]
            sum_var = 0

            for key, actor_issue in self.model_ref.actor_issues[issue].items():
                position = actor_issue.position
                sum_var += ((position - nbs) ** 2)

                self.voting_history[issue][key].append(position)
                self.voting_loss[issue][key].append(abs(actor_issue.position - nbs) * actor_issue.salience)

            nbs_var = sum_var / len(self.model_ref.actor_issues[issue])

            self.voting_history[issue]["nbs"].append(nbs)
            self.voting_loss[issue]["nbs"].append(nbs_var)

    def after_execution(self, repetition):
        """
        Write all the data to the filesystem
        """

        for issue in self.preference_history:
            with open("{0}/{1}.csv".format(self.output_directory, issue), 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')

                self.issue_obj = self.model_ref.issues[issue]  # type: Issue

                heading = ["rnd-" + str(x) for x in range(len(self.voting_history[issue]["nbs"]))]

                writer.writerow([self.issue_obj.name, self.issue_obj.lower, self.issue_obj.upper])
                writer.writerow(["Overview issue"])
                writer.writerow(["round", "nbs", "voting nbs", "nbs var", "vot vat"])

                preference_nbs = self.preference_history[issue]["nbs"]
                del self.preference_history[issue]["nbs"]

                voting_nbs = self.voting_history[issue]["nbs"]
                del self.voting_history[issue]["nbs"]

                preference_nbs_var = self.preference_loss[issue]["nbs"]
                del self.preference_loss[issue]["nbs"]

                voting_nbs_var = self.voting_loss[issue]["nbs"]
                del self.voting_loss[issue]["nbs"]

                for x in range(len(preference_nbs)):
                    writer.writerow(
                        ["rn-" + str(x), self._number_value(preference_nbs[x]), self._number_value(voting_nbs[x]),
                         self._number_value(preference_nbs_var[x]), self._number_value(voting_nbs_var[x])])

                writer.writerow([])
                writer.writerow(["Preference development NBS and all actors"])
                writer.writerow(["actor"] + heading)

                plt.clf()
                nbs_values = self._number_list_value(preference_nbs)

                writer.writerow(["nbs"] + nbs_values)

                plt.plot(nbs_values, label='nbs')

                for key, value in self.preference_history[issue].items():
                    values = self._number_list_value(value)
                    writer.writerow([key] + values)
                    plt.plot(values, label=self.model_ref.actors[key].name)

                plt.legend(loc='upper left')
                plt.title(self.issue_obj)
                plt.savefig('{0}/{1}.png'.format(self.output_directory, self.issue_obj.name))

                writer.writerow([])
                writer.writerow(["Voting development NBS and all actors"])
                writer.writerow(["actor"] + heading)

                writer.writerow(["nbs"] + self._number_list_value(voting_nbs))

                for key, value in self.voting_history[issue].items():
                    writer.writerow([key] + self._number_list_value(value))

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

    def _number_value(self, value):
        return self.issue_obj.de_normalize(value)

    def _number_list_value(self, values):
        for _, value in enumerate(values):
            values[_] = self.issue_obj.de_normalize(value)
        return values
