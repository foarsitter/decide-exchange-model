import argparse
import logging
import os
from datetime import datetime
from typing import List

from decide import input_folder
from decide.data.modelfactory import ModelFactory
from decide.data.reader import InputDataFile
from decide.model import randomrate, equalgain
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.logger import Logger
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver
from decide.model.utils import ModelLoop


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Decide exchange model".format()
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
        default=os.path.join(input_folder, 'sample_data.txt'),
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

    parser.add_argument("--step", default='0.80', type=str)
    parser.add_argument("--stop", default='0.80', type=str)
    parser.add_argument("--start", default='0.0', type=str)
    parser.add_argument("--name", default=None, type=str)
    parser.add_argument("--actors", default=None, type=str)
    parser.add_argument("--issues", default=None, type=str)

    return parser.parse_args()


def init_event_handlers(model, output_directory, database_file, write_csv=True):
    event_handler = Observable(model_ref=model, output_directory=output_directory)

    SQLiteObserver(event_handler, output_directory)

    Logger(event_handler)
    Logger.LOG_LEVEL = 99

    if write_csv:
        # csv handlers
        Externalities(event_handler)
        ExchangesWriter(event_handler)
        IssueDevelopment(event_handler)

    return event_handler


def init_output_directory(*args):
    output_directory = os.path.join(*args)

    if not os.path.isdir(output_directory):

        if os.path.isfile(output_directory):
            output_directory += '_output'

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

    return output_directory


def float_range(start=0.0, stop=1.0, step=0.05):
    # when the step size is 0, return
    if step == 0:
        yield 0
    else:
        # prevent locking yourself out
        if (stop - start) / step > 256:
            raise RuntimeError("Maximum steps exceeded with step={} (256)".format(step))

        i = start
        # add a 10th step to stop for floating point rounding differences 0.500001 vs 0.499999
        while i < (stop + step / 10):
            yield i
            i += step


def actors_param(args) -> List[str]:
    actors = None
    if args.actors:
        actors = args.actors.split(
            ";"
        )

    return actors


def issues_param(args) -> List[str]:
    issues = None

    if args.issues:
        issues = args.issues.split(
            ";"
        )

    return issues


def p_values_param(args) -> List[float]:
    p_values = []

    if args.start and args.step and args.stop:
        p_values = [
            str(round(p, 2))
            for p in float_range(
                start=float(args.start), step=float(args.step), stop=float(args.stop)
            )
        ]

    elif args.p:

        if ";" in args.p:
            p_values += args.p.split(";")
        else:
            p_values.append(args.p)

    return p_values


def main():
    args = parse_arguments()

    p_values = p_values_param(args)
    issues = issues_param(args)
    actors = actors_param(args)

    data_file = InputDataFile.open(args.input_file)

    data_set_name = os.path.splitext(os.path.basename(args.name or args.input_file))[0]

    factory = ModelFactory(data_file, actor_whitelist=actors, issue_whitelist=issues)

    """
        Initial the right model from the given arguments
        """

    if args.model == "equal":
        model_klass = equalgain.EqualGainModel
    else:
        model_klass = randomrate.RandomRateModel

    for p in p_values:

        start_time = datetime.now()  # for timing operations

        model = factory(model_klass=model_klass, randomized_value=p)

        output_directory = init_output_directory(
            args.output_dir,
            data_set_name,
            p,
        )

        # The event handlers for logging and writing the results to the disk.
        event_handler = init_event_handlers(
            model=model,
            output_directory=output_directory,
            database_file=args.database,
            write_csv=True,
        )

        event_handler.log(message="Start calculation at {0}".format(start_time))

        event_handler.log(message="Parsed file".format(args.input_file))

        event_handler.before_repetitions(
            repetitions=args.repetitions, iterations=args.iterations
        )

        for repetition in range(args.repetitions):

            model = factory(model_klass=model_klass, randomized_value=p)

            event_handler.update_model_ref(model)

            model_loop = ModelLoop(model, event_handler, repetition)

            event_handler.before_iterations(repetition)

            for iteration_number in range(args.iterations):
                logging.info("round {0}.{1}".format(repetition, iteration_number))
                model_loop.loop()

            event_handler.after_iterations(repetition)

        event_handler.after_repetitions()

        event_handler.log(message="Finished in {0}".format(datetime.now() - start_time))

    logging.info("Done")


if __name__ == "__main__":
    main()
