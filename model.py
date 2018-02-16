import decimal

from model.observers.sqliteobserver import SQLiteObserver

if __name__ == "__main__":

    import os
    from datetime import datetime

    from model.helpers import helpers, csvparser
    from model.helpers.helpers import ModelLoop
    from model.observers.exchanges_writer import ExchangesWriter
    from model.observers.externalities import Externalities
    from model.observers.issue_development import IssueDevelopment
    from model.observers.observer import Observable

    args = helpers.parse_arguments()
    input_file = args.input
    output_dir = args.output

    if args.model == "equal":
        import model.equalgain as Model

        if args.p != 'None':
            p = decimal.Decimal(args.p)
            model_name = 'equal-' + str(round(p, 2))
        else:
            p = None
            model_name = 'equal'

        model = Model.EqualGainModel(randomized_value=p)
    else:
        import model.randomrate as Model

        model_name = 'random'
        model = Model.RandomRateModel()

    model.data_set_name = input_file.split("/")[-1].split(".")[0]
    output_directory = output_dir + "/" + model.data_set_name
    output_directory = output_directory + "/" + model_name

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    startTime = datetime.now()

    # The event handlers for logging and writing the results to the disk.
    eventHandler = Observable(model_ref=model, output_directory=output_directory)
    eventHandler.log(message="Start calculation at {0}".format(startTime))

    csvParser = csvparser.CsvParser(model)
    csvParser.read(input_file)

    SQLiteObserver(eventHandler)

    # csv handlers
    Externalities(eventHandler)
    ExchangesWriter(eventHandler)
    IssueDevelopment(eventHandler)

    eventHandler.log(message="Parsed file".format(input_file))

    eventHandler.before_repetitions(repetitions=args.repetitions, iterations=args.rounds)

    for repetition in range(args.repetitions):

        csvParser.read(input_file)

        model_loop = ModelLoop(model, eventHandler, repetition)

        eventHandler.before_iterations(repetition)

        for iteration_number in range(args.rounds):
            print("round {0}.{1}".format(repetition, iteration_number))
            model_loop.loop()

        eventHandler.after_iterations(repetition)

    eventHandler.after_repetitions()

    eventHandler.log(message="Finished in {0}".format(datetime.now() - startTime))
