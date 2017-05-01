import os
from datetime import datetime

from model.helpers import helpers, csvParser
from model.helpers.helpers import ModelLoop
from model.observers.exchanges_writer import ExchangesWriter
from model.observers.externalities import Externalities
from model.observers.issue_development import IssueDevelopment
from model.observers.observer import Observable

if __name__ == "__main__":

    args = helpers.parse_arguments()
    input_file = args.input
    output_dir = args.output

    output_directory = output_dir + "/" + input_file.split("/")[-1].split(".")[0]

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    if args.model == "equal":
        from model.equalgain import EqualGainModel as Model
    else:
        from model.randomrate import RandomRateModel as Model

    startTime = datetime.now()

    model = Model()

    # The event handlers for logging and writing the results to the disk.
    eventHandler = Observable(model_ref=model, output_directory=output_directory)
    eventHandler.log(message="Start calculation at {0}".format(startTime))

    csvParser = csvParser.Parser(model)

    model = csvParser.read(input_file)

    Externalities(eventHandler)
    ExchangesWriter(eventHandler)
    IssueDevelopment(eventHandler)

    eventHandler.log(message="Parsed file".format(input_file))

    eventHandler.before_repetitions()

    for repetition in range(args.repetitions):

        model_loop = ModelLoop(model, eventHandler, repetition)

        eventHandler.before_iterations(repetition)

        for iteration_number in range(args.rounds):
            model_loop.loop()

        eventHandler.after_iterations(repetition)

    eventHandler.after_repetitions()

    eventHandler.log(message="Finished in {0}".format(datetime.now() - startTime))
