import csv

from model.equalgain import EqualGainExchange


class CsvWriter:
    def __init__(self):
        self.var = "x"
        self.file = "data/output"

    def write(self, filename, realized):
        with open(filename, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', lineterminator='\n')

            writer.writerow(self.create_heading(realized[0]))

            for exchange in realized:
                writer.writerow(self.create_row(exchange))

    @staticmethod
    def create_row(exchange):

        if isinstance(exchange, EqualGainExchange):
            return [
                # the actors
                exchange.i.actor_name,
                exchange.i.supply_issue,
                exchange.i.c,
                exchange.i.s / exchange.i.s_demand,
                "-",
                exchange.i.x,
                exchange.i.move,
                exchange.i.y,
                exchange.i.opposite_actor.x_demand,
                exchange.gain,
                "",
                exchange.j.actor_name,
                exchange.j.supply_issue,
                exchange.j.c,
                exchange.j.s / exchange.j.s_demand,
                "-",
                exchange.j.x,
                exchange.j.move,
                exchange.j.y,
                exchange.j.opposite_actor.x_demand,
                exchange.gain]
        else:
            return [
                # the actors
                exchange.i.actor_name,
                exchange.i.supply_issue,
                exchange.i.eu,
                exchange.i.is_highest_gain,
                exchange.j.actor_name,
                exchange.j.supply_issue,
                exchange.j.eu,
                exchange.j.is_highest_gain,
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

    @staticmethod
    def create_heading(exchange):

        if isinstance(exchange, EqualGainExchange):
            return [
                # the actors
                "actor_name",  # exchange.i.actor_name,
                "supply",  # exchange.i.supply,
                "power",
                "sal s/d",
                "preference",
                "start",
                "move",
                "voting",
                "demand",
                "gain",
                "",
                "actor_name",  # exchange.i.actor_name,
                "supply",  # exchange.i.supply,
                "power",
                "sal s/d",
                "preference",
                "start",
                "move",
                "voting",
                "demand",
                "gain"]

        return [
            # the actors
            "actor_name",  # exchange.i.actor_name,
            "supply",  # exchange.i.suply,
            "gain",
            "highest",
            "actor_name",  # exchange.j.actor_name,
            "supply",  # exchange.j.supply,
            "gain",
            "highest",
            # the move of i
            "supply",  # exchange.i.x,
            "move",  # exchange.i.move,
            "y",  # exchange.i.y,
            "demand",  # exchange.i.opposite_actor.x_demand,
            # the move of j
            "supply",  # exchange.j.x,
            "move",  # exchange.j.move,
            "y",  # exchange.j.y,
            "demand",  # exchange.j.opposite_actor.x_demand,
            # other info.
            "dp",  # exchange.dp,
            "dq",  # exchange.dq,
            "nbs_0",  # exchange.i.nbs_0,
            "nbs_1",  # exchange.i.nbs_1,
            "nbs_0",  # exchange.j.nbs_0,
            "nbs_1"]  # exchange.j.nbs_1]

# nbs info
