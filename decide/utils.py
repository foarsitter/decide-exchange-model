import csv
from decimal import Decimal
from pathlib import Path

import matplotlib.pyplot as plt


def append_nbs(data):

    saliences = {}
    powers = {}
    positions = {}
    actors = []

    denominator = Decimal(0)
    power_salience_positions = [Decimal(0) for _ in range(10)]

    for actor, salience, power, *_ in data:

        salience = Decimal(salience)
        power = Decimal(power)

        saliences[actor] = salience
        powers[actor] = power
        positions[actor] = _
        actors.append(actor)

        power_salience = power * salience

        denominator += power_salience

        for index, position in enumerate(_):
            power_salience_positions[index] += power_salience * Decimal(position)

    return [x / denominator for x in power_salience_positions]


def graph_builder(file_path: str, p: str):
    path = Path(file_path)

    csv_path = path / "csv"
    chart_path = path / "charts" / "modified"

    # chart_path_2 = Path("/home/jelmert/Downloads/kopenhagen (1)/kopenhagen/modified")

    if not chart_path.exists():
        chart_path.mkdir()

    for file in csv_path.glob("*.csv"):
        with file.open() as csv_file:
            reader = csv.reader(csv_file, delimiter=";", quotechar="'")

            plot_name = next(reader)[0] + f" p={p}"

            chart_area = get_chart_area_from_csv(
                "AVG Preference development MDS and all actors", reader
            )

            nbs = append_nbs(chart_area)

            plt.plot(nbs, linestyle="--", label="MDS")

            plt.title(plot_name)

            for row in chart_area:
                plt.plot([float(x) for x in row[3:]], label=row[0])

            x = chart_path / file.name
            lgd = plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
            plt.savefig(
                str(x).replace(".csv", ".png"),
                bbox_extra_artists=(lgd,),
                bbox_inches="tight",
            )
            plt.show()
            plt.clf()


def get_chart_area_from_csv(begin: str, reader: csv.reader):
    data = []

    found_begin = False

    for index, row in enumerate(reader):

        if len(row) > 0 and row[0] == begin:
            found_begin = index

        if found_begin:
            if len(row) == 0 or row[0] == "":
                return data

            if len(row) > 0 and index - found_begin > 1:
                data.append(row)

    return data


if __name__ == "__main__":

    for p in ["0.00", "0.20", "0.40", "0.60", "0.80", "1.00"]:
        graph_builder(
            # ~Alternative power files artikel/Alternative power files artikel/CoP21_2Oct2015_A_no_allfin_amb alt power/CoP21_2Oct2015_A_no_allfin_amb alt power/1.00/issues/summary
            f"/home/jelmert/Downloads/Alternative power files artikel/Alternative power files artikel/CoP21_2Oct2015_A_no_allfin_amb alt power/CoP21_2Oct2015_A_no_allfin_amb alt power/{p}/issues/summary",
            p
        )
