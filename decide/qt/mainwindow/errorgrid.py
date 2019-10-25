import logging
import os
import sys
from typing import List

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from decide import log_filename, input_folder
from decide.data.reader import InputDataFile
from decide.qt.utils import exception_hook


class ErrorGrid(QDialog):
    """
    Visualisation of the input file in a dialog to inform the user of the errors a input file has
    """
    def __init__(self, data_file: InputDataFile, *args, **kwargs):
        super(ErrorGrid, self).__init__(*args, **kwargs)

        self.data_file = data_file
        self.row_pointer = 0

        self.main = QtWidgets.QGridLayout()

        self.init_window()

    def init_window(self):

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.main)

        layout = QtWidgets.QHBoxLayout(self)
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area_widget_contents = QtWidgets.QWidget()
        self.main = QtWidgets.QGridLayout(scroll_area_widget_contents)
        scroll_area.setWidget(scroll_area_widget_contents)
        layout.addWidget(scroll_area)

        self.setLayout(layout)
        self.showMaximized()
        # self.setGeometry(300, 300, 400, 400)
        self.setWindowTitle("Error reporting tool")

        self.init_grid()

        self.show()

    def init_grid(self):

        for row, columns in self.data_file.rows.items():
            self.add_row(row, columns)

    def add_row(self, row, columns: List[str]):
        for column, content in enumerate(columns):

            label = QtWidgets.QLabel(str(content))

            if row in self.data_file.errors:
                label.setStyleSheet("color: red")
                error = self.data_file.errors[row]
                label.setToolTip(str(error))

            self.main.addWidget(label, row, column)


def main():

    logging.basicConfig(
        filename=log_filename,
        filemode="w",
        level=logging.DEBUG,
        format=" %(asctime)s - %(levelname)s - %(message)s",
    )

    sys.excepthook = exception_hook

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    data_file = InputDataFile.open(
        os.path.join(input_folder, "kopenhagen_with_errors.csv")
    )

    error_dialog = ErrorGrid(data_file)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
