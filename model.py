

if __name__ == "__main__":

    import os
    from datetime import datetime

    from model.helpers import helpers, csvParser
    from model.helpers.helpers import ModelLoop
    from model.observers.exchanges_writer import ExchangesWriter
    from model.observers.externalities import Externalities
    from model.observers.issue_development import IssueDevelopment
    from model.observers.observer import Observable

    args = helpers.parse_arguments()
    input_file = args.input
    output_dir = args.output

    output_directory = output_dir + "/" + input_file.split("/")[-1].split(".")[0]
    output_directory = output_directory + "/" + args.model

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    if args.model == "equal":
        import model.equalgain as Model

        model = Model.EqualGainModel()
    else:
        import model.randomrate as Model

        model = Model.RandomRateModel()

    startTime = datetime.now()

    # The event handlers for logging and writing the results to the disk.
    eventHandler = Observable(model_ref=model, output_directory=output_directory)
    eventHandler.log(message="Start calculation at {0}".format(startTime))

    csvParser = csvParser.Parser(model)

    Externalities(eventHandler)
    ExchangesWriter(eventHandler)
    IssueDevelopment(eventHandler)

    eventHandler.log(message="Parsed file".format(input_file))

    eventHandler.before_repetitions()

    for repetition in range(args.repetitions):

        model = csvParser.read(input_file)

        model_loop = ModelLoop(model, eventHandler, repetition)

        eventHandler.before_iterations(repetition)

        for iteration_number in range(args.rounds):
            print("round {0}.{1}".format(repetition, iteration_number))
            model_loop.loop()

        eventHandler.after_iterations(repetition)

    eventHandler.after_repetitions()

    eventHandler.log(message="Finished in {0}".format(datetime.now() - startTime))
