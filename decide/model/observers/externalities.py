import collections
import csv
import os
from collections import defaultdict

from .. import base
from .. import calculations
from ..observers import observer


class Externalities(observer.Observer):
    """
    There are three stages of externalities: by exchange, by issue combination and by actor. This class writes at the 
    end of each loop the externalities to the filesystem. 
    """

    def __init__(self, observable: observer.Observable, summary_only=False):
        super().__init__(observable)
        self.actor_totals = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.summary_only = summary_only

    def _setup(self):
        """
        Initializes the class attributes for reusable purpose        
        """
        self.connections = {}
        self.actors = defaultdict(lambda: defaultdict(int))
        self.exchanges = []

        self.database_objects = []

    def _add_exchange_set(self, externalities, realized, model, inner, issue_set_key):
        """
        Checks if an externality is own, inner or outer and positive or negative. This method also updates the actor
        externalities but returns the exchange as an set.         
        """

        exchange_set = defaultdict(int)

        for actor, value in externalities.items():

            if (
                actor == realized.i.actor or actor == realized.j.actor
            ):  # own, always positive
                key = "own"
                value = realized.gain  # TODO hotfix, should not be needed.
            else:
                is_inner = self.model_ref.is_inner_group_member(
                    actor, inner, issue_set_key
                )

                if value > 0:  # positive
                    if is_inner:  # inner
                        key = "ip"
                    else:  # outer
                        key = "op"
                else:  # negative
                    if is_inner:  # inner
                        key = "in"
                    else:  # outer
                        key = "on"

            self.actors[actor][key] += value
            exchange_set[key] += value

        return exchange_set

    def _add_or_update_issue_set(self, issue_set_key, realized, exchange_set):
        """
        Create a new entry or adds the value to the existing connection
        :param issue_set_key: 
        :param realized: 
        :param exchange_set: 
        :return: 
        """

        if issue_set_key in self.connections:
            for key, value in exchange_set.items():
                self.connections[issue_set_key][key] += value
        else:
            self.connections[issue_set_key] = exchange_set
            self.connections[issue_set_key]["first"] = realized.p
            self.connections[issue_set_key]["second"] = realized.q
            # end if

    @staticmethod
    def _calculate_externalities(model, realized):
        """
        Loops over all the actors and calculates each actor his externalities
        :param model: 
        :param realized: 
        :return: 
        """

        results = {}

        for actor in model.actors:
            results[actor] = calculations.actor_externalities(actor, model, realized)

        return results

    def _create_directories(self, repetition):
        """
        Helper for creating the output directory        
        """
        if not os.path.exists(
            "{0}/externalities/{1}".format(self.output_directory, repetition)
        ):
            os.makedirs(
                "{0}/externalities/{1}".format(self.output_directory, repetition)
            )

    def _ordered_actors(self):
        """
        Helper for outputting the actors in a consisting order        
        """
        return collections.OrderedDict(sorted(self.actors.items())).items()

    def _sum(self, ordered_actors, iteration, repetition):
        """
        sum the dictionary keys
        """

        for key, value in ordered_actors:
            actor = self.actor_totals[key][iteration]

            actor["ip"].append(value["ip"])
            actor["in"].append(value["in"])
            actor["op"].append(value["op"])
            actor["on"].append(value["on"])
            actor["own"].append(value["own"])

    def execute_exchange(self, exchange: base.AbstractExchange):
        """
        Calculations of the externalities performed each round after an exchange is executed
        :param exchange: AbstractExchange        
        """

        issue_set_key = self.model_ref.create_existing_issue_set_key(
            exchange.p, exchange.q
        )

        inner = exchange.get_inner_groups()

        externalities = self._calculate_externalities(self.model_ref, exchange)

        exchange_set = self._add_exchange_set(
            externalities, exchange, self.model_ref, inner, issue_set_key
        )

        self._add_or_update_issue_set(issue_set_key, exchange, exchange_set)

        self.exchanges.append(
            [
                exchange.i.actor,
                exchange.i.supply.issue,
                exchange.j.actor,
                exchange.j.supply.issue,
                exchange_set["ip"],
                exchange_set["in"],
                exchange_set["op"],
                exchange_set["on"],
                exchange_set["own"],
            ]
        )

    def before_repetitions(self, repetitions, iterations, randomized_value=None):
        """
        create storage units for each repetition and each iteration
        :return:
        """
        pass

    def before_loop(self, iteration: int, repetition: int):
        self._setup()
        self._create_directories(repetition)

    def end_loop(self, iteration: int, repetition: int):
        """
        Write the data to the filesystem and append the storage for the summary
        :param repetition:
        :param iteration: int the current iteration round
        :return: 
        """
        ordered_actors = self._ordered_actors()

        self._sum(ordered_actors, iteration, repetition)

        if self.summary_only:
            return

        with open(
            "{0}/externalities/{2}/externalities.{1}.csv".format(
                self.output_directory, iteration + 1, repetition
            ),
            "w",
        ) as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")

            # headings
            writer.writerow(
                [
                    "Actor",
                    "Inner Positive",
                    "Inner Negative",
                    "Outer Positive",
                    "Outer Negative",
                    "Own",
                ]
            )

            for key, value in ordered_actors:
                writer.writerow(
                    [
                        key,
                        value["ip"],
                        value["in"],
                        value["op"],
                        value["on"],
                        value["own"],
                    ]
                )

            writer.writerow([])
            writer.writerow(["Connections"])
            writer.writerow(
                [
                    "first",
                    "second",
                    "inner pos",
                    "inner neg",
                    "sx outer pos",
                    "outer neg",
                    "own",
                ]
            )

            for key, value in self.connections.items():
                writer.writerow(
                    [
                        value["first"],
                        value["second"],
                        value["ip"],
                        value["in"],
                        value["op"],
                        value["on"],
                        value["own"],
                    ]
                )

            writer.writerow([])
            writer.writerow(["Realizations"])
            writer.writerow(
                [
                    "first",
                    "supply",
                    "second",
                    "supply ",
                    "inner pos",
                    "inner neg",
                    "outer pos",
                    "outer neg",
                    "own",
                ]
            )

            for realizations in self.exchanges:
                writer.writerow(realizations)
                #
                # if insert_db:
                #     from decide.data import database as db
                #
                #     with db.connection.atomic():
                #         db.Externality.create()

    def after_repetitions(self):
        """
        Write the summary's
        """

        if not os.path.exists(
            "{0}/externalities/summary".format(self.output_directory)
        ):
            os.makedirs("{0}/externalities/summary".format(self.output_directory))

        file = defaultdict(list)

        for actor, iterations in collections.OrderedDict(
            sorted(self.actor_totals.items())
        ).items():

            for iteration, externalities in iterations.items():
                row = [actor]

                _in = self._sum_var(externalities["ip"])
                row.append(_in[0])
                row.append(_in[1])
                _in = self._sum_var(externalities["in"])
                row.append(_in[0])
                row.append(_in[1])
                _in = self._sum_var(externalities["op"])
                row.append(_in[0])
                row.append(_in[1])
                _in = self._sum_var(externalities["on"])
                row.append(_in[0])
                row.append(_in[1])
                _in = self._sum_var(externalities["own"])
                row.append(_in[0])
                row.append(_in[1])

                file[iteration].append(row)

        for key, value in file.items():

            with open(
                "{0}/externalities/summary/{1}.csv".format(self.output_directory, key),
                "w",
            ) as csv_file:
                writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")

                # headings
                writer.writerow(
                    [
                        "Actor",
                        "Inner Positive",
                        "",
                        "Inner Negative",
                        "",
                        "Outer Positive",
                        "",
                        "Outer Negative",
                        "",
                        "Own" "",
                    ]
                )

                for row in value:
                    writer.writerow(row)

    def _sum_var(self, items: list):

        if len(items) == 0:
            return 0, 0

        total = sum(items)
        avg = total / len(items)

        if total == 0:
            return 0, 0

        variance = sum([pow(x - avg, 2) for x in items]) / len(items)

        return str(avg), str(variance)
