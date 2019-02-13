import logging
import sys

from PyQt5 import QtWidgets

from decide import log_filename
from decide.model.helpers.helpers import exception_hook
from decide.qt.mainwindow import ProgramSettings


class ErrorDialog(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(ErrorDialog, self).__init__(*args, **kwargs)

        self.settings = ProgramSettings()
        self.settings.load()

        self.main = QtWidgets.QVBoxLayout()

        self.error_message = self.add_message_box()

        self.add_label('Attachments:')
        self.add_settings()
        self.add_input_file()
        self.add_send_button()

        self.init_window()

    def init_window(self):

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.main)
        self.setCentralWidget(central_widget)

        self.setGeometry(300, 300, 400, 400)
        self.setWindowTitle("Error reporting tool")
        self.show()

    def add_widget(self, widget):
        self.main.addWidget(widget)

    def add_label(self, text):
        self.add_widget(QtWidgets.QLabel(text))

    def add_message_box(self):

        self.add_widget(QtWidgets.QLabel('What happend?'))

        textarea = QtWidgets.QPlainTextEdit()

        self.add_widget(textarea)

        return textarea

    def add_input_file(self):
        self.add_label('Data:' + self.settings.input_filename)

    def add_settings(self):

        self.add_label('Settings:' + self.settings.settings_file)

    def add_send_button(self):

        button = QtWidgets.QPushButton()
        button.setText('Send error report')

        self.add_widget(button)

        return button

    def send_error_report(self):
        pass


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

    error_dialog = ErrorDialog()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
