import csv
from csv import excel

import csvWriter
from datetime import datetime
import collections
import calculations
import itertools
from csvParser import Parser
from objects.update_listeners.observer import Observable, Observer
from objects.update_listeners.update_listener import Updater, Logger
from objects.update_listeners.externalities import Externalities
from objects.update_listeners.exchanges_writer import ExchangesWriter

# The event handlers for logging and writing the results to the disk.
eventHandler = Observable()

Updater(eventHandler)
Logger(eventHandler)



startTime = datetime.now()

eventHandler.notify(Observable.LOG, "Start calculation at {0}".format(startTime))

csvParser = Parser()

current_file = "verkiezing 2012"
model = csvParser.read("data/{0}.csv".format(current_file))

Externalities(eventHandler, model, current_file)
ExchangesWriter(eventHandler, model, current_file)

eventHandler.notify(Observable.LOG, "Parsed file".format(current_file))

# collect the data
history = {}
externalities = []
ext_realizations = []
ext_connections = []

# TODO: this should be calculated in an event
for issue in model.ActorIssues:

    issue_list = {}

    for key, actor_issue in model.ActorIssues[issue].items():
        issue_list[actor_issue.actor_name] = []
        issue_list[actor_issue.actor_name].append(actor_issue.position)

    issue_list["nbs"] = []
    history[issue] = issue_list

#start = 0
stop = 10

for iteration_number in range(stop):

    model.calc_nbs()
    model.determine_positions()
    model.calc_combinations()
    model.determine_groups()

    realized = []

    while len(model.Exchanges) > 0:
        realize = model.highest_gain()

        # TODO: write a method to check is there are more exchanges with an equal gain.

        # TEST BLOCK
        # if len(model.Exchanges) > 0:
        #
        #     # TODO: this should be done in an unit-test
        #     if abs(realize.gain - model.Exchanges[0].gain) == 0:
        #         if realize.i.actor_name == "ALBA" and realize.i.supply == "financewho" and realize.j.actor_name == "Umbrellamin":
        #             model.Exchanges.append(realize)
        #             realize = model.highest_gain()
        #         elif realize.i.actor_name == "EU28" and realize.i.supply == "eaa" and realize.j.actor_name == "China" and realize.j.supply == "mrv":
        #             model.Exchanges.append(realize)
        #             realize = model.highest_gain()
        #         elif realize.i.actor_name == "LDC" and realize.i.supply == "progress" and realize.j.actor_name == "Brazil" and realize.j.supply == "adaptfinance":
        #             model.Exchanges.append(realize)
        #             realize = model.highest_gain()
        #         elif realize.i.actor_name == "Arabstates" and realize.i.supply == "progress" and realize.j.actor_name == "LDC" and realize.j.supply == "financewho":
        #             model.Exchanges.append(realize)
        #             realize = model.highest_gain()
        #         elif realize.i.actor_name == "EU28" and realize.i.supply == "financewho" and realize.j.actor_name == "Brazil" and realize.j.supply == "legal":
        #             model.Exchanges.append(realize)
        #             realize = model.highest_gain()
        #             # else:
        #             #     # print(str(model.Exchanges[0]))
        # # end if

        removed_exchanges = model.remove_invalid_exchanges(realize)
        eventHandler.notify(Observable.REMOVED, model, removed_exchanges)
        eventHandler.notify(Observable.EXECUTED, model, realize)
        realized.append(realize)
    # end while

    eventHandler.notify(Observable.FINISHED_ROUND, model, realized, iteration_number)

    for issue in model.ActorIssues:
        for key, actor_issue in model.ActorIssues[issue].items():
            history[issue][key].append(actor_issue.position)

        history[issue]["nbs"].append(model.nbs[issue])
        # end for

    for exchange in realized:
        model.ActorIssues[exchange.i.supply][exchange.i.actor_name].position = exchange.i.new_start_position()
        model.ActorIssues[exchange.j.supply][exchange.j.actor_name].position = exchange.j.new_start_position()
        # end for
# end for




for issue in history:
    with open("output/{3}/{0}.{1}.{2}".format("output", issue, "csv", current_file), 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')

        writer.writerow(["Actor I", "Supply I", "Actor J", "Supply J"])

        for key, value in history[issue].items():
            writer.writerow([key] + value)
            # end for
            # end with
# end for

eventHandler.notify(Observable.CLOSE)
eventHandler.notify(Observable.LOG, "Finished in {0}".format(datetime.now() - startTime))

# eof
