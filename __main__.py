import csv
from datetime import datetime

import calculations
from csvParser import Parser

startTime = datetime.now()

csvParser = Parser()
model = csvParser.read("data/CoP21.csv")

# issue,actor, position

history = {}
externalities = []
ext_realizations = []
ext_connections = []
for issue in model.ActorIssues:

    issue_list = {}

    for key, actor_issue in model.ActorIssues[issue].items():
        issue_list[actor_issue.actor.Name] = []
        issue_list[actor_issue.actor.Name].append(actor_issue.position)

    issue_list["nbs"] = []
    # issue_list["nbs"].append(model.nbs[issue])

    history[issue] = issue_list

start = 0
stop = 2

for i_round in range(start, stop):

    # for issue in model.ActorIssues:
    #
    #     # if not os.path.exists("{0}/{1}".format("output", issue)):
    #     #     os.makedirs("{0}/{1}".format("output", issue))
    #
    #     # with open("output/{1}/{0}.{2}".format(i_round, issue, "output.csv"), 'w', newline='') as csvfile:
    #     #     writer = csv.writer(csvfile, delimiter=';')
    #
    #     for key, actor_issue in model.ActorIssues[issue].items():
    #         writer.writerow([actor_issue.actor.Name, actor_issue.position])

    model.calc_nbs()
    model.determine_positions()
    model.calc_combinations()
    model.determine_groups()

    realized = []

    while len(model.Exchanges) > 0:
        realize = model.highest_gain()

        if len(model.Exchanges) > 0:

            if abs(realize.gain - model.Exchanges[0].gain) == 0:
                if realize.i.actor.Name == "ALBA" and realize.i.supply == "financewho" and realize.j.actor.Name == "Umbrellamin":
                    model.Exchanges.append(realize)
                    realize = model.highest_gain()
                elif realize.i.actor.Name == "EU28" and realize.i.supply == "eaa" and realize.j.actor.Name == "China" and realize.j.supply == "mrv":
                    model.Exchanges.append(realize)
                    realize = model.highest_gain()
                elif realize.i.actor.Name == "LDC" and realize.i.supply == "progress" and realize.j.actor.Name == "Brazil" and realize.j.supply == "adaptfinance":
                    model.Exchanges.append(realize)
                    realize = model.highest_gain()
                elif realize.i.actor.Name == "Arabstates" and realize.i.supply == "progress" and realize.j.actor.Name == "LDC" and realize.j.supply == "financewho":
                    model.Exchanges.append(realize)
                    realize = model.highest_gain()
                elif realize.i.actor.Name == "EU28" and realize.i.supply == "financewho" and realize.j.actor.Name == "Brazil" and realize.j.supply == "legal":
                    model.Exchanges.append(realize)
                    realize = model.highest_gain()
                else:
                    pass  # print(str(model.Exchanges[0]))

        model.update_exchanges(realize)
        realized.append(realize)

    ext = {}
    ext_realizations_set = []
    ext_connections_set = {}
    # externalities
    for exchange in realized:

        ext_2 = {'ip': 0, 'in': 0, 'op': 0, 'on': 0, "own": 0}

        # update the list with the positions of the exchange.
        # model.ActorIssues[exchange.i.supply][exchange.i.actor.Name].position = exchange.i.y
        # model.ActorIssues[exchange.j.supply][exchange.j.actor.Name].position = exchange.j.y

        # by confention
        p = exchange.i.demand
        q = exchange.i.supply

        nbs_q = calculations.calc_adjusted_nbs(model.ActorIssues[q], exchange.updates[q], exchange.i.actor,
                                               exchange.i.y,
                                               model.nbs_denominators[q])

        nbs_p = calculations.calc_adjusted_nbs(model.ActorIssues[p], exchange.updates[p], exchange.j.actor,
                                               exchange.j.y,
                                               model.nbs_denominators[p])

        issue_set_key = "{0}-{1}".format(exchange.p, exchange.q)

        if issue_set_key not in model.groups:
            issue_set_key = "{0}-{1}".format(exchange.q, exchange.p)

        actor = exchange.i.actor  # inner
        nbs_p0 = model.nbs[p]
        nbs_p1 = nbs_p

        nbs_q0 = model.nbs[q]
        nbs_q1 = nbs_q

        xp = model.ActorIssues[p][actor.Name].position
        sp = model.ActorIssues[p][actor.Name].salience

        xq = model.ActorIssues[q][actor.Name].position
        sq = model.ActorIssues[q][actor.Name].salience

        euk = (abs(nbs_p0 - xp) - abs(nbs_p1 - xp)) * sp + (abs(nbs_q0 - xq) - abs(nbs_q1 - xq)) * sq
        euk *= 1
        # else:
        #         #outer
        #         pass
        # for actor in model.groups[issue_set_key]['b']:
        # for actor in model.groups[issue_set_key]['c']:
        # for actor in model.groups[issue_set_key]['d']:

        # for key, actor_issue in model.ActorIssues[p].items():
        #
        #     externality = calculations.externalities(model.nbs[p], nbs_p, exchange)
        #
        #     if key not in ext:  # todo fix different
        #         ext[key] = {'ip': 0, 'in': 0, 'op': 0, 'on': 0, "own": 0}
        #
        #     ext[key][externality["type"]] += externality["value"]
        #     ext_2[externality["type"]] += externality["value"]
        #
        # # end for
        #
        # for key, actor_issue in model.ActorIssues[q].items():
        #
        #     externality = calculations.externalities(actor_issue, model.nbs[q], nbs_q, exchange)
        #
        #     if key not in ext:  # todo fix different
        #         ext[key] = {'ip': 0, 'in': 0, 'op': 0, 'on': 0, "own": 0}
        #
        #     ext[key][externality["type"]] += externality["value"]
        #     ext_2[externality["type"]] += externality["value"]
        #
        # # end for
        #
        #
        # if issue_set_key in ext_connections_set:
        #     for key, value in ext_2.items():
        #         ext_connections_set[issue_set_key][key] += value
        # else:
        #     ext_connections_set[issue_set_key] = ext_2
        #     ext_connections_set[issue_set_key]["first"] = exchange.p
        #     ext_connections_set[issue_set_key]["second"] = exchange.q
        #
        # ext_realizations_set.append(
        #     [exchange.i.actor.Name, exchange.i.supply, exchange.j.actor.Name, exchange.j.supply,
        #      ext_2["ip"], ext_2["in"], ext_2["op"], ext_2["on"], ext_2["own"]])

# externalities.append(ext)
# ext_realizations.append(ext_realizations_set)
# ext_connections.append(ext_connections_set)

for exchange in realized:
    model.ActorIssues[exchange.i.supply][exchange.i.actor.Name].position = exchange.i.new_start_position()
    model.ActorIssues[exchange.j.supply][exchange.j.actor.Name].position = exchange.j.new_start_position()

import csvWriter

writer = csvWriter.csvWriter()
writer.write("output/{0}.{1}".format(i_round, "output.csv"), realized)

for issue in model.ActorIssues:
    for key, actor_issue in model.ActorIssues[issue].items():
        history[issue][key].append(actor_issue.position)

    history[issue]["nbs"].append(model.nbs[issue])

import collections

for i in range(len(externalities)):
    with open("output/{0}.{1}.{2}".format("externalities", i, "csv"), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')

        # headings
        writer.writerow(["Actor", "Inner Positive", "Inner Negative", "Outer Positive", "Outer Negative", "Own"])

        od_e = collections.OrderedDict(sorted(externalities[i].items()))
        for key, value in od_e.items():
            writer.writerow([key, value["ip"], value["in"], value["op"], value["on"], value["own"]])

        writer.writerow([])
        writer.writerow(["Connections"])
        writer.writerow(
            ["first", "second", "inner pos", "inner neg", "outer pos", "outer neg", "own", "ally pos", "ally neg"])

        for key, value in ext_connections[i].items():
            writer.writerow(
                [value["first"], value["second"], value["ip"], value["in"], value["op"], value["on"], value["own"]])

        writer.writerow([])
        writer.writerow(["Realizations"])
        writer.writerow(
            ["first", "supply", "second", "supply ", "inner pos", "inner neg", "outer pos", "outer neg", "own",
             "ally pos", "ally neg"])
        for realizations_row in ext_realizations[i]:
            writer.writerow(realizations_row)

for issue in history:

    with open("output/{0}.{1}.{2}".format("output", issue, "csv"), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')

        writer.writerow(["Actor I", "Supply I", "Actor J", "Supply J"])

        for key, value in history[issue].items():
            writer.writerow([key] + value)

print("Finished")
print(datetime.now() - startTime)
