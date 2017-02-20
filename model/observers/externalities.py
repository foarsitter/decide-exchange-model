import collections
import csv
import os

from model import calculations
from model.observers.observer import Observer, Observable


class Externalities(Observer):
    """
    There are three stages of externalities
    By exchange, by issue set and by actor
    """

    def __init__(self, observable, model, current_file):
        super(Externalities, self).__init__(observable=observable)

        self.current_file = current_file

        self.issue_set = {}
        self.actors = {}
        self.exchanges = []

        for actor in model.Actors:
            self.actors[actor] = {'ip': 0, 'in': 0, 'op': 0, 'on': 0, "own": 0}

    def setup(self, model):
        self.issue_set = {}
        self.actors = {}
        self.exchanges = []

        for actor in model.Actors:
            self.actors[actor] = {'ip': 0, 'in': 0, 'op': 0, 'on': 0, "own": 0}

    def init_issue_set(self, issue_sets):
        pass

    def init_actors(self, actors):
        pass

    def update(self, observable, notification_type, **kwargs):

        if notification_type == Observable.EXECUTED:
            self.calculate_externalities(**kwargs)
        elif notification_type == Observable.FINISHED_ROUND:
            self.write_round(**kwargs)

    def calculate_externalities(self, **kwargs):

        realized = kwargs["realized"]
        model = kwargs["model"]

        issue_set_key = "{0}-{1}".format(realized.p, realized.q)

        # an combination only exists once, so it can happen that we have to change the sequence of the keys
        if issue_set_key not in model.groups:
            issue_set_key = "{0}-{1}".format(realized.q, realized.p)
        # end if

        inner = ['a', 'd']
        outer = ['b', 'c']

        # switch the inner and outer if this is not the case
        if realized.i.group != "a" and realized.i.group != "d":
            inner, outer = outer, inner
        # end if

        externalities = self.calculate_exteranlities(model, realized)

        exchange_set = self.add_exchange_set(externalities, realized, model, inner, issue_set_key)

        self.add_or_update_issue_set(issue_set_key, realized, exchange_set)

        self.exchanges.append(
            [realized.i.actor_name, realized.i.supply_issue, realized.j.actor_name, realized.j.supply_issue, exchange_set["ip"],
             exchange_set["in"], exchange_set["op"], exchange_set["on"], exchange_set["own"]])

    def add_exchange_set(self, externalities, realized, model, inner, issue_set_key):
        exchange_set = {'ip': 0, 'in': 0, 'op': 0, 'on': 0, "own": 0}

        for actor_name, value in externalities.items():

            if actor_name == realized.i.actor_name or actor_name == realized.j.actor_name:  # own, always positive
                key = "own"
            else:
                is_inner = actor_name in model.groups[issue_set_key][inner[0]] or actor_name in \
                                                                                  model.groups[issue_set_key][inner[1]]

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

            self.actors[actor_name][key] += value
            exchange_set[key] += value

        return exchange_set

    def add_or_update_issue_set(self, issue_set_key, realized, exchange_set):

        if issue_set_key in self.issue_set:
            for key, value in exchange_set.items():
                self.issue_set[issue_set_key][key] += value
        else:
            self.issue_set[issue_set_key] = exchange_set
            self.issue_set[issue_set_key]["first"] = realized.p
            self.issue_set[issue_set_key]["second"] = realized.q
            # end if

    @staticmethod
    def calculate_exteranlities(model, realized):

        results = {}

        for actor in model.Actors:
            results[actor] = calculations.actor_externalities(actor, model, realized)
        # end for

        return results

    def write_round(self, **kwargs):

        iteration_number = kwargs["iteration"]
        model = kwargs["model"]

        # TODO: we should write all the documents after executing all the rounds as we do with the externalities

        if not os.path.exists("{0}/externalities".format(self.current_file)):
            os.makedirs("{0}/externalities".format(self.current_file))

        with open("{0}/externalities/externalities.{1}.csv".format(self.current_file, iteration_number+1),
                  'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=';',lineterminator='\n')

            # headings
            writer.writerow(
                ["Actor", "Inner Positive", "Inner Negative", "Outer Positive", "Outer Negative", "Own"])

            od_e = collections.OrderedDict(sorted(self.actors.items()))
            for key, value in od_e.items():
                writer.writerow([key, value["ip"], value["in"], value["op"], value["on"], value["own"]])

            writer.writerow([])
            writer.writerow(["Connections"])
            writer.writerow(
                ["first", "second", "inner pos", "inner neg", "outer pos", "outer neg", "own", "ally pos",
                 "ally neg"])

            for key, value in self.issue_set.items():
                writer.writerow(
                    [value["first"], value["second"], value["ip"], value["in"], value["op"], value["on"],
                     value["own"]])
            # end for

            writer.writerow([])
            writer.writerow(["Realizations"])
            writer.writerow(
                ["first", "supply", "second", "supply ", "inner pos", "inner neg", "outer pos", "outer neg", "own",
                 "ally pos", "ally neg"])

            for realizations_row in self.exchanges:
                writer.writerow(realizations_row)

                # end for
        # end with

        self.setup(model)
