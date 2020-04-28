import logging
import os
import statistics
import sys
import time
import xml.etree.cElementTree as ET

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from decide import log_filename
from decide.cli import init_output_directory
from decide.data.modelfactory import ModelFactory
from decide.data.reader import InputDataFile
from decide.model.base import AbstractModel
from decide.model.equalgain import EqualGainModel
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.logger import Logger
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver
from decide.model.utils import ModelLoop
from decide.qt import utils
from decide.qt.mainwindow.settings import ProgramSettings
from decide.qt.mainwindow.settings import SettingsFormWidget
from decide.qt.mainwindow.widgets import ActorWidget, IssueWidget, SummaryWidget, ActorIssueWidget, MenuBar
from decide.qt.utils import show_user_error


class Worker(QtCore.QObject):
    """
    Worker to execute the model in a thread so the window does not freeze
    """
    finished = QtCore.pyqtSignal(str)
    update = QtCore.pyqtSignal(int, int, int, float)

    def __init__(self, settings: ProgramSettings):
        super(Worker, self).__init__()

        self.settings = settings
        self.break_loop = False

    @QtCore.pyqtSlot()
    def run_model(self):
        settings = self.settings

        factory = ModelFactory(
            date_file=InputDataFile.open(settings.input_filename),
            actor_whitelist=settings.selected_actors,
            issue_whitelist=settings.selected_issues,
        )

        parent_output_directory = init_output_directory(
            settings.output_directory,
            settings.data_set_name,
        )

        model = factory(model_klass=EqualGainModel, randomized_value=settings.model_variations[0])

        event_handler = init_event_handlers(model, parent_output_directory, settings)

        event_handler.before_model()

        model_variations = list(settings.model_variations)

        for variation, p in enumerate(model_variations, 1):

            output_directory = init_output_directory(
                parent_output_directory,
                p
            )

            event_handler.update_output_directory(output_directory)

            event_handler.before_repetitions(
                repetitions=settings.repetitions,
                iterations=settings.iterations,
                randomized_value=p,
            )

            start_time = time.time()

            for repetition in range(settings.repetitions):

                model = factory(model_klass=EqualGainModel, randomized_value=p)

                event_handler.update_model_ref(model)

                model_loop = ModelLoop(model, event_handler, repetition)

                event_handler.before_iterations(repetition)

                for iteration_number in range(settings.iterations):

                    if self.break_loop:
                        break

                    self.update.emit(variation, repetition, iteration_number, start_time)

                    model_loop.loop()

                event_handler.after_iterations(repetition)

                if self.break_loop:
                    break

            if not self.break_loop:
                event_handler.after_repetitions()

                logging.info('tie count is {}'.format(model.tie_count))

        if not self.break_loop:
            event_handler.update_output_directory(parent_output_directory)
            event_handler.after_model()
            print(len(AbstractModel.eui))
            print(statistics.variance(AbstractModel.eui))
        self.finished.emit(parent_output_directory)

    def stop(self):
        self.break_loop = True


class ProgramData(QtCore.QObject):
    """
    Central object for the data used for displaying
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

    Logger(event_handler)

    SQLiteObserver(event_handler, settings.output_directory)
    Externalities(event_handler, summary_only=True)
    ExchangesWriter(event_handler, summary_only=True)
    IssueDevelopment(event_handler, write_voting_position=True, summary_only=True)

    return event_handler


class DecideMainWindow(QtWidgets.QMainWindow):
    """
    The first thing you see
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data = ProgramData()
        self.settings = ProgramSettings()
        self.settings.load()
        self.menu_bar = MenuBar(self, self)
        self.start = QtWidgets.QPushButton("Start")

        self.issue_widget = IssueWidget(self)
        self.actor_widget = ActorWidget(self)
        self.scroll_area_widget = QtWidgets.QWidget()
        self.actor_issue_widget = ActorIssueWidget(self.scroll_area_widget)
        self.scroll_area_widget.setLayout(self.actor_issue_widget)
        self.settings_widget = SettingsFormWidget(self.settings, self)

        self.progress_dialog = None

        self.thread = QtCore.QThread()
        self.worker = None

        self.overview_widget = SummaryWidget(
            self, self.settings, self.data, self.actor_widget, self.issue_widget
        )

        self.init_ui()

        self.load_settings()

        self.init_ui_data(self.settings.input_filename)

    def init_ui(self):
        self.statusBar().showMessage("Ready")

        self.setMenuBar(self.menu_bar)

        self.menu_bar.setNativeMenuBar(False)

        main = QtWidgets.QHBoxLayout()

        self.start.clicked.connect(self.run)
        self.set_start_button_state()

        left = QtWidgets.QVBoxLayout()

        left_top = QtWidgets.QHBoxLayout()

        actor_box = QtWidgets.QGroupBox("Actors")
        actor_box.setLayout(self.actor_widget)

        issue_box = QtWidgets.QGroupBox("Issues")
        issue_box.setLayout(self.issue_widget)

        # for the ActorIssueBox
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        scroll_area.setWidget(self.scroll_area_widget)

        scroll_area_layout = QtWidgets.QHBoxLayout()
        scroll_area_layout.addWidget(scroll_area)
        # the grid layout = self.actor_issue_widget

        actor_issue_box = QtWidgets.QGroupBox("Actor Issues")
        actor_issue_box.setLayout(scroll_area_layout)

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
        right.setAlignment(QtCore.Qt.AlignTop)

        main.addLayout(left, 1)
        main.addLayout(right, 1)

        q = QtWidgets.QWidget()
        q.setLayout(main)

        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle("Decide Exchange Model")
        self.show()

    def show_debug_dialog(self):
        utils.open_file_natively(log_filename)

    def show_error_report_dialog(self):

        from decide.qt.mainwindow.errordialog import ErrorDialog
        ex = ErrorDialog("Error message", self)

    def update_data_widgets(self):

        self.issue_widget.set_issues(list(self.data.issues.values()))
        self.actor_widget.set_actors(list(self.data.actors.values()))

        self.actor_issue_widget.set_actor_issues(list(self.data.actor_issues.values()))

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
            self.load_input_data(file_name)

    def load_input_data(self, file_name):

        self.statusBar().showMessage("Input file set to {} ".format(file_name))

        self.init_ui_data(file_name)

        self.overview_widget.update_widget()

    def open_current_input_window_with_current_data(self):

        from decide.qt.inputwindow.gui import InputWindow, register_app

        ex = InputWindow(self)
        ex.load(self.settings.input_filename)

        register_app(ex)

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

    def open_data_view(self):

        from decide.qt.inputwindow.gui import InputWindow, register_app

        ex = InputWindow(self)

        register_app(ex)

    def init_ui_data(self, file_name):

        if file_name:
            if not os.path.isfile(file_name):
                show_user_error(self, "Selected file does not exists")
            else:
                data_file = InputDataFile.open(file_name)

                if data_file.is_valid:

                    self.data.actors = data_file.actors
                    self.data.issues = data_file.issues
                    self.data.actor_issues = data_file.actor_issues
                    self.update_data_widgets()

                    # update the settings
                    self.settings.set_input_filename(file_name)
                    self.settings.save()
                else:

                    error_list = "\n".join([f"line: {line_no}, {message}" for line_no, message in data_file.errors.items()])

                    show_user_error(
                        self,
                        f"Your input file contains errors. The red rows are not valid. Hover with your mouse over the row for more information.\n{error_list}",
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

    def update_progress(self, variation, repetition, iteration, start_time):

        value = variation * repetition * self.settings.iterations + iteration

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

    def finished(self, output_directory):

        self._clean_progress_dialog()

        if not self.worker.break_loop:
            button_reply = QtWidgets.QMessageBox.question(
                self,
                "Done",
                "Done running the calculations. Open the result directory?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )

            if button_reply == QtWidgets.QMessageBox.Yes:
                utils.open_file_natively(output_directory)

    def _clean_progress_dialog(self):
        self.progress_dialog.setValue(
            self.settings.iterations * self.settings.repetitions * len(self.settings.model_variations)
        )
        self.progress_dialog.hide()

    def run(self):
        # store the current state of the app
        self.save_settings()

        self.setWindowTitle("Decide Exchange Model")

        self.show_progress_dialog()

        self.run_safe()

    def show_progress_dialog(self):

        self.progress_dialog = QtWidgets.QProgressDialog(
            "Task in progress",
            "Cancel",
            0,
            self.settings.repetitions * self.settings.iterations * len(self.settings.model_variations),
            self,
        )

        self.progress_dialog.setWindowTitle('Progress')

        bar = QtWidgets.QProgressBar(self.progress_dialog)
        bar.setTextVisible(True)
        bar.setFormat("%v/%m (%p%)")
        bar.setMinimum(0)
        bar.setMaximum(self.settings.iterations * self.settings.repetitions * len(self.settings.model_variations))
        self.progress_dialog.setBar(bar)

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
        filemode="a",
        level=logging.INFO,
        format=" %(asctime)s - %(levelname)s - %(message)s",
    )

    qtapp = QtWidgets.QApplication(sys.argv)
    qtapp.setQuitOnLastWindowClosed(True)

    app = DecideMainWindow()

    sys.excepthook = utils.exception_hook

    sys.exit(qtapp.exec_())


if __name__ == "__main__":
    main()
