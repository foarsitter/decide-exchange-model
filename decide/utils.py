import csv
from decimal import Decimal
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes


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

    n_series = 16
    line_styles = ["-", "--", ":", "-."]
    marker_styles = ["o", "s", "^", "x", "d", "p", "*"]
    colors = plt.cm.gray(np.linspace(0.2, 0.8, n_series))  # Grayscale colors

    fig, axes = plt.subplots(2, 2, figsize=(11, 11))  # 2 rows, 2 columns

    layers = {0: [0, 0], 1: [0, 1], 2: [1, 0], 3: [1, 1]}

    unique_labels = ["MDS"]

    for index, file in enumerate(csv_path.glob("*.csv")):
        with file.open() as csv_file:
            reader = csv.reader(csv_file, delimiter=";", quotechar="'")

            plot_name = next(reader)[0]

            subplot: Axes = axes[layers[index][0], layers[index][1]]
            subplot.set_ylim(0, 100)
            subplot.set_xlim(0, 9)

            chart_area = get_chart_area_from_csv(
                "AVG Preference development NBS and all actors", reader
            )

            nbs = append_nbs(chart_area)

            subplot.plot(nbs, linestyle="-", label="MDS", color="black")

            subplot.set_title(plot_name)

            for lindex, row in enumerate(chart_area):
                label = row[0]

                if label not in unique_labels:
                    unique_labels.append(label)

                subplot.plot(
                    [float(x) for x in row[3:]],
                    label=label,
                    color=colors[lindex],
                    linestyle=line_styles[
                        lindex % len(line_styles)
                    ],  # Cycle through line styles
                    marker=marker_styles[
                        lindex % len(marker_styles)
                    ],  # Cycle through markers
                )

            x = chart_path / file.name

    fig.legend(
        unique_labels,
        loc="lower center",
        ncol=6,  # Stacked vertically
        bbox_to_anchor=(0.5, 0.005),
        # ncol=1,
        # bbox_to_anchor=(0.5, -0.05),
        fontsize="large",
    )
    plt.savefig(
        str(x).replace(".csv", "grouped.png"),
        # bbox_extra_artists=(lgd,),
        bbox_inches="tight",
        dpi=300,
    )
    plt.tight_layout(rect=[0, 0.1, 1, 1])
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
    # for p in ["0.00", "0.20", "0.40", "0.60", "0.80", "1.00"]:
    for p in ["0.00"]:
        graph_builder(
            # f"/home/jelmert/Downloads/kopenhagen/kopenhagen/{p}/issues/summary",
            f"/home/jelmert/Downloads/Alternative power files artikel/Alternative power files artikel/CoP21_2Oct2015_A_only allfin alt power/{p}/issues/summary",
            p,
        )
