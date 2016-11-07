from decimal import *
from itertools import combinations
from operator import attrgetter

from calculations import calc_nbs, calc_nbs_denominator

from objects.ActorIssue import ActorIssue
from objects.RandomExchange import Exchange


class RandomRateModel:
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

    def get_actor_issue(self, actor_name: str, issue: str):

        if actor_name in self.ActorIssues[issue]:
            return self.ActorIssues[issue][actor_name]
        else:
            return False

    def get_value(self, actor_name: str, issue: str, field: str):

        a = self.ActorIssues[issue][actor_name]

        if a is not False:

            if field is "c":
                return a.power
            if field is "s":
                return a.salience
            if field is "x":
                return a.position

    def add_actor(self, actor_name: str) -> str:

        self.Actors[actor_name] = actor_name
        return self.Actors[actor_name]

    def add_issue(self, issue_name: str, human: str):
        self.Issues.append(issue_name)
        self.ActorIssues[issue_name] = {}

    def add_actor_issue(self, actor_name: str, issue_name: str, position: Decimal, salience: Decimal,
                        power: Decimal) -> ActorIssue:

        self.ActorIssues[issue_name][actor_name] = ActorIssue(actor_name, issue_name, position, salience, power)

        return self.ActorIssues[issue_name][actor_name]

    def add_exchange(self, i: str, j: str, p: str, q: str, groups) -> None:
        e = Exchange(i, j, p, q, self, groups)
        e.calculate()
        self.Exchanges.append(e)
        return e

    def calc_nbs(self):
        for issue, actor_issues in self.ActorIssues.items():
            self.nbs_denominators[issue] = calc_nbs_denominator(actor_issues)

            self.nbs[issue] = calc_nbs(actor_issues, self.nbs_denominators[issue])

    def determine_positions(self):
        for issue, issue_nbs in self.nbs.items():
            for actorIssue in self.ActorIssues[issue].values():
                actorIssue.is_left_to_nbs(issue_nbs)

    def calc_combinations(self):
        self.issue_combinations = combinations(self.Issues, 2)

    def determine_groups(self):
        for combination in self.issue_combinations:

            pos = [[], [], [], []]

            for k, actor in self.Actors.items():

                a0 = self.get_actor_issue(actor_name=actor, issue=combination[0])
                a1 = self.get_actor_issue(actor_name=actor, issue=combination[1])

                if a0 is not False and a1 is not False:
                    position = a0.left | a1.left * 2

                    pos[position].append(actor)

            id = "{0}-{1}".format(combination[0], combination[1])

            self.groups[id] = {"a": pos[0], "b": pos[1], "c": pos[2], "d": pos[3]}

            for i in pos[0]:
                for j in pos[3]:
                    self.add_exchange(i, j, combination[0], combination[1], groups=['a', 'd'])

                    self.ActorIssues[str(combination[0])][i].group = "a"
                    self.ActorIssues[str(combination[1])][j].group = "d"

            for i in pos[1]:
                for j in pos[2]:
                    self.add_exchange(i, j, combination[0], combination[1], groups=['b', 'c'])
                    self.ActorIssues[combination[0]][i].group = "b"
                    self.ActorIssues[combination[1]][j].group = "c"

    def sort_exchanges(self):
        self.Exchanges.sort(key=attrgetter("gain"), reverse=True)  # .sort(key=lambda x: x.count, reverse=True)

    def highest_gain(self) -> Exchange:
        # To sort the list in place...
        self.sort_exchanges()

        return self.Exchanges.pop(0)

    def remove_invalid_exchanges(self, res: Exchange):
        length = len(self.Exchanges)

        valid_exchanges = []
        invalid_exchanges = []
        for i in range(length):
            self.Exchanges[i].recalculate(res)

            if self.Exchanges[i].is_valid:
                valid_exchanges.append(self.Exchanges[i])
            else:
                invalid_exchanges.append(self.Exchanges[i])

        self.Exchanges = valid_exchanges

        return invalid_exchanges
