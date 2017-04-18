import argparse
import re
from model.helpers.csvParser import Parser
from model.observers.observer import Observable

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
    def __init__(self, model, event_handler):
        self.model = model
        self.event_handler = event_handler
        self.iteration_number = 0

    def loop(self):
        self.model.calc_nbs()
        self.model.determine_positions()
        self.model.calc_combinations()
        self.model.determine_groups()

        realized = []

        self.event_handler.notify(Observable.START_ROUND, model=self.model, iteration=self.iteration_number)

        while len(self.model.Exchanges) > 0:

            realize = self.model.highest_gain()

            if realize and realize.is_valid:
                removed_exchanges = self.model.remove_invalid_exchanges(realize)

                realized.append(realize)

                self.event_handler.notify(Observable.REMOVED, model=self.model, removed=removed_exchanges)
                self.event_handler.notify(Observable.EXECUTED, model=self.model, realized=realize)
            else:
                print(realize)
        # end while

        self.event_handler.notify(Observable.FINISHED_ROUND, model=self.model, realized=realized, iteration=self.iteration_number)

        for exchange in realized:
            self.model.ActorIssues[exchange.i.supply_issue][exchange.i.actor_name].position = exchange.i.y
            self.model.ActorIssues[exchange.j.supply_issue][exchange.j.actor_name].position = exchange.j.y

        # calc the new NBS on the voting positions
        self.model.calc_nbs()
        self.event_handler.notify(Observable.PREPARE_NEXT_ROUND, model=self.model, realized=realized, iteration=self.iteration_number)

        # calculate for each realized exchange there new start positions
        for exchange in realized:
            pi = exchange.i.new_start_position()
            self.model.ActorIssues[exchange.i.supply_issue][exchange.i.actor_name].position = pi

            pj = exchange.j.new_start_position()
            self.model.ActorIssues[exchange.j.supply_issue][exchange.j.actor_name].position = pj

        self.iteration_number += 1
