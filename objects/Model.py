from itertools import combinations
from typing import List

from calculations import calc_nbs
from objects.Actor import Actor
from objects.ActorIssue import ActorIssue
from objects.Exchange import Exchange


class Model:
    Issues = {}
    Actors = {}
    ActorIssues = {}  # type: List[ActorIssue]
    Exchanges = []  # type: List[Exchange]

    def __init__(self):
        self.Issues = []
        self.ActorIssues = {}
        self.Actors = {}
        self.Exchanges = []
        self.nbs = {}
        self.issue_combinations = []
        self.groups = {}

    def get_actor_issue(self, actor: Actor, issue: str):
        try:
            return self.ActorIssues[issue][actor.Id]
        except IndexError:
            return None

    def get(self, actor: Actor, issue: str, field: str):

        a = None

        try:
            a = self.ActorIssues[issue][actor.Id]
        except IndexError:
            return None

        if field is "c":
            return a.Power
        if field is "s":
            return a.Salience
        if field is "x":
            return a.Position

    def add_actor(self, actor: str) -> Actor:
        a = Actor(actor)
        a.Id = len(self.Actors)
        self.Actors[actor] = a
        return a

    def add_issue(self, name: str, human: str):
        self.Issues.append(name)
        self.ActorIssues[name] = []

    def add_actor_issue(self, actor: str, issue: str, position: float, salience: float, power: float) -> ActorIssue:
        a = self.Actors[actor]
        # i = self.Issues[issue]

        ai = ActorIssue(position, salience, power)
        ai.Issue = issue

        self.ActorIssues[issue].append(ai)

        return ActorIssue

    def add_exchange(self, i: Actor, j: Actor, p: str, q: str) -> None:

        e = Exchange(i, j, p, q, self)
        e.calc()
        self.Exchanges.append(e)
        return e

    def calc_nbs(self):
        for k, v in self.ActorIssues.items():
            self.nbs[k] = calc_nbs(v)

    def determine_positions(self):
        for k, v in self.nbs.items():
            for actorIssue in self.ActorIssues[k]:
                actorIssue.is_left_to_nbs(v)

    def calc_combinations(self):
        self.issue_combinations = combinations(self.Issues, 2)

    def determine_groups(self):
        for combination in self.issue_combinations:

            pos = [[], [], [], []]

            for k, actor in self.Actors.items():

                a0 = self.get_actor_issue(actor=actor, issue=combination[0])
                a1 = self.get_actor_issue(actor=actor, issue=combination[1])

                if a0 is not None and a1 is not None:
                    position = a0.Left | a1.Left * 2

                    pos[position].append(actor)

            for i in pos[0]:
                for j in pos[3]:
                    self.add_exchange(i, j, combination[0], combination[1])

            for i in pos[1]:
                for j in pos[2]:
                    self.add_exchange(i, j, combination[0], combination[1])

            id = "{0}-{1}".format(combination[0], combination[1])

            self.groups[id] = {"a": pos[0], "b": pos[1], "c": pos[2], "d": pos[3]}

    def highest_gain(self):
        # To sort the list in place...
        self.Exchanges.sort(key=lambda x: x.gain, reverse=True)  # .sort(key=lambda x: x.count, reverse=True)

        return self.Exchanges.pop(0)
