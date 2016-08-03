import calculations
from objects.Actor import Actor


class Exchange:
    def __init__(self, i: Actor, j: Actor, p: str, q: str, m):
        self.model = m
        self.gain = 0
        self.is_valid = True
        self.re_calc = False
        self.p = p
        self.q = q

        # c.	If (1) holds, i shifts his position on issue p in the direction of j,
        # whereas j shifts his position on issue q in the direction of i.
        # Issue p is then called the supply issue of i and the demand issue of j,
        # whereas issue q is the demand issue of i and the supply issue of j.
        # If (2) holds,
        # issue q is the supply issue of i and issue p is the supply issue of j.
        # if ( (model$s_matrix[p, i] / model$s_matrix[q, i]) < (model$s_matrix[p, j] / model$s_matrix[q, j]))
        if (m.get(i, p, "s") / m.get(i, q, "s")) < (m.get(j, p, "s") / m.get(j, q, "s")):
            self.i = ExchangeActor(m, j, supply=q, demand=p)
            self.j = ExchangeActor(m, i, supply=p, demand=q)
        else:
            self.i = ExchangeActor(m, i, supply=q, demand=p)
            self.j = ExchangeActor(m, j, supply=p, demand=q)

        self.j.opposite_actor = self.i
        self.i.opposite_actor = self.j

    def calculate(self):
        # first we try to move j to the position of i on issue p
        # we start with the calculation for j
        dp = calculations.by_absolute_move(self.model.ActorIssues[self.j.supply], self.j)
        dq = calculations.by_exchange_ratio(self.j, dp)

        move_i = calculations.reverse_move(self.model.ActorIssues[self.i.supply], self.i, dq)
        move_j = abs(self.i.x_demand - self.j.x)

        if abs(move_i) > abs(self.j.x_demand - self.i.x):
            dq = calculations.by_absolute_move(self.model.ActorIssues[self.i.supply], self.i)
            dp = calculations.by_exchange_ratio(self.i, dq)

            move_i = abs(self.j.x_demand - self.i.x)
            move_j = calculations.reverse_move(self.model.ActorIssues[self.j.supply], self.j, dp)

        # TODO add check of NBS.
        # this check is only necessary for the smallest exchange,
        # because if the smallest exchange exceeds the limit the larger one will definitely do so

        if self.i.x > self.j.x_demand:
            move_i *= -1

        if self.j.x > self.i.x_demand:
            move_j *= -1

        self.i.moves.append(move_i)
        self.j.moves.append(move_j)

        self.i.y = self.i.x + move_i
        self.j.y = self.j.x + move_j

        eui = calculations.gain(self.i, dq, dp)
        euj = calculations.gain(self.j, dp, dq)

        if abs(eui - euj) > 0.0001:
            raise Exception("Expected equal gain")
        else:
            self.gain = abs(eui)

        b1 = self.i.is_move_valid(move_i)
        b2 = self.j.is_move_valid(move_j)

        self.is_valid = b1 and b2

        if self.is_valid:
            # TODO garbage code, korsakov code or something like that
            # Need sto be methodical approached
            nbs_i0 = self.model.nbs[self.i.supply]
            nbs_i = calculations.calc_adjusted_nbs(self.model.ActorIssues[self.i.supply], self.i.actor, self.i.y)

            if self.j.x_demand > nbs_i0 and self.j.x_demand > nbs_i:
                pass
            elif self.j.x_demand < nbs_i0 and self.j.x_demand < nbs_i:
                pass
            else:
                self.is_valid = False

            nbs_j0 = self.model.nbs[self.j.supply]
            nbs_j = calculations.calc_adjusted_nbs(self.model.ActorIssues[self.j.supply], self.j.actor, self.j.y)

            if self.i.x_demand > nbs_j0 and self.i.x_demand > nbs_j:
                pass
            elif self.i.x_demand < nbs_j0 and self.i.x_demand < nbs_j:
                pass
            else:
                self.is_valid = False

    def recalculate(self, exchange: 'Exchange'):
        # update supply positions

        self.re_calc = False

        # TODO create a method inside ExchangeActor for comparison, gets ugly
        if self.i.actor.Name == exchange.i.actor.Name and self.i.supply == exchange.i.supply:
            self.i.x = exchange.i.y
            self.i.moves.pop()
            self.j.moves.pop()
            self.i.moves.append(exchange.i.moves[-1])
            self.re_calc = True
        elif self.i.actor.Name == exchange.j.actor.Name and self.i.supply == exchange.j.supply:
            self.i.x = exchange.j.y
            self.i.moves.pop()
            self.j.moves.pop()
            self.i.moves.append(exchange.j.moves[-1])
            self.re_calc = True

        if self.j.actor.Name == exchange.i.actor.Name and self.j.supply == exchange.i.supply:
            self.j.x = exchange.i.y
            self.i.moves.pop()
            self.j.moves.pop()
            self.j.moves.append(exchange.i.moves[-1])
            self.re_calc = True
        elif self.j.actor.Name == exchange.j.actor.Name and self.j.supply == exchange.j.supply:
            self.j.x = exchange.j.y
            self.i.moves.pop()
            self.j.moves.pop()
            self.j.moves.append(exchange.j.moves[-1])
            self.re_calc = True

        if self.re_calc:
            self.calculate()

    def __str__(self):
        return "{0}: {1}, {2}".format(round(self.gain, 9), str(self.i), str(self.j))


class ExchangeActor:
    def __init__(self, model, actor: Actor, demand: str, supply: str):
        self.c = model.get(actor, supply, "c")
        self.s = model.get(actor, supply, "s")
        self.x = model.get(actor, supply, "x")
        self.y = 0

        self.c_demand = model.get(actor, demand, "c")
        self.s_demand = model.get(actor, demand, "s")
        self.x_demand = model.get(actor, demand, "x")

        self.start_position = self.x

        self.demand = demand
        self.supply = supply

        self.actor = actor

        self.opposite_actor = None

        self.moves = []

    def is_move_valid(self, move):
        # a move cannot exceed the interval [0,100]
        if abs(move) > 100 or abs(move) <= 1e-10:
            return False

        # if an exchange is on the edges there is no move posible
        if self.x + move < 0 or self.x + move > 100:
            return False

        if len(self.moves) == 1:
            return True

        if sum(self.moves) > 100:
            return False

        moves_min = min(self.moves)
        moves_max = max(self.moves)

        if moves_min < 0 and moves_max < 0 or moves_min > 0 and moves_max:
            return True
            # newMoves < - c(self$moves, move) < 0
            #
            # return (isTRUE(all.equal(min(newMoves), max(newMoves))))

    def __str__(self):
        return "{0} {1} {2} {3} ({4})".format(self.actor.Name, self.supply, self.x, self.y,
                                              self.opposite_actor.x_demand)
