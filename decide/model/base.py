import logging
from collections import defaultdict
from decimal import Decimal
from itertools import combinations
from typing import List


class Issue:
    def __init__(self, name, lower=None, upper=None):
        """
        Refers an issue
        :param name: str
        :param lower: int
        :param upper: int
        """
        self.delta = 0
        self.step_size = 0

        self.name = name

        self.lower = lower
        self.upper = upper

        self.comment = ""

        if self.lower is not None or self.upper is not None:
            self.calculate_delta()
            self.calculate_step_size()

    @property
    def issue_id(self):
        return self.name

    def calculate_delta(self):
        self.delta = self.upper - self.lower

    def calculate_step_size(self):
        if self.delta != 0:
            self.step_size = Decimal(100 / self.delta)
        else:
            self.step_size = 0

    def de_normalize(self, value):
        if value == 0:
            return self.lower

        return value / self.step_size + self.lower

    def normalize(self, value):
        return Decimal(value - self.lower) * self.step_size

    def expand_lower(self, value):

        if self.lower is None:
            self.lower = value
        elif value < self.lower:
            self.lower = value

    def expand_upper(self, value):
        if self.upper is None:
            self.upper = value
        elif value > self.upper:
            self.upper = value

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{0} [{1} - {2}]".format(self.name, self.lower, self.upper)

    def __eq__(self, other):

        if isinstance(other, str):
            b = self.issue_id == other
            return b

        if isinstance(other, Issue):
            return self.issue_id == other.issue_id

        if isinstance(other, int):
            h = self.__hash__()
            b = h == other
            return b

        if not other:
            return False

        raise NotImplementedError()

    def __hash__(self):
        return hash(self.issue_id)

    def __lt__(self, other):
        """
        Needed for sorting
        :param other:
        :return:
        """
        return self.issue_id < other.issue_id


class Actor:
    def __init__(self, name, actor_id=None):
        """
        Represents an Actor
        """
        self.name = name
        self.comment = ""

        if actor_id:
            self.actor_id = actor_id
        else:
            self.actor_id = name

    def __eq__(self, other):

        from decide.data.database import Actor as ModelActor

        if isinstance(other, str):
            return self.actor_id == str(other)
        if isinstance(other, int):
            return self.__hash__() == other
        if isinstance(other, Actor):
            return self.actor_id == other.actor_id
        if isinstance(other, ModelActor):
            return self.actor_id == other.key
        if not other:
            return False
        raise NotImplementedError()

    def __lt__(self, other):
        """
        Needed for sorting
        :param other:
        :return:
        """
        if not isinstance(other, Actor):
            raise ValueError("error")

        return self.actor_id < other.actor_id

    def __hash__(self):
        """
        Hashing is based on the id
        :return:
        """
        return hash(self.actor_id)

    def __str__(self):
        """
        Human representation of this object
        :return:
        """
        return self.name


class ActorIssue:
    """
    Represents a combination between an actor and issue
    """

    def __init__(self, actor: Actor, issue: Issue, position, salience, power):
        """
        :param actor: Actor 
        :param issue: Issue
        :param position: Double
        :param salience: Double
        :param power: Double
        """

        self.actor = actor
        self.power = Decimal(power)
        self.position = Decimal(position)
        self.salience = Decimal(salience)
        self.left = False  # left of nbs
        self.issue = issue

    def is_left_to_nbs(self, nbs):
        """
        True when the position is lower than the Nash Bargaining Solution for this issue. 
        :param nbs: int
        :return: bool 
        """
        self.left = self.position <= nbs
        return self.left

    def __str__(self):
        return "{0} on {1} with x={2}, s={3}, c={4}".format(
            self.actor.name, self.issue.name, self.position, self.salience, self.power
        )

    def __eq__(self, other):
        """
        True when the name and issue are the same
        :param other: 
        :return: 
        """
        if isinstance(other, ActorIssue):
            return self.actor == other.actor and self.issue == other.issue

        return NotImplemented

    def __lt__(self, other):
        return self.actor < other.actor


class DemandActorIssue(ActorIssue):
    """
    Object for a demand issue, has the same properties as a ActorIssue
    """

    def __init__(self, actor_issue: ActorIssue):
        super().__init__(
            actor_issue.actor,
            actor_issue.issue,
            actor_issue.position,
            actor_issue.salience,
            actor_issue.power,
        )

        self.actor_issue = actor_issue


class SupplyActorIssue(ActorIssue):
    """
    Object for a demand issue, has a extra voting_position (self.y)
    """

    def __init__(self, actor_issue: ActorIssue, y=None):
        super().__init__(
            actor_issue.actor,
            actor_issue.issue,
            actor_issue.position,
            actor_issue.salience,
            actor_issue.power,
        )

        self.y = y
        self.actor_issue = actor_issue


class AbstractExchangeActor:
    """
    Represents an exchange actor. Contains his demand and supply issues and voting-position
    """

    def __init__(
            self,
            model: "AbstractModel",
            actor: Actor,
            demand_issue: Issue,
            supply_issue: Issue,
            exchange: "AbstractExchange",
    ):
        """
        Constructor, must be invoked

        :param model: AbstractModel
        :param actor: Actor
        :param demand_issue: Issue
        :param supply_issue: Issue
        :param exchange: AbstractExchange
        """
        # the actor
        self.actor = actor

        # create supply and demand issues from the ActorIssues
        self.supply = SupplyActorIssue(model.actor_issues[supply_issue][actor])
        self.demand = DemandActorIssue(model.actor_issues[demand_issue][actor])

        # the voting position for the supply issue
        self.y = None
        self.start_position = self.supply.position

        # the expected utility
        self.eu = 0

        self.opposite_actor = None  # type: AbstractExchangeActor
        # current move (should be equal with self.y - self.supply.position
        self.move = 0

        # history of moves
        self.moves = []

        # placeholder for the nbs before this exchange and after
        self.nbs_0 = 0
        self.nbs_1 = 0

        # backref to the exchange object and model
        self.exchange = exchange
        self.model = model

        self.is_adjusted_by_nbs = False

    def is_move_valid(self, move):

        """
        Cheks if a move not exceeds the interval [0,100]

        :param move:
        :return:
        """
        if abs(move) > 100 or abs(move) <= 1e-10:
            return False

        # if an exchange is on the edges there is no move posible
        if self.supply.position + move < 0 or self.supply.position + move > 100:
            return False

        if sum(self.moves) > 100:
            return False

        moves_min = min(self.moves)
        moves_max = max(self.moves)

        if (moves_min < 0 and moves_max < 0) or (moves_min > 0 and moves_max > 0):
            return True

    def new_start_position(self):
        """
        Calculate the new starting postion for the next round
        :return:
        """
        from decide.model import calculations

        return calculations.new_start_position(
            salience=self.supply.salience,
            x=self.start_position,
            y=self.y,
            salience_weight=self.model.SALIENCE_WEIGHT,
            fixed_weight=self.model.FIXED_WEIGHT,
        )

    def actor_issues(self):
        """ shortcut, demand ActorIssues should never not be needed """
        return self.supply_actor_issues()

    def supply_actor_issues(self):
        """ shortcut function"""
        return self.model.actor_issues[self.supply.issue]

    def demand_actor_issues(self):
        """ shortcut function"""
        return self.model.actor_issues[self.demand.issue]

    def adjust_nbs(self, position):

        actor_issues = self.actor_issues()

        updates = self.exchange.updates[self.supply.issue]

        from . import calculations  # Todo should be global import

        return calculations.adjusted_nbs(
            actor_issues=actor_issues,
            updates=updates,
            actor=self.actor,
            new_position=position,
            denominator=self.model.nbs_denominators[self.supply.issue],
        )

    def equals_actor_demand_issue(self, other: "AbstractExchangeActor"):
        """
        Has this ExchangeActor the same actor and same demand issue
        :param other:
        :return:
        """
        return self.equals_actor(other) and self.equals_demand_issue(other)

    def equals_actor_supply_issue(self, other: "AbstractExchangeActor"):
        """
        Has this ExchangeActor the same actor and same supply issue
        :param other:
        :return:
        """
        return self.equals_actor(other) and self.equals_supply_issue(other)

    def equals_actor(self, other):
        """
        Has this ExchangeActor the same actor
        :param other:
        :return:
        """
        return self.actor == other.actor

    def equals_supply_issue(self, other: "AbstractExchangeActor"):
        """
        Has this ExchangeActor the same supply issue
        :param other: AbstractExchangeActor
        :return:
        """
        return self.supply.issue == other.supply.issue

    def equals_demand_issue(self, other: "AbstractExchangeActor"):
        """
        Has this ExchangeActor the same demand issue?
        :param other: AbstractExchangeActor
        :return:
        """
        return self.demand.issue == other.demand.issue

    def check_nbs(self):
        """
        Calculate if the outcome doesn't shifts over the original position of the demand actor of his first exchange.
        :return:
        """

        from . import calculations

        self.nbs_0 = self.adjust_nbs(self.supply.position)

        self.nbs_1 = self.adjust_nbs(self.y)

        x = self.opposite_actor.demand.position

        check = round(self.opposite_actor.demand.position, 3) >= round(
            self.nbs_0, 3
        ) and round(self.opposite_actor.demand.position, 3) >= round(self.nbs_1, 3)
        check_2 = round(self.opposite_actor.demand.position, 3) <= round(
            self.nbs_0, 3
        ) and round(self.opposite_actor.demand.position, 3) <= round(self.nbs_1, 3)

        if (x - self.nbs_0) >= 0 and (x - self.nbs_1) >= 0:
            if not check:
                raise Exception("test")
        elif (x - self.nbs_0) <= 0 and (x - self.nbs_1) <= 0:
            if not check_2:
                raise Exception("test123")
        else:
            delta = abs(
                calculations.adjusted_nbs_by_position(
                    actor_issues=self.actor_issues(),
                    updates=self.exchange.updates[self.supply.issue],
                    actor=self.actor,
                    x_pos=self.supply.position,
                    new_nbs=self.opposite_actor.demand.position,
                    denominator=self.model.nbs_denominators[self.supply.issue],
                )
            )

            self.exchange.dp = calculations.exchange_ratio(
                delta_x=delta,
                salience=self.supply.salience,
                power=self.supply.power,
                denominator=self.model.nbs_denominators[self.supply.issue],
            )

            self.exchange.dq = calculations.by_exchange_ratio(self, self.exchange.dp)

            self.opposite_actor.move = abs(
                calculations.reverse_move(
                    actor_issues=self.opposite_actor.actor_issues(),
                    actor=self.opposite_actor,
                    exchange_ratio=self.exchange.dq,
                )
            )

            self.move = delta

            if self.opposite_actor.supply.position > self.demand.position:
                self.opposite_actor.move *= -1

            if self.supply.position > self.opposite_actor.demand.position:
                self.move *= -1

            self.opposite_actor.moves.pop()
            self.moves.pop()
            self.opposite_actor.moves.append(self.opposite_actor.move)
            self.moves.append(self.move)

            self.opposite_actor.y = (
                    self.opposite_actor.supply.position + self.opposite_actor.move
            )
            self.y = self.supply.position + self.move

            eui = calculations.expected_utility(
                self.opposite_actor, self.exchange.dq, self.exchange.dp
            )
            euj = calculations.expected_utility(
                self, self.exchange.dp, self.exchange.dq
            )

            if abs(eui - euj) > 0.0001:
                raise Exception("Expected equal gain")
            else:
                self.exchange.gain = abs(eui)

            b1 = self.opposite_actor.is_move_valid(self.opposite_actor.move)
            b2 = self.is_move_valid(self.move)

            self.nbs_1 = self.adjust_nbs(self.y)

            if abs(self.nbs_1 - self.y) > 1e-10:
                logging.debug(
                    "The new calculated NBS is not exactly the same as the new position of the actor (nbs 0 {} nbs 1: {} y: {})".format(
                        self.nbs_0, self.nbs_1, self.y
                    )
                )

            self.exchange.is_valid = b1 and b2

            self.is_adjusted_by_nbs = True

    def __str__(self):
        """
        The String representation of the object
        :return: String representation of the object
        """

        if hasattr(self, "eu"):
            return "{0} {1} eu={2}, x={3} y={4}, d={5}".format(
                self.actor.name,
                self.supply.issue.name,
                round(self.eu, 2),
                self.supply.position,
                self.y,
                self.opposite_actor.demand.position,
            )
        else:
            return "{0} {1} {2} {3} ({4})".format(
                self.actor.name,
                self.supply.issue.name,
                self.supply.position,
                self.y,
                self.opposite_actor.demand.position,
            )

    def __eq__(self, other):
        return (
                self.equals_actor(other)
                and self.equals_demand_issue(other)
                and self.equals_supply_issue(other)
        )


class AbstractExchange:
    """
    An exchange between two actors and two issues. Each actor has a demand and supply issue
    """

    actor_class = AbstractExchangeActor

    def __init__(self, i, j, p, q, m, groups):
        """
        An exchange between two actors and two issues. Each actor has a demand and supply issue
        :param i: Actor
        :param j: Actor
        :param p: Issue
        :param q: Issue
        :param m: AbstractModel
        :param groups: tuple of the two groups each actor is in
        """
        self.model = m
        self.groups = groups

        # if the groups are not valid exit
        self.validate_groups()

        self.gain = 0  # expected utility
        self.is_valid = True
        self.re_calc = False
        self.p = p
        self.q = q

        self.dp = 0
        self.dq = 0

        self.updates = defaultdict(dict)

        # c.	If (1) holds, i shifts his position on issue p in the direction of j,
        # whereas j shifts his position on issue q in the direction of i.
        # Issue p is then called the supply issue of i and the demand issue of j,
        # whereas issue q is the demand issue of i and the supply issue of j.
        # If (2) holds,
        # issue q is the supply issue of i and issue p is the supply issue of j.
        # if ( (model$s_matrix[p, i] / model$s_matrix[q, i]) < (model$s_matrix[p, j] / model$s_matrix[q, j]))
        if (m.get_value(i, p, "s") / m.get_value(i, q, "s")) < (
                m.get_value(j, p, "s") / m.get_value(j, q, "s")
        ):
            self.i: AbstractExchangeActor = self.actor_class(
                m, j, supply_issue=q, demand_issue=p, exchange=self
            )
            self.j: AbstractExchangeActor = self.actor_class(
                m, i, supply_issue=p, demand_issue=q, exchange=self
            )
        else:
            self.i: AbstractExchangeActor = self.actor_class(
                m, i, supply_issue=q, demand_issue=p, exchange=self
            )
            self.j: AbstractExchangeActor = self.actor_class(
                m, j, supply_issue=p, demand_issue=q, exchange=self
            )

        self.j.opposite_actor = self.i
        self.i.opposite_actor = self.j

    def calculate(self):
        """Method stub to be overriden"""
        raise NotImplementedError

    def invalidate_move(self):
        self.i.moves.pop()
        self.j.moves.pop()

    def invalidate_exchange_by_supply(self, exchange):

        """
        If the actors and supply issues match one or both the actors from the exchange that is executed,
        this exchange invalidates and needs to be recalculated.

        When the move invalidates, erase the current values for the move so the new values can be calculated.

        If both the cases happen (i equals j and j equals i) the exchange is identical, this is not posible.

        :param exchange:
        :return:
        """
        invalid_i = False
        invalid_j = False

        if self.i.equals_actor_supply_issue(exchange.i):
            self.i.supply.position = exchange.i.y
            self.i.moves.append(exchange.i.moves[-1])
            invalid_i = True
        elif self.i.equals_actor_supply_issue(exchange.j):
            self.i.supply.position = exchange.j.y
            self.i.moves.append(exchange.j.moves[-1])
            invalid_i = True

        if self.j.equals_actor_supply_issue(exchange.i):
            self.j.supply.position = exchange.i.y
            self.j.moves.append(exchange.i.moves[-1])
            invalid_j = True
        elif self.j.equals_actor_supply_issue(exchange.j):
            self.j.supply.position = exchange.j.y
            self.j.moves.append(exchange.j.moves[-1])
            invalid_j = True

        if invalid_i or invalid_j:
            self.invalidate_move()
        elif invalid_i and invalid_j:
            raise Exception(
                "Exchanges are equal: {0} and {1}".format(str(self), str(exchange))
            )

        return invalid_i or invalid_j

    def update_updates(
            self,
            exchange_actor: AbstractExchangeActor,
            demand_issue: Issue,
            updated_position,
    ):
        """
        Update the updates dictionary with the current exchange
        :param exchange_actor:
        :param demand_issue:
        :param updated_position:
        """

        # if the start position is left of the updated_position then TODO
        if exchange_actor.start_position <= updated_position:
            # what is this?
            if updated_position < exchange_actor.y:
                self.updates[demand_issue][exchange_actor.actor] = updated_position
            else:
                self.updates[demand_issue][exchange_actor.actor] = exchange_actor.y
        else:
            if updated_position > exchange_actor.y:
                self.updates[demand_issue][exchange_actor.actor] = updated_position
            else:
                self.updates[demand_issue][exchange_actor.actor] = exchange_actor.y

    def recalculate(self, exchange):
        """
        This exchange needs to be recalculated because the given exchange is performed
        and has an influence on this (self) exchange
        :param exchange:
        """
        self.re_calc = self.invalidate_exchange_by_supply(exchange)

        # update the positions for the demand actors...
        if exchange.j.equals_actor_demand_issue(
                self.j
        ) or exchange.j.equals_actor_demand_issue(self.i):

            if exchange.i.actor in self.updates[exchange.j.demand.issue]:
                self.update_updates(
                    exchange.i,
                    exchange.j.demand.issue,
                    self.updates[exchange.j.demand.issue][exchange.i.actor],
                )
            else:
                self.updates[exchange.j.demand.issue][exchange.i.actor] = exchange.i.y

            if not self.re_calc:
                self.invalidate_move()
                self.re_calc = True

        if exchange.i.equals_actor_demand_issue(
                self.j
        ) or exchange.i.equals_actor_demand_issue(self.i):

            if exchange.j.actor in self.updates[exchange.i.demand.issue]:
                self.update_updates(
                    exchange.j,
                    exchange.i.demand.issue,
                    self.updates[exchange.i.demand.issue][exchange.j.actor],
                )
            else:
                self.updates[exchange.i.demand.issue][exchange.j.actor] = exchange.j.y

            if not self.re_calc:
                self.invalidate_move()
                self.re_calc = True

        if self.re_calc:
            self.calculate()

    def validate_groups(self):
        """
        Two actors can only exchange when they are in group a-d or b-c
        :return:
        """
        if "a" in self.groups and "d" in self.groups:
            return True
        elif "b" in self.groups and "c" in self.groups:
            return True
        else:
            raise Exception(
                "invalid group combination [%,%]".format(self.groups[0], self.groups[1])
            )

    def get_inner_groups(self):
        """
        When groups[0] is not a and not d, the b&c group is inner.
        If groups[0] == a, then groups[1] has to be D
        """

        if len(self.groups) != 2:
            raise ValueError("Too much groups given!")

        if "a" in self.groups and "d" in self.groups:
            return ["a", "d"]

        if "b" in self.groups and "c" in self.groups:
            return ["b", "c"]

        raise ValueError(
            "Actors should only exchange with their inner group."
            " The given groups are {0}".format(self.groups)
        )

    def __str__(self):
        return "{0}: {1}, {2}".format(round(self.gain, 9), str(self.i), str(self.j))

    def __bool__(self):
        return self.is_valid

    def __eq__(self, other):
        return self.i == other.i and self.j == other.j


class AbstractModel:
    SALIENCE_WEIGHT = 0.4
    FIXED_WEIGHT = 0.1
    VERBOSE = True  # verbose messages for debugging

    def __init__(self, *args, **kwargs):
        self.issues = {}
        self.actor_issues = defaultdict(dict)
        self.actors = {}
        self.exchanges: List[AbstractExchange] = []
        self.nbs = {}
        self.issue_combinations = []
        self.groups = {}
        self.moves = {}  # dict with issue,actor[move_1,move_2,move_3]
        self.nbs_denominators = {}
        self.data_set_name = ""
        self.model_name = "abstract"
        self.tie_count = 0

    def get_actor_issue(self, actor: Actor, issue: Issue):
        """
        Getter function for an ActorIssue
        :param actor: the id of the actor
        :param issue: the id of the issue
        :return:
        """
        if actor in self.actor_issues[issue]:
            return self.actor_issues[issue][actor]
        else:
            return False

    def get_value(self, actor: Actor, issue: Issue, field):
        """
        Get the value of an attribute for an actor on the specified issue
        :param actor: str
        :param issue: str
        :param field: str
        :return: Double
        """

        a = self.actor_issues[issue][actor]

        if a is not False:

            if field == "c":
                return a.power
            if field == "s":
                return a.salience
            if field == "x":
                return a.position

        raise ValueError("ActorIssue not found")

    def add_actor(self, actor_name, actor_id=None, comment="") -> Actor:
        """
        Add an actor to the model
        :param comment:
        :param actor_id:
        :param actor_name:
        :return:
        """
        actor = Actor(actor_name, actor_id)
        actor.comment = comment
        self.actors[actor] = actor
        return actor

    def add_issue(self, issue_name, issue_id=None, comment="") -> Issue:
        """
        Add an issue to the model
        :param comment:
        :param issue_id:
        :param issue_name:
        """
        issue = Issue(issue_name)
        issue.comment = comment
        self.issues[issue] = issue
        return issue

    def add_actor_issue(self, actor, issue, position, salience, power):
        """
        Add an actor issue to the model
        :param actor: Actor
        :param issue: Issue
        :param position: Double
        :param salience: Double
        :param power: Double
        :return:
        """

        if not isinstance(actor, Actor):
            if actor in self.actors:
                actor = self.actors[actor]
            elif hash(actor) in self.actors:
                actor = self.actors[hash(actor)]
            else:
                raise ValueError("Actor not found: {0}".format(actor))

        if not isinstance(issue, Issue):
            if issue in self.issues:
                issue = self.issues[issue]
            elif hash(issue) in self.issues:
                issue = self.issues[hash(issue)]
            else:
                raise ValueError(
                    "The issue '{0}' is missing in your input file. "
                    "Define '#P' with '{0}' and add a description".format(issue)
                )

        self.actor_issues[issue][actor] = ActorIssue(
            actor, issue, position, salience, power
        )

        return self.actor_issues[issue][actor]

    def add_exchange(self, i, j, p, q, groups):
        """
        Add an exchange pair to the model
        :param i:
        :param j:
        :param p:
        :param q:
        :param groups:
        :return:
        """
        e = self.new_exchange_factory(i, j, p, q, self, groups)
        e.calculate()
        self.eui.append(e.i.eu)
        self.exchanges.append(e)
        return e

    eui = []

    def calc_nbs(self):
        from . import calculations

        """
        Calculate the nash bargaining solution for all the issue
        """
        for issue, actor_issues in self.actor_issues.items():
            self.nbs_denominators[issue] = calculations.calc_nbs_denominator(
                actor_issues
            )

            nbs = calculations.nash_bargaining_solution(
                actor_issues, self.nbs_denominators[issue]
            )
            self.nbs[issue] = nbs

    def determine_positions(self):
        """
        Determine if the position of an actor is left or right of the Nash Bargaining Solution on an issue
        """
        for issue_name, issue_nbs in self.nbs.items():
            for actor_issue in self.actor_issues[issue_name].values():
                actor_issue.is_left_to_nbs(issue_nbs)

    def calc_combinations(self):
        """
        Create a list of all possible combinations for the issues
        """
        self.issue_combinations = combinations(self.issues, 2)

    def determine_groups_and_calculate_exchanges(self):
        """
        There are 4 groups: A, B, C, and D.
        An actor is member of group A if his position on both issues is left of the NBS.
        Each actor of group A can exchange with the actors of Group D, the actors of B with C.
        """
        for combination in self.issue_combinations:

            pos = [[], [], [], []]

            for k, actor in self.actors.items():

                a0 = self.get_actor_issue(actor=actor, issue=combination[0])
                a1 = self.get_actor_issue(actor=actor, issue=combination[1])

                # some magic happens here: we have four possibilities and two bytes, so
                # A = 00 = 0
                # B = 01 = 1
                # C = 10 = 2
                # D = 11 = 3

                if a0 is not False and a1 is not False:
                    position = a0.left | a1.left * 2
                    pos[position].append(actor)

            combination_id = "{0}-{1}".format(combination[0], combination[1])

            self.groups[combination_id] = {
                "a": pos[0],
                "b": pos[1],
                "c": pos[2],
                "d": pos[3],
            }

            # all actors of group A and D
            for i in pos[0]:
                for j in pos[3]:
                    self.add_exchange(
                        i, j, combination[0], combination[1], groups=["a", "d"]
                    )

                    self.actor_issues[combination[0]][i].group = "a"
                    self.actor_issues[combination[1]][j].group = "d"

            # all actors of group B and C
            for i in pos[1]:
                for j in pos[2]:
                    self.add_exchange(
                        i, j, combination[0], combination[1], groups=["b", "c"]
                    )
                    self.actor_issues[combination[0]][i].group = "b"
                    self.actor_issues[combination[1]][j].group = "c"

    def remove_invalid_exchanges(self, res):
        """
        Removes all the invalid exchanges from the exchanges list and return them
        :param res: a list of exchanges
        :return: a list with online valid exchanges
        """
        length = len(self.exchanges)

        valid_exchanges = []
        invalid_exchanges = []

        for i in range(length):

            if self.exchanges[i].is_valid:
                self.exchanges[i].recalculate(res)

                if self.exchanges[i].is_valid:
                    valid_exchanges.append(self.exchanges[i])
                else:
                    invalid_exchanges.append(self.exchanges[i])

        self.exchanges = valid_exchanges

        return invalid_exchanges

    def sort_exchanges(self):
        """
        Abstract method
        :return:
        """
        raise NotImplementedError

    def highest_gain(self):
        """
        Abstract method
        :return:
        """
        raise NotImplementedError

    def create_existing_issue_set_key(self, p, q):
        """
        Create a combination of issue so it can be used as key
        """
        issue_set_key = "{0}-{1}".format(p, q)
        # an combination only exists once, so it can happen that we have to change the sequence of the keys
        if issue_set_key not in self.groups:
            issue_set_key = "{0}-{1}".format(q, p)

        return issue_set_key

    def is_inner_group_member(self, actor, inner, issue_set_key):
        """
        When an actor is in the same [A] or opposing group [D], return true
        False, When in [B] or [C]
        :param actor:
        :param issue_set_key:
        :param inner:
        :return:
        """

        is_inner = (
                actor in self.groups[issue_set_key][inner[0]]
                or actor in self.groups[issue_set_key][inner[1]]
        )

        return is_inner

    @staticmethod
    def new_exchange_factory(i, j, p, q, model_ref, groups):
        """
        Creates a new Exchange set 
        :param groups: 
        :param model_ref: 
        :param q: 
        :param p: 
        :param j: 
        :param i:
        """
        raise NotImplementedError
