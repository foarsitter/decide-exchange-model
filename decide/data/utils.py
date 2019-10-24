import csv
from typing import List

from decide.model.base import AbstractExchange


def write_exchanges(
        filename: str, realized: List[AbstractExchange], delimiter=";", lineterminator="\n"
):
    """
    Write all realized exchanges to the given file
    """

    if len(realized) <= 0:
        return

    with open(filename, "w") as csv_file:
        writer = csv.writer(
            csv_file, delimiter=delimiter, lineterminator=lineterminator
        )

        # write heading
        writer.writerow(realized[0].csv_row(head=True))

        for exchange in realized:
            if exchange.is_valid:
                writer.writerow(exchange.csv_row())
