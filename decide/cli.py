import decimal
import os
from datetime import datetime

from decide.model.equalgain import EqualGainModel
from decide.model.helpers import helpers, csvparser
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver
from decide.model.randomrate import RandomRateModel


def init_model(args):
    """
    Initial the right model from the given arguments
    """

    if args.model == "equal":
        p = decimal.Decimal(args.p) if args.p != 'None' else None
        model = EqualGainModel(randomized_value=p)
    else:
        model = RandomRateModel()

    model.data_set_name = args.input_file.split("/")[-1].split(".")[0]

    return model


def init_event_handlers(model, output_directory):
    event_handler = Observable(model_ref=model, output_directory=output_directory)

    SQLiteObserver(event_handler)

    # csv handlers
    Externalities(event_handler)
    ExchangesWriter(event_handler)
    IssueDevelopment(event_handler)

    return event_handler


def init_output_directory(model, args):

    output_directory = os.path.join(args.output, model.data_set_name, model.model_name)

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    return output_directory


def main():
    start_time = datetime.now()  # for timing operations

    args = helpers.parse_arguments()

    model = init_model(args)

    output_directory = init_output_directory(model, args)

    # The event handlers for logging and writing the results to the disk.
    event_handler = init_event_handlers(model, output_directory=output_directory)
    event_handler.log(message="Start calculation at {0}".format(start_time))

    csv_parser = csvparser.CsvParser(model)
    csv_parser.read(args.input_file)

    event_handler.log(message="Parsed file".format(args.input))

    event_handler.before_repetitions(repetitions=args.repetitions, iterations=args.iterations)

    for repetition in range(args.repetitions):

        csv_parser.read(args.input_file)

        model_loop = helpers.ModelLoop(model, event_handler, repetition)

        event_handler.before_iterations(repetition)

        for iteration_number in range(args.iterations):
            print("round {0}.{1}".format(repetition, iteration_number))
            model_loop.loop()

        event_handler.after_iterations(repetition)

    event_handler.after_repetitions()

    event_handler.log(message="Finished in {0}".format(datetime.now() - start_time))


if __name__ == "__main__":
    main()
