import csv

import copy
import os
from collections import defaultdict
from typing import List

from model import calculations

matplotlib_loaded = True
try:
    import matplotlib.pyplot as plt
except:
    matplotlib_loaded = False

from model.base import AbstractExchange, Issue
from model.observers.observer import Observer, Observable


class IssueDevelopment(Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable: Observable, write_voting_position=False):
        super().__init__(observable=observable)

        self.preference_history = {}
        self.voting_history = {}
        self.voting_loss = {}
        self.preference_loss = {}
        self.issue_obj = None
        self.write_voting_position = write_voting_position

        self.preference_history_sum = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.voting_history_sum = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.voting_loss_sum = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.preference_loss_sum = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        self.denominator = 0

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

        self.denominator += 1

    def _number_value(self, value):
        return self.issue_obj.de_normalize(value)

    def _number_list_value(self, values, _map=None):
        for _, value in enumerate(values):
            if _map is not None:
                values[_] = self.issue_obj.de_normalize(_map(value))
            else:
                values[_] = self.issue_obj.de_normalize(value)
        return values

    def _create_directories(self, repetition):
        """
        Create the directories
        :param repetition: 
        :return: 
        """
        if not os.path.exists("{0}/issues/{1}".format(self.output_directory, repetition)):
            os.makedirs("{0}/issues/{1}".format(self.output_directory, repetition))

    def before_repetitions(self):
        pass

    def before_iterations(self, repetition):
        """
        :param repetition: 
        :return: 
        """
        self._setup()
        self._create_directories(repetition)

    def before_loop(self, iteration: int, repetition: int):
        pass

    def after_loop(self, realized: List[AbstractExchange], iteration: int, repetition: int):

        """
        After each round we calculate the variance
        :param repetition: 
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
                self.preference_history_sum[issue][key][iteration].append(actor_issue.position)

                loss = abs(actor_issue.position - nbs) * actor_issue.salience
                self.preference_loss[issue][key].append(loss)
                self.preference_loss_sum[issue][key][iteration].append(loss)

            nbs_var = sum_var / len(model.actor_issues[issue])

            self.preference_history[issue]["nbs"].append(nbs)
            self.preference_history_sum[issue]["nbs"][iteration].append(nbs)
            self.preference_loss[issue]["nbs"].append(nbs_var)
            self.preference_loss_sum[issue]["nbs"][iteration].append(nbs_var)

    def end_loop(self, iteration: int, repetition: int):
        """
        Before each round we calculate the voting positoin
        :param repetition: 
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

    def after_iterations(self, repetition):
        """
        Write all the data of this repetition to the filesystem
        """

        for issue in self.preference_history:
            with open("{0}/issues/{2}/{1}.csv".format(self.output_directory, issue, repetition), 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')

                self.issue_obj = self.model_ref.issues[issue]  # type: Issue

                heading = ["rnd-" + str(x) for x in range(len(self.preference_history[issue]["nbs"]))]

                writer.writerow([self.issue_obj.name, self.issue_obj.lower, self.issue_obj.upper])
                writer.writerow(["Overview issue"])

                if self.write_voting_position:
                    writer.writerow(["round", "nbs", "voting nbs", "nbs var", "vot vat"])
                else:
                    writer.writerow(["round", "nbs", "nbs var"])

                preference_nbs = self.preference_history[issue]["nbs"]
                del self.preference_history[issue]["nbs"]

                if self.write_voting_position:
                    voting_nbs = self.voting_history[issue]["nbs"]
                    del self.voting_history[issue]["nbs"]

                preference_nbs_var = self.preference_loss[issue]["nbs"]
                del self.preference_loss[issue]["nbs"]

                voting_nbs_var = self.voting_loss[issue]["nbs"]
                del self.voting_loss[issue]["nbs"]

                for x in range(len(preference_nbs)):

                    if self.write_voting_position:
                        writer.writerow(
                            ["rn-" + str(x), self._number_value(preference_nbs[x]), self._number_value(voting_nbs[x]),
                             self._number_value(preference_nbs_var[x]), self._number_value(voting_nbs_var[x])])
                    else:
                        writer.writerow(
                            ["rn-" + str(x), self._number_value(preference_nbs[x]),
                             self._number_value(preference_nbs_var[x])])

                writer.writerow([])
                writer.writerow(["Preference development NBS and all actors"])
                writer.writerow(["actor"] + heading)

                if matplotlib_loaded:
                    plt.clf()

                nbs_values = self._number_list_value(preference_nbs)

                writer.writerow(["nbs"] + nbs_values)

                if matplotlib_loaded:
                    plt.plot(nbs_values, label='nbs')

                for key, value in self.preference_history[issue].items():
                    values = self._number_list_value(value)
                    writer.writerow([key] + values)
                    if matplotlib_loaded:
                        plt.plot(values, label=self.model_ref.actors[key].name)

                if matplotlib_loaded:
                    plt.legend(loc='upper left')
                    plt.title(self.issue_obj)
                    plt.savefig('{0}/issues/{2}/{1}.png'.format(self.output_directory, self.issue_obj.name, repetition))

                if self.write_voting_position:
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

                if self.write_voting_position:

                    writer.writerow([])
                    writer.writerow(["Voting variance and loss of all actors"])

                    writer.writerow(["nbs-var"] + voting_nbs_var)

                    for key, value in self.voting_loss[issue].items():
                        writer.writerow([key] + value)

    def after_repetitions(self):
        """
        Write all the results to a summary with the averages for all repetitions
        :return: 
        """
        print("after")

        self._create_directories("summary")

        for issue in self.preference_history_sum:
            with open("{0}/issues/{2}/{1}.csv".format(self.output_directory, issue, 'summary'), 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')

                self.issue_obj = self.model_ref.issues[issue]  # type: Issue

                heading = ["rnd-" + str(x) for x in range(len(self.preference_history_sum[issue]["nbs"]))]

                writer.writerow([self.issue_obj.name, self.issue_obj.lower, self.issue_obj.upper])
                writer.writerow(["Overview issue"])

                if self.write_voting_position:
                    writer.writerow(["round", "nbs avg", "nbs var", "voting nbs avg", "voting nbs var", "nbs var avg",
                                     "nbs var var", "vot var avg", "vot var var"])
                else:
                    writer.writerow(["round", "nbs avg", "nbs var", "nbs var avg",
                                     "nbs var var"])

                preference_nbs = self.preference_history_sum[issue]["nbs"]
                del self.preference_history_sum[issue]["nbs"]

                if self.write_voting_position:
                    voting_nbs = self.voting_history_sum[issue]["nbs"]
                    del self.voting_history_sum[issue]["nbs"]

                preference_nbs_var = self.preference_loss_sum[issue]["nbs"]
                del self.preference_loss_sum[issue]["nbs"]

                voting_nbs_var = self.voting_loss_sum[issue]["nbs"]
                del self.voting_loss_sum[issue]["nbs"]

                _ = self._number_value

                # NBS related data.
                for x in range(len(preference_nbs)):

                    if self.write_voting_position:

                        p = calculations.average_and_variance(preference_nbs[x])
                        v = calculations.average_and_variance(voting_nbs[x])
                        pvar = calculations.average_and_variance(preference_nbs_var[x])
                        vvar = calculations.average_and_variance(voting_nbs_var[x])

                        writer.writerow(
                            ["rn-" + str(x), _(p[0]), _(p[1]), _(v[0]), _(v[1]), _(pvar[0]), _(pvar[1]), _(vvar[0]), _(vvar[1])])
                    else:
                        p = calculations.average_and_variance(preference_nbs[x])
                        pvar = calculations.average_and_variance(preference_nbs_var[x])

                        writer.writerow(
                            ["rn-" + str(x), _(p[0]), _(p[1]), _(pvar[0]), _(pvar[1])])

                writer.writerow([])
                writer.writerow(["Preference development NBS and all actors"])
                writer.writerow(["actor"] + heading)

                for actor, value in self.preference_history_sum[issue].items():

                    row = [actor]

                    for iteration, values in value.items():

                        avg, var = calculations.average_and_variance(values)
                        row.append(avg)
                        row.append(var)

                    writer.writerow(row)