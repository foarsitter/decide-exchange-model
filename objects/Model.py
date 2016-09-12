from decimal import *
from itertools import combinations
from operator import attrgetter

from calculations import calc_nbs, calc_nbs_denominator
from objects.Actor import Actor
from objects.ActorIssue import ActorIssue
from objects.Exchange import Exchange


class Model:
    def __init__(self):
        self.Issues = []
        self.ActorIssues = {}
        self.Actors = {}
        self.Exchanges = []
        self.nbs = {}
        self.issue_combinations = []
        self.groups = {}
        self.moves = {}  # dict with issue,actor[move_1,move_2,move_3]
        self.nbs_denominators = {}

    def get_actor_issue(self, actor: Actor, issue: str):

        if actor.Name in self.ActorIssues[issue]:
            return self.ActorIssues[issue][actor.Name]
        else:
            return False

    def get(self, actor: Actor, issue: str, field: str):

        a = None

        a = self.ActorIssues[issue][actor.Name]

        if a is not False:

            if field is "c":
                return a.power
            if field is "s":
                return a.salience
            if field is "x":
                return a.position

    def add_actor(self, actor: str) -> Actor:
        a = Actor(actor)
        self.Actors[actor] = a
        return a

    def add_issue(self, name: str, human: str):
        self.Issues.append(name)
        self.ActorIssues[name] = {}

    def add_actor_issue(self, actor: str, issue: str, position: Decimal, salience: Decimal,
                        power: Decimal) -> ActorIssue:
        a = self.Actors[actor]

        ai = ActorIssue(a, position, salience, power)
        ai.Issue = issue

        self.ActorIssues[issue][a.Name] = ai

        return ActorIssue

    def add_exchange(self, i: Actor, j: Actor, p: str, q: str, groups) -> None:
        e = Exchange(i, j, p, q, self, groups)
        e.calculate()
        self.Exchanges.append(e)
        return e

    def calc_nbs(self):
        for k, v in self.ActorIssues.items():
            self.nbs_denominators[k] = calc_nbs_denominator(v)

            self.nbs[k] = calc_nbs(v, self.nbs_denominators[k])

    def determine_positions(self):
        for k, v in self.nbs.items():
            for actorIssue in self.ActorIssues[k].values():
                actorIssue.is_left_to_nbs(v)

    def calc_combinations(self):
        self.issue_combinations = combinations(self.Issues, 2)

    def determine_groups(self):
        for combination in self.issue_combinations:

            pos = [[], [], [], []]

            for k, actor in self.Actors.items():

                a0 = self.get_actor_issue(actor=actor, issue=combination[0])
                a1 = self.get_actor_issue(actor=actor, issue=combination[1])

                if a0 is not False and a1 is not False:
                    position = a0.left | a1.left * 2

                    pos[position].append(actor)

            id = "{0}-{1}".format(combination[0], combination[1])

            self.groups[id] = {"a": pos[0], "b": pos[1], "c": pos[2], "d": pos[3]}

            for i in pos[0]:
                for j in pos[3]:
                    self.add_exchange(i, j, combination[0], combination[1], groups=['a', 'd'])

                    self.ActorIssues[str(combination[0])][i.Name].group = "a"
                    self.ActorIssues[str(combination[1])][j.Name].group = "d"

            for i in pos[1]:
                for j in pos[2]:
                    self.add_exchange(i, j, combination[0], combination[1], groups=['a', 'd'])
                    self.ActorIssues[combination[0]][i.Name].group = "b"
                    self.ActorIssues[combination[1]][j.Name].group = "c"

    def sort_exchanges(self):
        self.Exchanges.sort(key=attrgetter("gain"), reverse=True)  # .sort(key=lambda x: x.count, reverse=True)

    def highest_gain(self) -> Exchange:
        # To sort the list in place...
        self.sort_exchanges()

        return self.Exchanges.pop(0)

    def update_exchanges(self, res: Exchange):
        length = len(self.Exchanges)

        valid_exchanges = []

        for i in range(length):
            self.Exchanges[i].recalculate(res)

            if self.Exchanges[i].is_valid:
                valid_exchanges.append(self.Exchanges[i])

        self.Exchanges = valid_exchanges
