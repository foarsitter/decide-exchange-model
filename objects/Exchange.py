import calculations
from objects.Actor import Actor


class Exchange:
    i = None  # type: ExchangeActor
    j = None  # type: ExchangeActor
    p = None  # type: str
    q = None  # type: str

    model = None  # type: objects.Model.Model
    gain = 0

    def __init__(self, i: Actor, j: Actor, p: str, q: str, m):
        self.model = m
        self.gain = 0
        # q is supply actor of i
        self.i = ExchangeActor(m, i, supply=q, demand=p)

        # p is supply actor of j
        self.j = ExchangeActor(m, j, supply=p, demand=q)

        self.j.opposite_actor = self.i
        self.i.opposite_actor = self.j

        self.p = p
        self.q = q

        # if this conditions holds, we need to swap the actors...

        # c.	If (1) holds, i shifts his position on issue p in the direction of j,
        # whereas j shifts his position on issue q in the direction of i.
        # Issue p is then called the supply issue of i and the demand issue of j,
        # whereas issue q is the demand issue of i and the supply issue of j. If (2) holds,
        # issue q is the supply issue of i and issue p is the supply issue of j.
        # if ( (model$s_matrix[p, i] / model$s_matrix[q, i]) < (model$s_matrix[p, j] / model$s_matrix[q, j]))
        if (self.i.s_demand / self.i.s) < (self.j.s / self.j.s_demand):
            i_copy = self.i
            self.i = self.j
            self.j = i_copy

    def calc(self):
        # first we try to move j to the position of i on issue p
        is_second = False
        # we start with the calculation for j
        dp = calculations.by_absolute_move(self.model.ActorIssues[self.j.supply], self.j)
        dq = calculations.by_exchange_ratio(self.j, dp)

        move_i = calculations.reverse_move(self.model.ActorIssues[self.i.supply], self.i, dq)
        move_j = self.i.x_demand - self.j.x

        if abs(move_i) > abs(self.j.x_demand - self.i.x):
            dq = calculations.by_absolute_move(self.model.ActorIssues[self.i.supply], self.i)
            dp = calculations.by_exchange_ratio(self.i, dq)
            is_second = True
            move_i = self.j.x_demand - self.i.x
            move_j = calculations.reverse_move(self.model.ActorIssues[self.j.supply], self.j, dp)

        # TODO add check of NBS.
        # this check is only necessary for the smallest exchange,
        # because if the smallest exchange exceeds the limit the larger one will definitely do so

        self.i.moves.append(move_i)
        self.j.moves.append(move_j)

        eui = calculations.gain(self.i, dq, dp)
        euj = calculations.gain(self.j, dp, dq)

        if abs(eui - euj) > 0.0001:
            raise Exception("Expected equal gain")
        else:
            self.gain = abs(eui)


class ExchangeActor:
    actor = ""
    c = 0
    s = 0
    x = 0
    c_demand = 0
    s_demand = 0
    x_demand = 0

    start_position = 0
    demand = ""
    supply = ""
    moves = []

    opposite_actor = None  # type: ExchangeActor

    def __init__(self, model, actor: Actor, demand: str, supply: str):
        self.c = model.get(actor, supply, "c")
        self.s = model.get(actor, supply, "s")
        self.x = model.get(actor, supply, "x")

        self.c_demand = model.get(actor, demand, "c")
        self.s_demand = model.get(actor, demand, "s")
        self.x_demand = model.get(actor, demand, "x")

        self.start_position = self.x

        self.demand = demand
        self.supply = supply

        self.actor = actor

        self.moves = []

    def __str__(self):
        return self.actor.Name
