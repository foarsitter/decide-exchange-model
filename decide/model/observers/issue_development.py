import copy
import csv
import math
import os
from collections import defaultdict, OrderedDict
from typing import List

import matplotlib

matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt

from decide.model.base import Issue
from .. import base
from .. import calculations
from ..observers import observer


class IssueDevelopment(observer.Observer):
    """
    Keeps track of the change in issue position
    """

    def __init__(
        self,
        observable: observer.Observable,
        write_voting_position=True,
        summary_only=False,
    ):
        super().__init__(observable=observable)

        self.preference_history = {}
        self.voting_history = {}
        self.voting_loss = {}
        self.preference_loss = {}
        self.issue_obj = None
        self.write_voting_position = write_voting_position

        self.preference_history_sum = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self.voting_history_sum = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self.voting_loss_sum = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
        self.preference_loss_sum = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        self.denominator = 0  # TODO remove or document this attribute

        self.summary_only = summary_only

    def _setup(self):
        """
        Setup method.
        """
        for issue in self.model_ref.actor_issues:
            issue_list = {}

            for key, actor_issue in self.model_ref.actor_issues[issue].items():
                issue_list[actor_issue.actor] = []

            issue_list["nbs"] = []

            self.preference_history[issue] = copy.deepcopy(issue_list)
            self.voting_history[issue] = copy.deepcopy(issue_list)
            self.voting_loss[issue] = copy.deepcopy(issue_list)
            self.preference_loss[issue] = copy.deepcopy(issue_list)

        self.denominator += 1

    def _de_normalize_value(self, value):
        return self.issue_obj.de_normalize(value)

    def _de_normalize_list_value(self, values, _map=None):
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
        if not os.path.exists(
            "{0}/issues/{1}".format(self.output_directory, repetition)
        ):
            os.makedirs("{0}/issues/{1}/csv".format(self.output_directory, repetition))
            os.makedirs(
                "{0}/issues/{1}/charts".format(self.output_directory, repetition)
            )

    def before_repetitions(self, repetitions, iterations, randomized_value=None):
        pass

    def before_iterations(self, repetition):
        """
        :param repetition:
        :return:
        """
        self._setup()

        if not self.summary_only:
            self._create_directories(repetition)

    def before_loop(self, iteration: int, repetition: int):
        pass

    def after_loop(
        self, realized: List[base.AbstractExchange], iteration: int, repetition: int
    ):
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
            variance_sum = 0

            for actor_id, actor_issue in model.actor_issues[issue].items():
                # only the sum part of the variance formula
                variance_sum += (actor_issue.position - nbs) ** 2

                # the distance of the actor adjusted by his salience
                actor_loss = abs(actor_issue.position - nbs) * actor_issue.salience

                # track history
                self.preference_history[issue][actor_id].append(actor_issue.position)
                self.preference_history_sum[issue][actor_id][iteration].append(
                    actor_issue.position
                )

                # track loss
                self.preference_loss[issue][actor_id].append(actor_loss)
                self.preference_loss_sum[issue][actor_id][iteration].append(actor_loss)

            nbs_var = variance_sum / len(model.actor_issues[issue])

            self._append_nbs_preferences(
                issue=issue, iteration=iteration, nbs=nbs, nbs_var=nbs_var
            )

    def _append_nbs_preferences(self, issue, iteration, nbs, nbs_var):
        self.preference_history[issue]["nbs"].append(nbs)
        self.preference_history_sum[issue]["nbs"][iteration].append(nbs)
        self.preference_loss[issue]["nbs"].append(nbs_var)
        self.preference_loss_sum[issue]["nbs"][iteration].append(nbs_var)

    def end_loop(self, iteration: int, repetition: int):
        """
        Before each round we calculate the voting position
        :param repetition:
        :param iteration:1
        :return:
        """

        for issue in self.model_ref.actor_issues:

            nbs = self.model_ref.nbs[issue]
            variance_sum = 0

            for actor_id, actor_issue in self.model_ref.actor_issues[issue].items():
                variance_sum += (actor_issue.position - nbs) ** 2

                # the distance of the actor adjusted by his salience
                actor_loss = abs(actor_issue.position - nbs) * actor_issue.salience

                self.voting_history[issue][actor_id].append(actor_issue.position)

                self.voting_history_sum[issue][actor_id][iteration].append(
                    actor_issue.position
                )

                self.voting_loss[issue][actor_id].append(
                    abs(actor_issue.position - nbs) * actor_issue.salience
                )

                self.voting_loss_sum[issue][actor_id][iteration].append(actor_loss)

            nbs_var = variance_sum / len(self.model_ref.actor_issues[issue])

            self.voting_history[issue]["nbs"].append(nbs)
            self.voting_history_sum[issue]["nbs"][iteration].append(nbs)
            self.voting_loss[issue]["nbs"].append(nbs_var)
            self.voting_loss_sum[issue]["nbs"][iteration].append(nbs_var)

    def after_iterations(self, repetition):
        """
        Write all the data of this repetition to the filesystem
        """

        if self.summary_only:
            return

        for issue in self.preference_history:
            with open(
                "{0}/issues/{2}/csv/{1}.{3}.csv".format(
                    self.output_directory, issue, repetition, self._get_salt
                ),
                "w",
            ) as csv_file:
                writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
                self.write_issue_after_iterations_to_file(repetition, writer, issue)

    def write_issue_after_iterations_to_file(self, repetition, writer, issue):
        self.issue_obj = self.model_ref.issues[issue]  # type: Issue

        heading = [
            "rnd-" + str(x)
            for x in range(len(self.preference_history[issue]["nbs"]))
        ]

        writer.writerow([self.issue_obj])
        writer.writerow([])  # empty row for readability

        writer.writerow(["Issue overview"])

        if self.write_voting_position:
            writer.writerow(
                [
                    "round",
                    "preference nbs",
                    "preference nbs var",
                    "",
                    "voting nbs",
                    "voting nbs var",
                ]
            )
        else:
            writer.writerow(["round", "preference nbs", "preference nbs var"])

        # remove the nbs from each collection so it doesn't show up in the table.
        preference_nbs = self.preference_history[issue]["nbs"]
        del self.preference_history[issue]["nbs"]

        preference_nbs_var = self.preference_loss[issue]["nbs"]
        del self.preference_loss[issue]["nbs"]

        if self.write_voting_position:
            voting_nbs = self.voting_history[issue]["nbs"]
            del self.voting_history[issue]["nbs"]

            voting_nbs_var = self.voting_loss[issue]["nbs"]
            del self.voting_loss[issue]["nbs"]

        # create a summary table for only the preference and voting nbs + variance
        for x in range(len(preference_nbs)):

            row = [
                "rnd-" + str(x),  # round
                self._de_normalize_value(preference_nbs[x]),  # preference nbs
                self._de_normalize_value(
                    preference_nbs_var[x]
                ),  # preference nbs variance
            ]

            # write the voting positions only when the author asks for it te keep the output simple.
            if self.write_voting_position:
                row.append("")  # extra spacing for readability
                row.append(
                    self._de_normalize_value(voting_nbs[x])
                )  # voting nbs
                row.append(
                    self._de_normalize_value(voting_nbs_var[x])
                )  # voting nbs variance

            writer.writerow(row)

        # issue development summary
        writer.writerow([])
        writer.writerow(
            ["First and last round comparison of NBS and all actors"]
        )
        writer.writerow(
            [
                "Actor",
                "Salience",
                "Power",
                "First round",
                "Final round",
                "Position shift",
                "Distance NBS start",
                "Distance NBS end",
            ]
        )

        nbs_start = self._de_normalize_value(preference_nbs[0])
        nbs_end = self._de_normalize_value(preference_nbs[-1])

        writer.writerow(["NBS", "-", "-", nbs_start, nbs_end, "-"])

        # to compare different issues and variances of the model, keep the output sorted
        od = OrderedDict(sorted(self.preference_history[issue].items()))

        for actor_id, value in od.items():
            actor_issue = self.model_ref.actor_issues[self.issue_obj][actor_id]

            position_start = self._de_normalize_value(value[0])
            position_end = self._de_normalize_value(value[-1])
            position_delta = position_end - position_start

            nbs_distance_start = abs(position_start - nbs_start)
            nbs_distance_end = abs(position_start - nbs_end)
            nbs_distance_delta = nbs_distance_end - nbs_distance_start

            writer.writerow(
                [
                    actor_issue.actor,
                    actor_issue.salience,
                    actor_issue.power,
                    position_start,
                    position_end,
                    position_delta,
                    nbs_distance_start,
                    nbs_distance_end,
                    nbs_distance_delta,
                ]
            )

        # second table
        writer.writerow([])
        writer.writerow(["Preference development NBS and all actors"])
        writer.writerow(["actor", "salience", "power"] + heading)

        plt.clf()

        nbs_values = self._de_normalize_list_value(preference_nbs)

        writer.writerow(["nbs", "-", "-"] + nbs_values)

        plt.plot(nbs_values, label="nbs")

        for actor_id, value in od.items():
            actor_issue = self.model_ref.actor_issues[self.issue_obj][actor_id]

            values = self._de_normalize_list_value(value)
            writer.writerow(
                [actor_id, actor_issue.salience, actor_issue.power] + values
            )

            plt.plot(values, label=self.model_ref.actors[actor_id].name)

        lgd = plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
        plt.title(self.issue_obj)
        plt.savefig(
            "{0}/issues/{2}/charts/{1}.png".format(
                self.output_directory, self.issue_obj.name, repetition
            ),
            bbox_extra_artists=(lgd,),
            bbox_inches="tight",
        )

        if self.write_voting_position:
            writer.writerow([])
            writer.writerow(["Voting development NBS and all actors"])
            writer.writerow(["Actor", "Salience", "Power"] + heading)

            writer.writerow(
                ["NBS", "-", "-"] + self._de_normalize_list_value(voting_nbs)
            )

            od = OrderedDict(sorted(self.voting_history[issue].items()))

            for actor_id, value in od.items():
                actor_issue = self.model_ref.actor_issues[self.issue_obj][
                    actor_id
                ]
                writer.writerow(
                    [actor_id, actor_issue.salience, actor_issue.power]
                    + self._de_normalize_list_value(value)
                )

        writer.writerow([])
        writer.writerow(["Preference variance and loss of all actors"])

        writer.writerow(["nbs-var"] + preference_nbs_var)

        od = OrderedDict(sorted(self.preference_loss[issue].items()))

        for actor_id, value in od.items():
            writer.writerow([actor_id] + value)

        if self.write_voting_position:

            writer.writerow([])
            writer.writerow(["Voting variance and loss of all actors"])

            writer.writerow(["nbs-var"] + voting_nbs_var)

            od = OrderedDict(sorted(self.voting_loss[issue].items()))

            for actor_id, value in od.items():
                writer.writerow([actor_id] + value)

    def after_repetitions(self):
        """
        Write all the results to a summary with the averages for all repetitions
        :return:
        """

        self._create_directories("summary")

        for issue in self.preference_history_sum:
            with open(
                "{0}/issues/{2}/csv/{1}.{3}.{2}.csv".format(
                    self.output_directory, issue, "summary", self._get_salt
                ),
                "w",
            ) as csv_file:
                writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")

                self.issue_obj = self.model_ref.issues[issue]  # type: Issue

                heading = [
                    "rnd-" + str(x)
                    for x in range(len(self.preference_history_sum[issue]["nbs"]))
                ]

                writer.writerow([self.issue_obj])
                writer.writerow([])
                writer.writerow(["Overview issue"])

                if self.write_voting_position:
                    writer.writerow(
                        [
                            "round",
                            "avg nbs",
                            "variance",
                            "",
                            "avg voting nbs",
                            "variance",
                            "",
                            "avg nbs var",
                            "variance",
                            "",
                            "avg voting variance",
                            "variance",
                        ]
                    )
                else:
                    writer.writerow(
                        [
                            "round",
                            "avg nbs",
                            "variance",
                            "",
                            "avg voting nbs",
                            "variance",
                        ]
                    )

                preference_nbs = self.preference_history_sum[issue]["nbs"]
                del self.preference_history_sum[issue]["nbs"]

                voting_nbs = self.voting_history_sum[issue]["nbs"]
                del self.voting_history_sum[issue]["nbs"]

                preference_nbs_var = self.preference_loss_sum[issue]["nbs"]
                del self.preference_loss_sum[issue]["nbs"]

                voting_nbs_var = self.voting_loss_sum[issue]["nbs"]
                del self.voting_loss_sum[issue]["nbs"]

                _ = self._de_normalize_value

                # NBS related data.
                plt.clf()

                p_line = []

                nbs_start = None
                nbs_end = None

                nbs_voting_start = None
                nbs_voting_end = None

                for x in range(len(preference_nbs)):

                    if self.write_voting_position:

                        p = calculations.average_and_variance(preference_nbs[x])
                        v = calculations.average_and_variance(voting_nbs[x])
                        pvar = calculations.average_and_variance(preference_nbs_var[x])
                        vvar = calculations.average_and_variance(voting_nbs_var[x])

                        writer.writerow(
                            [
                                "rn-" + str(x),
                                _(p[0]),
                                p[1],
                                "",
                                _(v[0]),
                                v[1],
                                "",
                                _(pvar[0]),
                                pvar[1],
                                "",
                                _(vvar[0]),
                                vvar[1],
                            ]
                        )

                        p_line.append(_(p[0]))

                        if nbs_voting_start is None:
                            nbs_voting_start = _(v[0])
                        nbs_voting_end = _(v[0])

                    else:
                        p = calculations.average_and_variance(preference_nbs[x])
                        pvar = calculations.average_and_variance(preference_nbs_var[x])

                        writer.writerow(
                            ["rn-" + str(x), _(p[0]), p[1], "", _(pvar[0]), pvar[1]]
                        )

                        p_line.append(_(p[0]))

                    if nbs_start is None:
                        nbs_start = _(p[0])
                    nbs_end = _(p[0])

                plt.plot(p_line, label="nbs")

                writer.writerow([])
                writer.writerow(
                    ["[Preference] First and last round comparison of NBS and all actors"]
                )
                writer.writerow(
                    [
                        "Actor",
                        "Salience",
                        "Power",
                        "First round",
                        "Final round",
                        "Position shift",
                        "Distance NBS start",
                        "Distance NBS end",
                    ]
                )

                writer.writerow(["NBS", "-", "-", nbs_start, nbs_end, "-"])

                for actor, value in sorted(self.preference_history_sum[issue].items()):

                    actor_issue = self.model_ref.actor_issues[issue][actor]

                    initial, var = calculations.average_and_variance(list(value.values())[0])
                    last, var = calculations.average_and_variance(list(value.values())[-1])

                    position_start = _(initial)
                    position_end = _(last)
                    position_delta = position_end - position_start

                    nbs_distance_start = abs(position_start - nbs_start)
                    nbs_distance_end = abs(position_start - nbs_end)

                    writer.writerow(
                        [
                            actor_issue.actor,
                            actor_issue.salience,
                            actor_issue.power,
                            position_start,
                            position_end,
                            position_delta,
                            nbs_distance_start,
                            nbs_distance_end,
                        ]
                    )

                writer.writerow([])
                writer.writerow(
                    ["[Voting] First and last round comparison of NBS and all actors"]
                )
                writer.writerow(
                    [
                        "Actor",
                        "Salience",
                        "Power",
                        "First round",
                        "Final round",
                        "Position shift",
                        "Distance NBS start",
                        "Distance NBS end",
                    ]
                )

                writer.writerow(["NBS", "-", "-", nbs_voting_start, nbs_voting_end, "-"])

                for actor, value in sorted(self.voting_history_sum[issue].items()):

                    actor_issue = self.model_ref.actor_issues[issue][actor]

                    initial, var = calculations.average_and_variance(list(value.values())[0])
                    last, var = calculations.average_and_variance(list(value.values())[-1])

                    position_start = _(initial)
                    position_end = _(last)
                    position_delta = position_end - position_start

                    nbs_distance_start = abs(position_start - nbs_voting_start)
                    nbs_distance_end = abs(position_start - nbs_voting_end)

                    writer.writerow(
                        [
                            actor_issue.actor,
                            actor_issue.salience,
                            actor_issue.power,
                            position_start,
                            position_end,
                            position_delta,
                            nbs_distance_start,
                            nbs_distance_end,
                        ]
                    )

                writer.writerow([])
                writer.writerow(["AVG Preference development NBS and all actors"])
                writer.writerow(["actor", "salience", "power"] + heading)

                var_rows = []

                for actor, value in sorted(self.preference_history_sum[issue].items()):

                    actor_issue = self.model_ref.actor_issues[issue][actor]

                    row = [actor, actor_issue.salience, actor_issue.power]
                    var_row = [actor, actor_issue.salience, actor_issue.power]

                    avg_row = []
                    for iteration, values in value.items():
                        avg, var = calculations.average_and_variance(values)
                        avg_row.append(_(avg))
                        var_row.append(math.sqrt(var))

                    plt.plot(avg_row, label=actor.name)

                    writer.writerow(row + avg_row)
                    var_rows.append(var_row)

                writer.writerow([])
                writer.writerow(["Standard deviation"])
                writer.writerow(["actor", "salience", "power"] + heading)

                for row in var_rows:
                    writer.writerow(row)

                lgd = plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
                plt.title(self.issue_obj)
                plt.savefig(
                    "{0}/issues/{2}/charts/{1}.png".format(
                        self.output_directory, self.issue_obj.issue_id, "summary"
                    ),
                    bbox_extra_artists=(lgd,),
                    bbox_inches="tight",
                )

    @property
    def _get_salt(self):
        model_name = "random"
        from decide.model.equalgain import EqualGainModel

        if isinstance(self.model_ref, EqualGainModel):
            model_name = "equal"
            if self.model_ref.randomized_value is not None:
                model_name += "-" + str(round(self.model_ref.randomized_value, 2))

        return model_name
