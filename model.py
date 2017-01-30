from datetime import datetime

from model.helpers import helpers, csvParser
from model.helpers.helpers import ModelLoop
from model.observers.exchanges_writer import ExchangesWriter
from model.observers.externalities import Externalities
from model.observers.history_writer import HistoryWriter
from model.observers.initial_exchanges import InitialExchanges
from model.observers.logger import Logger
from model.observers.observer import Observable


if __name__ == "__main__":

    args = helpers.parse_arguments()
    input_file = args.input
    output_dir = args.output

    data_set_name = input_file.split("/")[-1].split(".")[0]

    if args.model == "equal":
        from model.equalgain import EqualGainModel as Model
    else:
        from model.randomrate import RandomRateModel as Model

    # The event handlers for logging and writing the results to the disk.
    eventHandler = Observable()
    Logger(eventHandler)

    startTime = datetime.now()

    eventHandler.notify(Observable.LOG, message="Start calculation at {0}".format(startTime))

    model = Model()

    csvParser = csvParser.Parser(model)

    model = csvParser.read(input_file)

    Externalities(eventHandler, model, data_set_name)
    ExchangesWriter(eventHandler, model, data_set_name)
    HistoryWriter(eventHandler, model, data_set_name)
    InitialExchanges(eventHandler)
    eventHandler.notify(Observable.LOG, message="Parsed file".format(input_file))

    model_loop = ModelLoop(model, eventHandler)

    for iteration_number in range(args.rounds):
        model_loop.loop()




