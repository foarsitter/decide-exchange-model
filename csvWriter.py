import csv
from typing import List

from objects.EqualExchange import Exchange


class csvWriter:
    def __init__(self):
        self.var = "x"
        self.file = "output"

    def write(self, filename, realized: List[Exchange]):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')

            for exchange in realized:
                writer.writerow(self.create_row(exchange))

    def create_row(self, exchange: Exchange):
        return [
            # the actors
            exchange.i.actor_name,
            exchange.i.supply,
            exchange.j.actor_name,
            exchange.j.supply,
            exchange.gain,
            # the move of i
            exchange.i.x,
            exchange.i.move,
            exchange.i.y,
            exchange.i.opposite_actor.x_demand,
            # the move of j
            exchange.j.x,
            exchange.j.move,
            exchange.j.y,
            exchange.j.opposite_actor.x_demand,
            # other info.
            exchange.dp,
            exchange.dq,
            exchange.i.nbs_0,
            exchange.i.nbs_1,
            exchange.j.nbs_0,
            exchange.j.nbs_1]

        # nbs info
