import json
import logging
import sys
import time
import xml.etree.ElementTree as ET
from json import JSONDecodeError
from pathlib import Path

from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6.QtCore import QProcess

from decide import decide_base_path
from decide import log_filename
from decide.data.reader import InputDataFile
from decide.qt import utils
from decide.qt.mainwindow.helpers import esc
from decide.qt.mainwindow.helpers import normalize
from decide.qt.mainwindow.settings import ProgramSettings
from decide.qt.mainwindow.settings import SettingsFormWidget
from decide.qt.mainwindow.widgets import ActorIssueWidget
from decide.qt.mainwindow.widgets import ActorWidget
from decide.qt.mainwindow.widgets import IssueWidget
from decide.qt.mainwindow.widgets import MenuBar
from decide.qt.mainwindow.widgets import SummaryWidget
from decide.qt.utils import show_user_error


class ProgramData(QtCore.QObject):
    """Central object for the data used for displaying."""

    changed = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.issues = {}
        self.actors = {}
        self.actor_issues = {}


class DecideMainWindow(QtWidgets.QMainWindow):
    """The first thing you see."""

    def __init__(self, *args, **kwargs) -> None:
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

        self.process = QProcess()

        self.overview_widget = SummaryWidget(
            self,
            self.settings,
            self.data,
            self.actor_widget,
            self.issue_widget,
        )

        self.init_ui()

        self.load_settings()

        if self.settings.input_filename:
            path = Path(self.settings.input_filename)
            self.init_ui_data(path)
        self.start_time = time.time()

    def init_ui(self) -> None:
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
        self.overview_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(settings_box, 1)
        right.addWidget(overview_box, 1)
        right.addWidget(self.start, 1)
        right.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        main.addLayout(left, 1)
        main.addLayout(right, 1)

        q = QtWidgets.QWidget()
        q.setLayout(main)

        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle("Decide Exchange Model")
        self.show()

    def show_debug_dialog(self) -> None:
        utils.open_file_natively(log_filename)

    def show_error_report_dialog(self) -> None:
        from decide.qt.mainwindow.errordialog import ErrorDialog

        ErrorDialog("Error message", self)

    def update_data_widgets(self) -> None:
        self.issue_widget.set_issues(list(self.data.issues.values()))
        self.actor_widget.set_actors(list(self.data.actors.values()))

        self.actor_issue_widget.set_actor_issues(list(self.data.actor_issues.values()))

        self.overview_widget.update_widget()

    def update_actor_issue_widget(self) -> None:
        """Button event to update the ActorIssueWidget."""
        issue = self.data.issues[self.sender().objectName()]
        actor_issues = list(self.data.actor_issues[issue].values())

        self.actor_issue_widget.set_actor_issues(issue, actor_issues)
        self.overview_widget.update_widget()

    def open_input_data(self) -> None:
        """Open the file, parse the data and update the layout."""
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select input data")

        if filename:
            self.load_input_data(Path(filename))

    def load_input_data(self, filename: Path) -> None:
        self.statusBar().showMessage(f"Input file set to {filename.absolute().resolve()} ")
        self.init_ui_data(filename)
        self.overview_widget.update_widget()

    def open_current_input_window_with_current_data(self) -> None:
        from decide.qt.inputwindow.gui import InputWindow
        from decide.qt.inputwindow.gui import register_app

        if self.settings and self.settings.input_filename:
            ex = InputWindow(self)
            ex.load(self.settings.input_filename)

            register_app(ex)

    def select_output_dir(self) -> None:
        """Output directory."""
        self.settings.output_directory = Path(
            QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"),
        )
        self.statusBar().showMessage(
            f"Output directory set to: {self.settings.output_directory} ",
        )

        self.overview_widget.update_widget()

    def set_start_button_state(self) -> None:
        if (
            self.settings.input_filename
            and self.settings.output_directory
            and self.process.state() == QProcess.ProcessState.NotRunning
        ):
            self.start.setEnabled(True)
            self.start.setDisabled(False)
        else:
            self.start.setEnabled(False)
            self.start.setDisabled(True)

    def open_data_view(self) -> None:
        from decide.qt.inputwindow.gui import InputWindow
        from decide.qt.inputwindow.gui import register_app

        ex = InputWindow(self)

        register_app(ex)

    def init_ui_data(self, filename: Path) -> None:
        if filename:
            if not filename.is_file():
                show_user_error(self, "Selected file does not exists")
            else:
                data_file = InputDataFile.open(filename)

                if data_file.is_valid:
                    self.data.actors = data_file.actors
                    self.data.issues = data_file.issues
                    self.data.actor_issues = data_file.actor_issues
                    self.update_data_widgets()

                    # update the settings
                    self.settings.set_input_filename(filename)
                    self.settings.save()
                else:
                    error_list = "\n".join(
                        [
                            f"line: {line_no}, {message}"
                            for line_no, message in data_file.errors.items()
                        ],
                    )

                    show_user_error(
                        self,
                        f"Your input file contains errors. The red rows are not valid."
                        f" Hover with your mouse over the row for more information.\n{error_list}",
                    )
                    from decide.qt.mainwindow.errorgrid import ErrorGrid

                    ErrorGrid(data_file, self)

    def handle_stderr(self) -> None:
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.message(stderr)

    def message(self, s) -> None:
        print(s)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")

        try:
            data = json.loads(stdout)
            event = data.get("event")

            if event == "Progress":
                self.update_progress(
                    progress=data["progress"],
                )
        except JSONDecodeError:
            self.message(stdout)

    def handle_state(self, state):
        states = {
            QProcess.ProcessState.NotRunning: "Not running",
            QProcess.ProcessState.Starting: "Starting",
            QProcess.ProcessState.Running: "Running",
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def run_safe(self) -> None:
        path = self.settings.output_path()
        path.mkdir(parents=True, exist_ok=True)

        update_settings_with_ui_values(
            self.settings,
            path / "settings.csv",
        )
        self.process = QProcess()
        self.process.finished.connect(self.finished)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.stateChanged.connect(self.handle_state)
        self.start_time = time.time()
        self.process.start(
            "python",
            [
                str(x)
                for x in [
                    f"{decide_base_path}/cli.py",
                    "--input-file",
                    self.settings.input_filename,
                    "--repetitions",
                    self.settings.repetitions,
                    "--iterations",
                    self.settings.iterations,
                    "--start",
                    self.settings.start,
                    "--step",
                    self.settings.step,
                    "--stop",
                    self.settings.stop,
                    "--output-dir",
                    self.settings.output_directory,
                    "--name",
                    self.settings.run_name,
                ]
            ],
        )

    def update_progress(self, progress: int) -> None:
        self.progress_dialog.setValue(progress)

        if self.start_time:
            time_expired = time.time() - self.start_time

            avg_time_per_repetition = time_expired / progress

            estimated_time_needed_seconds = avg_time_per_repetition * self.settings.repetitions

            estimated_time_left = estimated_time_needed_seconds - (
                progress * avg_time_per_repetition
            )

            self.statusBar().showMessage(
                f"{estimated_time_left / 60:.0f} minutes remaining ",
            )

    def finished(self) -> None:
        self._clean_progress_dialog()

        button_reply = QtWidgets.QMessageBox.question(
            self,
            "Done",
            "Done running the calculations. Open the result directory?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )

        if button_reply == QtWidgets.QMessageBox.StandardButton.Yes:
            utils.open_file_natively(self.settings.output_directory)

    def _clean_progress_dialog(self) -> None:
        self.progress_dialog.setValue(
            self.settings.iterations
            * self.settings.repetitions
            * len(self.settings.model_variations()),
        )
        self.progress_dialog.hide()

    def run(self) -> None:
        self.save_settings()

        if self.settings.output_path().is_dir():
            button_reply = QtWidgets.QMessageBox.question(
                self,
                "Output directory already exists",
                f"The given directory {self.settings.output_directory} already exists. Proceed?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )

            if button_reply == QtWidgets.QMessageBox.StandardButton.No:
                return

        self.setWindowTitle("Decide Exchange Model")

        self.show_progress_dialog()

        self.run_safe()

    def show_progress_dialog(self) -> None:
        self.progress_dialog = QtWidgets.QProgressDialog(
            "Task in progress",
            "Cancel",
            0,
            self.settings.repetitions
            * self.settings.iterations
            * len(self.settings.model_variations()),
            self,
        )

        self.progress_dialog.setWindowTitle("Progress")

        bar = QtWidgets.QProgressBar(self.progress_dialog)
        bar.setTextVisible(True)
        bar.setFormat("%v/%m (%p%)")
        bar.setMinimum(0)
        bar.setMaximum(
            self.settings.iterations
            * self.settings.repetitions
            * len(self.settings.model_variations()),
        )
        self.progress_dialog.setBar(bar)

        self.progress_dialog.canceled.connect(self.cancel)

        self.progress_dialog.show()

    def load_settings(self) -> None:
        if self.settings.settings_file.is_file():
            try:
                self.settings.load()
                self.menu_bar.load()
                self.settings_widget.load()

            except ET.ParseError:
                logging.info("Invalid xml")

    def save_settings(self) -> None:
        self.settings_widget.save()
        self.issue_widget.save()
        self.actor_widget.save()
        self.menu_bar.save()
        self.settings.save()

    def cancel(self) -> None:
        self.process.kill()


def update_settings_with_ui_values(settings: ProgramSettings, filename: Path) -> None:
    items = ["salience_weight", "fixed_weight", "iterations", "repetitions"]

    with filename.open("w") as file:
        for item in items:
            value = settings.__dict__[item]

            if isinstance(value, list):
                value = settings.settings_list_separator.join(value)

            file.write("\t".join([esc(item), esc(value), "\n"]))


def main() -> None:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    qtapp = QtWidgets.QApplication([])
    qtapp.setQuitOnLastWindowClosed(True)

    DecideMainWindow()

    sys.excepthook = utils.exception_hook

    qtapp.exec()


if __name__ == "__main__":
    main()
