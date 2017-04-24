import argparse
import re
from model.helpers.csvParser import Parser
from model.observers.observer import Observable, Observer


def parse_arguments():
    parser = argparse.ArgumentParser(description="This program accepts input with a dot (.) as decimal separator. \n"
                                                 "Parameters:\n{0} is for defining an actor,\n"
                                                 "{1} for an issue,\n"
                                                 "{2} for actor values for each issue.\n"
                                                 "We expect for {2} the following order in values: "
                                                 "actor, issue, position, salience, power".format(Parser.cA, Parser.cP,
                                                                                                  Parser.cD))
    parser.add_argument('--model',
                        help='The type of the model. The options are "equal" for the Equal Gain model and '
                             '"random" for the RandomRate model ',
                        default='equal', type=str)

    parser.add_argument('--rounds', help='The number of round the model needs to be executed', default=10, type=int)
    parser.add_argument('--input', help='The location of the csv input file. ', default="data/input/sample_data.txt", type=str)
    parser.add_argument('--output', help='Output directory ', default="data/output/", type=str)

    return parser.parse_args()


def create_key(value):
    """
    Create a safe for for index usage
    :type value: str
    """
    pattern = re.compile('[\W_]+')
    return pattern.sub('', value).lower()


class ModelLoop(object):
    def __init__(self, model, event_handler: Observable):
        self.model = model
        self.event_handler = event_handler
        self.iteration_number = 0

    def loop(self):
        self.model.calc_nbs()
        self.model.determine_positions()
        self.model.calc_combinations()
        self.model.determine_groups()

        realized = []

        # call the event for beginning the loop
        self.event_handler.before_loop(self.iteration_number)

        while len(self.model.exchanges) > 0:

            realize_exchange = self.model.highest_gain()

            if realize_exchange and realize_exchange.is_valid:
                removed_exchanges = self.model.remove_invalid_exchanges(realize_exchange)

                realized.append(realize_exchange)

                self.event_handler.removed_exchanges(removed_exchanges)
                self.event_handler.execute_exchange(realize_exchange)
            else:
                print(realize_exchange)

        # call the event for ending the loop
        self.event_handler.after_loop(realized=realized, iteration=self.iteration_number)

        for exchange in realized:
            self.model.actor_issues[exchange.i.supply_issue][exchange.i.actor_name].position = exchange.i.y
            self.model.actor_issues[exchange.j.supply_issue][exchange.j.actor_name].position = exchange.j.y

        # calc the new NBS on the voting positions and fire the event for ending this loop
        self.model.calc_nbs()
        self.event_handler.end_loop(iteration=self.iteration_number)

        # calculate for each realized exchange there new start positions
        for exchange in realized:
            pi = exchange.i.new_start_position()
            self.model.actor_issues[exchange.i.supply_issue][exchange.i.actor_name].position = pi

            pj = exchange.j.new_start_position()
            self.model.actor_issues[exchange.j.supply_issue][exchange.j.actor_name].position = pj

        self.iteration_number += 1
