import logging
import sys

import requests
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtWidgets import QDialog
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtWidgets import QPushButton

from decide import log_filename
from decide.qt.mainwindow.settings import ProgramSettings
from decide.qt.utils import exception_hook


class ErrorDialog(QDialog):
    """Dialog to send error information to me."""

    def __init__(self, message: str = "", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.settings = ProgramSettings()
        self.settings.load()

        self.main = QtWidgets.QVBoxLayout()

        self.error_message = self.add_message_box(message)

        self.add_label("Attachments:")
        self.settings_checkbox = self.add_settings()
        self.input_file_checkbox = self.add_input_file()
        self.add_send_button()

        self.init_window()

    def init_window(self) -> None:
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(self.main)
        self.setLayout(self.main)

        self.setGeometry(300, 300, 400, 400)
        self.setWindowTitle("Error reporting tool")
        self.show()

    def add_widget(self, widget: QCheckBox | QLabel | QPlainTextEdit | QPushButton) -> None:
        self.main.addWidget(widget)

    def add_label(self, text: str) -> None:
        self.add_widget(QtWidgets.QLabel(text))

    def add_message_box(self, message) -> QPlainTextEdit:
        self.add_widget(QtWidgets.QLabel("What happened?"))

        textarea = QtWidgets.QPlainTextEdit()
        textarea.setPlainText(message)

        self.add_widget(textarea)

        return textarea

    def add_input_file(self) -> QCheckBox:
        checkbox = QtWidgets.QCheckBox(self.settings.input_filename)
        checkbox.setChecked(True)
        self.add_widget(checkbox)

        return checkbox

    def add_settings(self) -> QCheckBox:
        checkbox = QtWidgets.QCheckBox(str(self.settings.settings_file))
        checkbox.setChecked(True)
        self.add_widget(checkbox)

        return checkbox

    def add_send_button(self) -> QPushButton:
        button = QtWidgets.QPushButton()
        button.setText("Send error report")
        button.clicked.connect(self.send_error_report)
        self.add_widget(button)

        return button

    def send_error_report(self) -> None:
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Confirm sending",
            "Are you sure you want to send the message with the attachments?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        settings = None
        input_data = None

        if confirm == QMessageBox.StandardButton.Yes:
            files = {}

            if self.settings_checkbox.isChecked():
                settings = open(self.settings.settings_file_path())
                files["settings"] = settings
            if self.input_file_checkbox.isChecked():
                input_data = open(self.settings.input_filename)
                files["input_data"] = input_data

            response = requests.post(
                url="https://jelmertmail.nl/decide/",
                data={"message": self.error_message.toPlainText()},
                files=files,
            )

            QtWidgets.QMessageBox.about(self, "Server response", str(response.content))

            if settings:
                settings.close()

            if input_data:
                input_data.close()


def main() -> None:
    logging.basicConfig(
        filename=log_filename,
        filemode="w",
        level=logging.DEBUG,
        format=" %(asctime)s - %(levelname)s - %(message)s",
    )

    sys.excepthook = exception_hook

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    ErrorDialog("empty message")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
