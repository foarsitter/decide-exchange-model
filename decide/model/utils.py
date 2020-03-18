import logging


class ModelLoop(object):
    """
    Helps performing all the actions in the correct order
    """

    def __init__(self, model, event_handler: "observer.Observable", repetition: int):
        self.model = model
        self.event_handler = event_handler
        self.iteration_number = 0
        self.repetition_number = repetition

    def loop(self):
        self.model.calc_nbs()
        self.model.determine_positions()
        self.model.calc_combinations()
        self.model.determine_groups_and_calculate_exchanges()

        realized = []

        # call the event for beginning the loop
        self.event_handler.before_loop(self.iteration_number, self.repetition_number)

        while len(self.model.exchanges) > 0:

            realize_exchange = self.model.highest_gain()  # type: base.AbstractExchange

            if realize_exchange and realize_exchange.is_valid:
                removed_exchanges = self.model.remove_invalid_exchanges(
                    realize_exchange
                )

                realized.append(realize_exchange)

                self.event_handler.removed_exchanges(removed_exchanges)
                self.event_handler.execute_exchange(realize_exchange)
            else:
                if self.model.VERBOSE:
                    logging.info(realize_exchange)

        # call the event for ending the loop
        self.event_handler.after_loop(
            realized=realized,
            iteration=self.iteration_number,
            repetition=self.repetition_number,
        )

        for exchange in realized:
            self.model.actor_issues[exchange.i.supply.issue][
                exchange.i.actor
            ].position = exchange.i.y
            self.model.actor_issues[exchange.j.supply.issue][
                exchange.j.actor
            ].position = exchange.j.y

        # calc the new NBS on the voting positions and fire the event for ending this loop
        self.model.calc_nbs()
        self.event_handler.end_loop(
            iteration=self.iteration_number, repetition=self.repetition_number
        )

        # calculate for each realized exchange there new start positions
        for exchange in realized:
            pi = exchange.i.new_start_position()
            self.model.actor_issues[exchange.i.supply.issue][
                exchange.i.actor
            ].position = pi

            pj = exchange.j.new_start_position()
            self.model.actor_issues[exchange.j.supply.issue][
                exchange.j.actor
            ].position = pj

        self.iteration_number += 1
