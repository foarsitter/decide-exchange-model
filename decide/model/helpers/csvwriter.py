import csv


class CsvWriter:
    """
    Helper functions to write an exchange to a .csv file
    """

    @staticmethod
    def write(filename, realized):
        """
        Write all realized exchanges to the given file
        """

        if len(realized) <= 0:
            return

        with open(filename, "w") as csvfile:
            writer = csv.writer(csvfile, delimiter=";", lineterminator="\n")

            # write heading
            writer.writerow(realized[0].csv_row(head=True))

            for exchange in realized:
                if exchange.is_valid:
                    writer.writerow(exchange.csv_row())
