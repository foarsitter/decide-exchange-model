import csv

from csvParser import Parser

csvParser = Parser()
model = csvParser.read("data/CoP21.csv")

model.calc_nbs()
model.determine_positions()
model.calc_combinations()
model.determine_groups()

realized = []

while len(model.Exchanges) > 0:
    realize = model.highest_gain()
    model.update_exchanges(realize)
    realized.append(realize)

print(len(realized))

with open('data/CoP21.compare.csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    compare = list(reader)

valid = 0

invalidRows = []

i = 1
fails = []
for exchange in realized:

    found_exchange = False

    for cRow in compare:

        if abs(exchange.gain - float(cRow[4])) < 1e-5:
            found_exchange = True
            break

    if not found_exchange:
        fails.append(i)

    i += 1

print(len(fails))
print(len(fails) / len(realized))
print(fails)
