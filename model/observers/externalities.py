import collections
import csv
import os
from collections import defaultdict

from model import calculations
from model.base import AbstractExchange
from model.observers.observer import Observer, Observable


class Externalities(Observer):
    """
    There are three stages of externalities: by exchange, by issue combination and by actor. This class writes at the 
    end of each loop the externalities to the filesystem. 
    """

    def __init__(self, observable: Observable):
        super().__init__(observable)
        self._setup()

    def _setup(self):
        """
        Initializes the class attributes for reusable purpose        
        """
        self.connections = {}
        self.actors = defaultdict(lambda: defaultdict(int))
        self.exchanges = []

    def execute_exchange(self, exchange: AbstractExchange):
        """
        Calculations of the externalities performed each round after an exchange is exectued
        :param exchange: AbstractExchange        
        """

        issue_set_key = "{0}-{1}".format(exchange.p, exchange.q)

        # an combination only exists once, so it can happen that we have to change the sequence of the keys
        if issue_set_key not in self.model_ref.groups:
            issue_set_key = "{0}-{1}".format(exchange.q, exchange.p)
        # end if

        inner = ['a', 'd']
        outer = ['b', 'c']

        # switch the inner and outer if this is not the case
        if exchange.i.group != "a" and exchange.i.group != "d":
            inner, outer = outer, inner
        # end if

        externalities = self._calculate_externalities(self.model_ref, exchange)

        exchange_set = self._add_exchange_set(externalities, exchange, self.model_ref, inner, issue_set_key)

        self._add_or_update_issue_set(issue_set_key, exchange, exchange_set)

        self.exchanges.append(
            [exchange.i.actor_name, exchange.i.supply_issue, exchange.j.actor_name, exchange.j.supply_issue,
             exchange_set["ip"],
             exchange_set["in"], exchange_set["op"], exchange_set["on"], exchange_set["own"]])

    def _add_exchange_set(self, externalities, realized, model, inner, issue_set_key):
        """
        Checks if an externalitie is own, inner or outer and positive or negative. This method alse updates the actor  
        externalities but returns the exchange as an set.         
        """

        exchange_set = defaultdict(int)

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

    def _create_directories(self):
        """
        Helper for creating the output directory        
        """
        if not os.path.exists("{0}/externalities".format(self.output_directory)):
            os.makedirs("{0}/externalities".format(self.output_directory))

    def _ordered_actors(self):
        """
        Helper for outputting the actors in a consisting order        
        """
        return collections.OrderedDict(sorted(self.actors.items())).items()

    def end_loop(self, iteration: int):
        """
        Write the data to the filesystem        
        :param iteration: int the current iteration round 
        :return: 
        """
        self._create_directories()

        with open("{0}/externalities/externalities.{1}.csv".format(self.output_directory, iteration + 1), 'w') as csv_file:
            writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')

            # headings
            writer.writerow(
                ["Actor", "Inner Positive", "Inner Negative", "Outer Positive", "Outer Negative", "Own"])

            for key, value in self._ordered_actors():
                writer.writerow([key, value["ip"], value["in"], value["op"], value["on"], value["own"]])

            writer.writerow([])
            writer.writerow(["Connections"])
            writer.writerow(["first", "second", "inner pos", "inner neg", "outer pos", "outer neg", "own"])

            for key, value in self.connections.items():
                writer.writerow(
                    [value["first"], value["second"], value["ip"], value["in"], value["op"], value["on"],
                     value["own"]])

            writer.writerow([])
            writer.writerow(["Realizations"])
            writer.writerow(
                ["first", "supply", "second", "supply ", "inner pos", "inner neg", "outer pos", "outer neg", "own"])

            for realizations in self.exchanges:
                writer.writerow(realizations)

        # after each round reset the state of the object.
        self._setup()
