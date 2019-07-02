import logging
import os
import sys
import time
import xml.etree.cElementTree as ET

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from decide import log_filename
from decide.data.reader import InputDataFile
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver
from decide.qt import utils
from decide.qt.mainwindow.settings import ProgramSettings, SettingsFormWidget
from decide.qt.mainwindow.widgets import ActorWidget, IssueWidget, SummaryWidget, ActorIssueWidget, MenuBar
from decide.qt.mainwindow.worker import Worker
from decide.qt.utils import show_user_error


class ProgramData(QtCore.QObject):
    """
    The data used for displaying
    """

    changed = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.issues = {}
        self.actors = {}
        self.actor_issues = {}


def init_event_handlers(model, output_directory, settings):
    """
    :type model: decide.model.base.AbstractModel
    :type output_directory: str
    :type settings: ProgramSettings
    """

    event_handler = Observable(model_ref=model, output_directory=output_directory)

    if settings.output_sqlite:
        SQLiteObserver(event_handler, settings.output_directory)

    if settings.externalities_csv:
        Externalities(event_handler, settings)

    if settings.exchanges_csv:
        ExchangesWriter(event_handler, settings.summary_only)

    if settings.issue_development_csv:
        IssueDevelopment(event_handler, summary_only=settings.summary_only)

    return event_handler


class DecideMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data = ProgramData()  # TODO: rewrite to InputDataFile
        self.settings = ProgramSettings()
        self.menu_bar = None
        self.start = QtWidgets.QPushButton("Start")

        self.issue_widget = IssueWidget(self)
        self.actor_widget = ActorWidget(self)
        self.actor_issue_widget = ActorIssueWidget(self)
        self.settings_widget = SettingsFormWidget(self.settings, self)

        self.progress_dialog = None

        self.thread = QtCore.QThread()
        self.worker = None

        self.overview_widget = SummaryWidget(
            self, self.settings, self.data, self.actor_widget, self.issue_widget
        )

        self.init_ui()

        self.load_settings()

        self.init_ui_data()

    def show_debug_dialog(self):
        utils.open_file_natively(log_filename)

    def show_error_report_dialog(self):

        from decide.qt.mainwindow.errordialog import ErrorDialog
        ex = ErrorDialog("Error message", self)

    def update_data_widgets(self):

        self.issue_widget.set_issues(list(self.data.issues.values()))
        self.actor_widget.set_actors(list(self.data.actors.values()))

        if len(self.issue_widget.objects) > 0:
            issue = self.issue_widget.objects[0]
            actor_issues = list(self.data.actor_issues[issue].values())
            self.actor_issue_widget.set_actor_issues(issue.name, actor_issues)

        self.overview_widget.update_widget()

    def update_actor_issue_widget(self):
        """
        Button event to update the ActorIssueWidget
        """
        issue = self.data.issues[self.sender().objectName()]
        actor_issues = list(self.data.actor_issues[issue].values())

        self.actor_issue_widget.set_actor_issues(issue, actor_issues)
        self.overview_widget.update_widget()

    def open_input_data(self):
        """
        Open the file, parse the data and update the layout
        """
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select input data")

        if file_name:
            self.statusBar().showMessage("Input file set to {} ".format(file_name))

            self.settings.input_filename = file_name

            self.init_ui_data()

        self.overview_widget.update_widget()

    def select_output_dir(self):
        """
        Output directory
        """
        self.settings.output_directory = str(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        )
        self.statusBar().showMessage(
            "Output directory set to: {} ".format(self.settings.output_directory)
        )

        self.overview_widget.update_widget()

    def set_start_button_state(self):
        if (
                self.settings.input_filename
                and self.settings.output_directory
                and not self.thread.isRunning()
        ):
            self.start.setEnabled(True)
            self.start.setDisabled(False)
        else:
            self.start.setEnabled(False)
            self.start.setDisabled(True)

    def init_ui(self):
        self.statusBar().showMessage("Ready")

        self.menu_bar = MenuBar(self, self)

        self.setMenuBar(self.menu_bar)

        self.menu_bar.setNativeMenuBar(False)

        main = QtWidgets.QHBoxLayout()

        self.start.clicked.connect(self.run)
        self.set_start_button_state()

        left = QtWidgets.QVBoxLayout()

        left_top = QtWidgets.QHBoxLayout()

        # left_top.setAlignment(QtCore.Qt.AlignTop)

        actor_box = QtWidgets.QGroupBox("Actors")
        issue_box = QtWidgets.QGroupBox("Issues")
        actor_issue_box = QtWidgets.QGroupBox("Actor Issues")

        actor_box.setLayout(self.actor_widget)
        issue_box.setLayout(self.issue_widget)
        actor_issue_box.setLayout(self.actor_issue_widget)

        left_top.addWidget(actor_box, 1)
        left_top.addWidget(issue_box, 1)

        left.addLayout(left_top, 1)
        left.addWidget(actor_issue_box, 1)

        settings_box = QtWidgets.QGroupBox("Model parameters")
        settings_box.setLayout(self.settings_widget)

        overview_box = QtWidgets.QGroupBox("Overview")
        overview_box.setLayout(self.overview_widget)
        self.overview_widget.setAlignment(QtCore.Qt.AlignTop)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(settings_box, 1)
        right.addWidget(overview_box, 1)
        right.addWidget(self.start, 1)

        main.addLayout(left, 1)
        main.addLayout(right, 1)

        q = QtWidgets.QWidget()
        q.setLayout(main)

        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle("Decide Exchange Model")
        self.show()

    def open_data_view(self):

        from decide.qt.inputwindow.gui import InputWindow, register_app

        ex = InputWindow(self)

        register_app(ex)

    def init_ui_data(self):

        if not os.path.isfile(self.settings.input_filename):
            show_user_error(self, "Selected file does not exists")
        else:

            data_file = InputDataFile.open(self.settings.input_filename)

            if data_file.is_valid:

                self.data.actors = data_file.actors
                self.data.issues = data_file.issues
                self.data.actor_issues = data_file.actor_issues
                self.update_data_widgets()
            else:
                show_user_error(
                    self,
                    "Your input file contains errors. The red rows are not valid. Hover with your move over the row for more information.",
                )
                from decide.qt.mainwindow.errorgrid import ErrorGrid

                ex = ErrorGrid(data_file, self)

    def run_safe(self):

        self.worker = Worker(self.settings)
        self.worker.finished.connect(self.finished)
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.update.connect(self.update_progress)
        self.thread.started.connect(self.worker.run_model)
        self.thread.start()

    def update_progress(self, repetition, iteration, start_time):

        value = repetition * self.settings.iterations + iteration

        self.progress_dialog.setValue(value)
        repetitions = self.settings.repetitions

        if repetition > 0 and repetitions > 100 and repetition % 20 == 0:
            time_expired = time.time() - start_time

            avg_time_per_repetition = time_expired / repetition

            estimated_time_needed_seconds = avg_time_per_repetition * repetitions

            estimated_time_left = estimated_time_needed_seconds - (
                    repetition * avg_time_per_repetition
            )

            self.statusBar().showMessage(
                "{:.0f} minutes remaining ".format(estimated_time_left / 60)
            )

    def finished(self, output_directory, tie_count):

        self._clean_progress_dialog()

        if not self.worker.break_loop:
            button_reply = QtWidgets.QMessageBox.question(
                self,
                "Done",
                "Done executing. Found {} ties. Open the result directory?".format(
                    tie_count
                ),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )

            if button_reply == QtWidgets.QMessageBox.Yes:
                if self.settings.summary_only and self.settings.issue_development_csv:
                    utils.open_file_natively(
                        os.path.join(output_directory, "issues", "summary")
                    )
                else:
                    utils.open_file_natively(output_directory)

    def _clean_progress_dialog(self):
        self.progress_dialog.setValue(
            self.settings.iterations * self.settings.repetitions
        )
        self.progress_dialog.hide()

    def run(self):
        # store the current state of the app
        self.save_settings()

        # create a whitelist for the selected actors

        selected_actors = self.actor_widget.get_selected()
        selected_actors.sort()

        actors_subset = "-".join(selected_actors)

        self.setWindowTitle("Decide Exchange Model {}".format(actors_subset))

        self.show_progress_dialog(actors_subset)

        self.run_safe()

    def show_progress_dialog(self, title):

        self.progress_dialog = QtWidgets.QProgressDialog(
            "Task in progress",
            "Cancel",
            0,
            self.settings.repetitions * self.settings.iterations,
            self,
        )

        bar = QtWidgets.QProgressBar(self.progress_dialog)
        bar.setTextVisible(True)
        bar.setFormat("%v/%m (%p%)")
        bar.setMinimum(0)
        bar.setMaximum(self.settings.iterations * self.settings.repetitions)
        self.progress_dialog.setBar(bar)
        # self.progress_dialog.setWindowTitle(title)

        self.progress_dialog.canceled.connect(self.cancel)

        self.progress_dialog.show()

    def load_settings(self):

        if os.path.isfile(self.settings.settings_file):
            try:
                self.settings.load()
                self.menu_bar.load()
                self.settings_widget.load()

            except ET.ParseError:
                logging.info("Invalid xml")

    def save_settings(self):
        self.settings_widget.save()
        self.issue_widget.save()
        self.actor_widget.save()
        self.menu_bar.save()
        self.settings.save()

    def cancel(self):
        self.worker.stop()


def main():
    logging.basicConfig(
        filename=log_filename,
        filemode="w",
        level=logging.DEBUG,
        format=" %(asctime)s - %(levelname)s - %(message)s",
    )

    sys.excepthook = utils.exception_hook
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    decide = DecideMainWindow()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
