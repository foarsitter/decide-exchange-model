import logging
import decimal
import os
from datetime import datetime

from decide.model import randomrate, equalgain
from decide.model.helpers import helpers, csvparser
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver


def init_model(model_type, input_file, p=None):
    """
    Initial the right model from the given arguments
    """

    if model_type == "equal":
        p = decimal.Decimal(p) if p else 0.0
        model = equalgain.EqualGainModel(randomized_value=p)
    else:
        model = randomrate.RandomRateModel()

    model.data_set_name = input_file.split("/")[-1].split(".")[0]

    return model


def init_event_handlers(model, output_directory, database_file, write_csv=True):
    event_handler = Observable(model_ref=model, output_directory=output_directory)

    # SQLiteObserver(event_handler, database_file)

    if write_csv:
        # csv handlers
        Externalities(event_handler)
        ExchangesWriter(event_handler)
        IssueDevelopment(event_handler)

    return event_handler


def init_output_directory(model, output_dir, selected_actors=list()):
    actor_unique = '-'.join(selected_actors)

    output_directory = os.path.join(output_dir, model.data_set_name, model.model_name, actor_unique)

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    return output_directory


def main():
    start_time = datetime.now()  # for timing operations

    args = helpers.parse_arguments()

    model = init_model(args.model, args.input_file, args.p)

    output_directory = init_output_directory(model, args.output_dir)

    # The event handlers for logging and writing the results to the disk.
    event_handler = init_event_handlers(
        model=model,
        output_directory=output_directory,
        database_file=args.database,
        write_csv=True
    )

    event_handler.log(message="Start calculation at {0}".format(start_time))

    csv_parser = csvparser.CsvParser(model)
    csv_parser.read(args.input_file)

    event_handler.log(message="Parsed file".format(args.input_file))

    event_handler.before_repetitions(repetitions=args.repetitions, iterations=args.iterations)

    for repetition in range(args.repetitions):

        csv_parser.read(args.input_file)

        model_loop = helpers.ModelLoop(model, event_handler, repetition)

        event_handler.before_iterations(repetition)

        for iteration_number in range(args.iterations):
            logging.info("round {0}.{1}".format(repetition, iteration_number))
            model_loop.loop()

        event_handler.after_iterations(repetition)

    event_handler.after_repetitions()

    event_handler.log(message="Finished in {0}".format(datetime.now() - start_time))


if __name__ == "__main__":
    main()
