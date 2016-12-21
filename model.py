from datetime import datetime

from model.helpers import helpers, csvParser
from model.observers.exchanges_writer import ExchangesWriter
from model.observers.externalities import Externalities
from model.observers.history_writer import HistoryWriter
from model.observers.initial_exchanges import InitialExchanges
from model.observers.observer import Observable
from model.observers.logger import Logger

args = helpers.parse_arguments()
input_file = args.input
output_dir = args.output

data_set_name = input_file.split("/")[-1].split(".")[0]

if args.model == "equal":
	from model.equal.EqualGainModel import Model
else:
	from model.random.RandomRateModel import Model

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

# collect the data
history = {}
externalities = []
ext_realizations = []
ext_connections = []

# TODO: this should be calculated in an event


for iteration_number in range(args.rounds):

	model.calc_nbs()
	model.determine_positions()
	model.calc_combinations()
	model.determine_groups()

	realized = []

	eventHandler.notify(Observable.START_ROUND, model=model, iteration=iteration_number)

	while len(model.Exchanges) > 0:

		realize = model.highest_gain()

		if realize.is_valid:
			removed_exchanges = model.remove_invalid_exchanges(realize)

			realized.append(realize)

			eventHandler.notify(Observable.REMOVED, model=model, removed=removed_exchanges)
			eventHandler.notify(Observable.EXECUTED, model=model, realized=realize)
	# end while

	eventHandler.notify(Observable.FINISHED_ROUND, model=model, realized=realized, iteration=iteration_number)

	# calculate for each realized exchange there new start positions
	for exchange in realized:
		model.ActorIssues[exchange.i.supply][exchange.i.actor_name].position = exchange.i.new_start_position()
		model.ActorIssues[exchange.j.supply][exchange.j.actor_name].position = exchange.j.new_start_position()
	# end for
# end for

eventHandler.notify(Observable.CLOSE, model=model)
eventHandler.notify(Observable.LOG, message="Finished in {0}".format(datetime.now() - startTime))
# eof
