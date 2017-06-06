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
                exchange.i.c,
                exchange.i.s / exchange.i.s_demand,
                exchange.i.x,
                exchange.i.move,
                exchange.i.y,
                exchange.i.opposite_actor.x_demand,
                exchange.i.eu, exchange.dp,
                "",
                exchange.j.actor_name,
                exchange.j.supply_issue,
                exchange.j.c,
                exchange.j.s / exchange.j.s_demand,
                exchange.j.x,
                exchange.j.move,
                exchange.j.y,
                exchange.j.opposite_actor.x_demand,
                exchange.j.eu, exchange.dq]

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
            "actor",
            "issue",
            "power",
            "sal s/d",
            "start",
            "move",
            "voting",
            "demand",
            "gain",
            "exchange ratio",
            "",
            "actor",
            "issue",
            "power",
            "sal s/d",
            "start",
            "move",
            "voting",
            "demand",
            "gain",
            "exchange ratio"]
