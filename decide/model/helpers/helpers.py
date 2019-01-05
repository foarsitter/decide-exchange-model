import argparse
import logging
import os
import re
import subprocess
import sys
import traceback

from decide import log_filename
from decide.model import base
from . import csvparser


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="This program accepts input with a dot (.) as decimal separator. \n"
        "Parameters:\n{0} is for defining an actor,\n"
        "{1} for an issue,\n"
        "{2} for actor values for each issue.\n"
        "We expect for {2} the following order in values: "
        "actor, issue, position, salience, power".format(
            csvparser.CsvParser.cA, csvparser.CsvParser.cP, csvparser.CsvParser.cD
        )
    )
    parser.add_argument(
        "--model",
        "-m",
        help='The type of the model. The options are "equal" for the Equal Gain model and '
        '"random" for the RandomRate model ',
        default="equal",
        type=str,
    )

    parser.add_argument(
        "--p", "-p", help="Randomized Equal Gain", default=None, type=str
    )
    parser.add_argument(
        "--iterations",
        "-i",
        help="The number of round the model needs to be executed",
        default=10,
        type=int,
    )
    parser.add_argument(
        "--repetitions",
        "-r",
        help="How many times it has te be repeated?",
        default=1,
        type=int,
    )
    parser.add_argument(
        "--input_file",
        help="The location of the csv input file. ",
        default="../data/input/sample_data.txt",
        type=str,
    )
    parser.add_argument(
        "--output_dir", help="Output directory ", default="../data/output/", type=str
    )
    parser.add_argument(
        "--database",
        help="The SQLite database",
        default="../data/output/decide-data_1.db",
        type=str,
    )

    parser.add_argument("--step", default=None, type=str)
    parser.add_argument("--stop", default=None, type=str)
    parser.add_argument("--start", default=None, type=str)
    parser.add_argument("--actors", default=None, type=str)
    parser.add_argument("--issues", default=None, type=str)

    return parser.parse_args()


def create_key(value):
    """
    Create a safe for for index usage
    :type value: str
    """
    pattern = re.compile("[\W_]+")
    return pattern.sub("", value).lower()


class ModelLoop(object):
    def __init__(self, model, event_handler: "observer.Observable", repetition: int):
        self.model = model
        self.event_handler = event_handler
        self.iteration_number = 0
        self.repetition_number = repetition

    def loop(self):
        self.model.calc_nbs()
        self.model.determine_positions()
        self.model.calc_combinations()
        self.model.determine_groups()

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


def example_data_file_path(filename):
    """
    :param filename:
    :type filename: str
    :return: full path to filename.csv
    :rtype: str
    """
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "..",
        "..",
        "..",
        "data",
        "input",
        "{}.csv".format(filename),
    )


def log_settings():
    """
    Reads the settings file into a string and logs it as info
    """

    settings_file = open("decide-settings.xml")

    settings_content = settings_file.read()

    logging.info(settings_content)


def open_file(path):

    if sys.platform.startswith("darwin"):
        subprocess.call(("open", path))
    elif os.name == "nt":
        os.startfile(path)
    elif os.name == "posix":
        subprocess.call(("xdg-open", path))


def exception_hook(exctype, ex, _traceback):
    """
    Setting the system exception hook so the exception will be logged and the log file displayed
    """

    tb_lines = traceback.format_exception(ex.__class__, ex, ex.__traceback__)
    tb_text = ''.join(tb_lines)
    logging.exception(tb_text)

    open_file(log_filename)

    sys.exit(1)
