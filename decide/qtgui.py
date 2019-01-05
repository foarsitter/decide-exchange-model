import copy
import logging
import os
import sys
import time
import xml.etree.cElementTree as ET
from typing import List

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from decide import log_file, open_file, exception_hook
from decide.cli import init_model, init_output_directory, float_range
from decide.model import base
from decide.model.equalgain import EqualGainModel
from decide.model.helpers import csvparser, helpers
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver
from decide.qtinputwindow import InputWindow

logging.basicConfig(
    filename=log_file,
    filemode="w",
    level=logging.DEBUG,
    format=" %(asctime)s - %(levelname)s - %(message)s",
)


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


class ProgramSettings(QtCore.QObject):
    """
    The settings for the model parameters
    """

    changed = QtCore.pyqtSignal()

    settings_file = "decide-settings.xml"

    def __init__(self, *args, **kwargs):
        super(ProgramSettings, self).__init__(*args, **kwargs)

        self.input_filename = ""
        self.output_directory = ""

        self.salience_weight = 0.4
        self.fixed_weight = 0.1

        self.randomized_value = 0.00
        self.start = 0.00
        self.step = 0.05
        self.stop = 0.50

        self.repetitions = 10
        self.iterations = 10

        self.settings_type = "xml"
        self.settings_list_separator = ";"

        self.version = 1

        self.output_sqlite = False
        self.issue_development_csv = True
        self.externalities_csv = False
        self.exchanges_csv = False
        self.voting_positions = False
        self.summary_only = True

        self.selected_actors = []
        self.selected_issues = []

    def save(self):
        if self.settings_type == "xml":
            self._save_xml()

    def _save_xml(self):

        element = ET.Element("decide-settings")

        for key, value in self.__dict__.items():
            if not key.startswith("_") and hasattr(self, key):

                if isinstance(value, list):
                    value = self.settings_list_separator.join(value)

                child = ET.Element(key)
                child.text = str(value)
                element.append(child)

        ET.ElementTree(element).write(self.settings_file)

    def load(self):
        if self.settings_type == "xml":
            self._load_xml()

    def _load_xml(self):
        for elm in ET.parse(self.settings_file).getroot():

            if hasattr(self, elm.tag):

                attr = getattr(self, elm.tag)

                if isinstance(attr, bool):
                    setattr(self, elm.tag, elm.text == "True")
                elif isinstance(attr, int):
                    setattr(self, elm.tag, int(elm.text))
                elif isinstance(attr, float):
                    setattr(self, elm.tag, float(elm.text))
                elif isinstance(attr, list):
                    setattr(
                        self, elm.tag, str(elm.text).split(self.settings_list_separator)
                    )
                else:
                    setattr(self, elm.tag, str(elm.text))


class DynamicFormLayout(QtWidgets.QGridLayout):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.checkboxes = []
        self.objects = []
        self.row_pointer = 0

    def clear(self):
        """
        Set the parent of all child widgets to None so they will be deleted
        """
        for i in reversed(range(self.count())):
            self.itemAt(i).widget().setParent(None)

    def add_row(self, *widgets):

        for index, widget in enumerate(widgets):
            self.addWidget(widget, self.row_pointer, index)

        self.row_pointer += 1

    def set_values(self, objects):
        self.objects = objects
        self.objects.sort()
        self.clear()

    def get_selected(self):

        selected = []

        for checkbox in self.checkboxes:  # type: QtWidgets.QCheckBox
            if checkbox.isChecked():
                selected.append(checkbox.objectName())

        return selected


class IssueWidget(DynamicFormLayout):
    """
    Form layout for customizing the Issue selection
    """

    def set_issues(self, issues: List[base.Issue]):
        self.set_values(issues)

        for issue in issues:
            checkbox = QtWidgets.QCheckBox(issue.name)

            lower = QtWidgets.QLabel(str(round(issue.lower, 3)))
            upper = QtWidgets.QLabel(str(round(issue.upper, 3)))

            checkbox.setObjectName(issue.issue_id)
            checkbox.stateChanged.connect(self.state_changed)

            if (
                issue in self.main_window.settings.selected_issues
                or len(self.main_window.settings.selected_issues) == 0
            ):
                checkbox.setChecked(True)

            info = QtWidgets.QPushButton("values")
            info.setObjectName(issue.issue_id)
            info.clicked.connect(self.main_window.update_actor_issue_widget)

            self.checkboxes.append(checkbox)
            self.add_row(checkbox, lower, upper, info)

    def state_changed(self):
        self.main_window.overview_widget.update_widget()

    def save(self):
        self.main_window.settings.selected_issues = self.get_selected()


class ActorWidget(DynamicFormLayout):
    """
    Form layout for customizing the Actor selection
    """

    def set_actors(self, actors: List[base.Actor]):
        self.set_values(actors)

        for actor in actors:
            checkbox = QtWidgets.QCheckBox(str(actor))
            checkbox.setObjectName(actor.actor_id)

            if (
                actor in self.main_window.settings.selected_actors
                or len(self.main_window.settings.selected_actors) == 0
            ):
                checkbox.setChecked(True)

            checkbox.stateChanged.connect(self.state_changed)

            self.checkboxes.append(checkbox)
            self.add_row(checkbox)

    def state_changed(self):
        self.main_window.overview_widget.update_widget()

    def save(self):
        self.main_window.settings.selected_actors = self.get_selected()


class ActorIssueWidget(DynamicFormLayout):
    def set_actor_issues(self, issue: base.Issue, actor_issues=List[base.ActorIssue]):
        self.set_values(actor_issues)

        self.add_row(QtWidgets.QLabel(str(issue)))

        heading = ["Actor", "Position", "Salience", "Power"]

        self.add_row(*[QtWidgets.QLabel(x) for x in heading])

        for actor_issue in actor_issues:
            actor = QtWidgets.QLabel(str(actor_issue.actor))
            position = QtWidgets.QLabel(str(round(actor_issue.position, 2)))
            salience = QtWidgets.QLabel(str(actor_issue.salience))
            power = QtWidgets.QLabel(str(actor_issue.power))

            self.add_row(actor, position, salience, power)


class SettingsFormWidget(QtWidgets.QFormLayout):
    """
    FormLayout containing the different parameters for the model
    """

    def __init__(self, settings, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = settings

        self.fixed_weight = QtWidgets.QDoubleSpinBox()
        self.fixed_weight.setSingleStep(0.05)
        self.fixed_weight.setDecimals(2)
        self.fixed_weight.setValue(0.10)
        self.fixed_weight.setMaximum(1)

        self.salience_weight = QtWidgets.QDoubleSpinBox()
        self.salience_weight.setSingleStep(0.05)
        self.salience_weight.setMaximum(1)
        self.salience_weight.setDecimals(2)
        self.salience_weight.setValue(0.40)

        self.randomized_value = QtWidgets.QDoubleSpinBox()
        self.randomized_value.setSingleStep(0.05)

        self.start = QtWidgets.QDoubleSpinBox()
        self.start.setSingleStep(0.05)

        self.step = QtWidgets.QDoubleSpinBox()
        self.step.setSingleStep(0.05)

        self.stop = QtWidgets.QDoubleSpinBox()
        self.stop.setSingleStep(0.05)

        self.iterations = QtWidgets.QSpinBox()
        self.iterations.setMinimum(1)
        self.iterations.setValue(10)
        self.iterations.setMaximum(10000)

        self.repetitions = QtWidgets.QSpinBox()
        self.repetitions.setMinimum(1)
        self.repetitions.setValue(10)
        self.repetitions.setMaximum(10000)

        self.addRow(QtWidgets.QLabel("Fixed weight"), self.fixed_weight)
        self.addRow(QtWidgets.QLabel("Salience weight"), self.salience_weight)
        self.addRow(QtWidgets.QLabel(""))
        self.addRow(QtWidgets.QLabel("Negotiation rounds"), self.iterations)
        self.addRow(QtWidgets.QLabel("Simulation repetitions"), self.repetitions)
        self.addRow(QtWidgets.QLabel(""))

        self.addRow(QtWidgets.QLabel("p-value"))
        self.addRow(QtWidgets.QLabel("Start"), self.start)
        self.addRow(QtWidgets.QLabel("Step"), self.step)
        self.addRow(QtWidgets.QLabel("Stop"), self.stop)

        # self.addRow(QtWidgets.QLabel('Extra value'), self.randomized_value)

    def load(self):
        """
        Copy the values from the ProgramSettings object
        """

        settings = self.settings.__dict__.items()

        for key, value in settings:
            if hasattr(self, key):
                attr = getattr(self, key)

                if isinstance(value, bool):  # type: QtWidgets.QAction
                    attr.setChecked(value)
                if isinstance(attr, list):
                    self.settings.__dict__[attr] = value
                else:
                    attr.setValue(value)

    def save(self):
        """
        Set the attributes to the ProgramSettings object
        """
        settings = self.__dict__.items()

        for key, value in settings:
            if hasattr(self.settings, key):
                setattr(self.settings, key, value.value())


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal(str, int)
    update = QtCore.pyqtSignal(int, int, float)

    def __init__(self, settings: ProgramSettings):
        super(Worker, self).__init__()

        self.settings = settings
        self._break = False

    @QtCore.pyqtSlot()
    def run_model(self):
        settings = self.settings

        print("start")
        print(settings.start)

        if settings.start == settings.stop:
            p_values = [settings.start]
        else:
            p_values = [
                str(round(p, 2))
                for p in float_range(
                    start=settings.start, step=settings.step, stop=settings.stop
                )
            ]

        print("P values")
        print(p_values)

        selected_actors = settings.selected_actors
        selected_issues = settings.selected_issues

        repetitions = settings.repetitions
        iterations = settings.iterations

        input_filename = settings.input_filename

        for p in p_values:
            model = init_model("equal", settings.input_filename, p=p)

            csv_parser = csvparser.CsvParser(model)
            csv_parser.read(
                input_filename,
                actor_whitelist=selected_actors,
                issue_whitelist=selected_issues,
            )

            output_directory = init_output_directory(
                model=model,
                output_dir=settings.output_directory,
                selected_actors=settings.selected_actors,
            )

            actor_issues = copy.deepcopy(model.actor_issues)

            event_handler = init_event_handlers(model, output_directory, settings)
            event_handler.before_repetitions(
                repetitions=repetitions, iterations=iterations
            )

            start_time = time.time()

            for repetition in range(repetitions):

                model.actor_issues = copy.deepcopy(actor_issues)

                model_loop = helpers.ModelLoop(model, event_handler, repetition)

                event_handler.before_iterations(repetition)

                for iteration_number in range(iterations):

                    if self._break:
                        break

                    logging.info("round {0}.{1}".format(repetition, iteration_number))
                    self.update.emit(repetition, iteration_number, start_time)

                    model_loop.loop()

                event_handler.after_iterations(repetition)

                if self._break:
                    break

            event_handler.after_repetitions()

            self.finished.emit(output_directory, model.tie_count)

    def stop(self):
        self._break = True


class SummaryWidget(DynamicFormLayout):
    def __init__(
        self, main_window, settings, data, actor_widget, issue_widget, *args, **kwargs
    ):
        """

        :type settings: ProgramSettings
        :type data: ProgramData
        :type actor_widget: ActorWidget
        :type issue_widget: IssueWidget
        """
        super(SummaryWidget, self).__init__(main_window, *args, **kwargs)

        self.settings = settings
        self.data = data
        self.actor_widget = actor_widget
        self.issue_widget = issue_widget

    def update_widget(self):

        self.clear()

        actors = self.actor_widget.get_selected()
        issues = self.issue_widget.get_selected()

        # self.add_text_row('Actors', ', '.join(actors))
        # self.add_text_row('Issues', ', '.join(issues))

        self.add_text_row("Input", self.settings.input_filename, self.test_callback)
        self.add_text_row(
            "Output directory", self.settings.output_directory, self.test_callback
        )

        settings = self.main_window.settings  # type: ProgramSettings
        settings_widget = self.main_window.settings_widget  # type: SettingsFormWidget

        p_values = [
            str(round(p, 2))
            for p in float_range(
                start=float(settings_widget.start.value()),
                step=float(settings_widget.step.value()),
                stop=float(settings_widget.stop.value()),
            )
        ]

        self.add_text_row("p-values", ", ".join(p_values))

        output_selection = []

        if settings.issue_development_csv:
            output_selection.append("Issue development values [.csv]")

        if settings.summary_only:
            output_selection.append("Summary only [.csv]")

        if settings.output_sqlite:
            output_selection.append("Sqlite [database]")

        if settings.exchanges_csv:
            output_selection.append("Exchange values [.csv]")

        if settings.externalities_csv:
            output_selection.append("Externalities [.csv]")

        if settings.voting_positions:
            output_selection.append("Show Voting positions [.csv]")

        self.add_text_row("Output settings", output_selection[0])

        for setting in output_selection[-1:]:
            self.add_text_row("", setting)

        self.main_window.set_start_button_state()

    def add_text_row(self, label, value, callback=None):

        if callback:
            value_label = QtWidgets.QLabel(
                '<a href="{}">...{}/</a>'.format(value, value[-50:])
            )
            value_label.linkActivated.connect(callback)
        else:
            value_label = QtWidgets.QLabel(value)

        self.add_row(QtWidgets.QLabel(label), value_label)

    def test_callback(self, link):
        open_file(link)


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.settings = main_window.settings

        file_menu = self.addMenu("&File")
        output_menu = self.addMenu("&Output")

        self.output_sqlite = QtWidgets.QAction("&sqlite", self)
        self.output_sqlite.setCheckable(True)

        self.issue_development_csv = QtWidgets.QAction("Issue development (.csv)", self)
        self.issue_development_csv.setCheckable(True)
        self.issue_development_csv.setChecked(True)

        self.externalities_csv = QtWidgets.QAction("Externalities (.csv)", self)
        self.externalities_csv.setCheckable(True)

        self.exchanges_csv = QtWidgets.QAction("Exchanges (.csv)", self)
        self.exchanges_csv.setCheckable(True)

        self.voting_positions = QtWidgets.QAction("Show voting positions", self)
        self.voting_positions.setCheckable(True)

        self.summary_only = QtWidgets.QAction("Summary only (.csv)", self)
        self.summary_only.setCheckable(True)
        self.summary_only.setChecked(True)

        self.open_data_view = QtWidgets.QAction("Data view", self)
        self.open_data_view.triggered.connect(self.main_window.open_data_view)

        open_action = QtWidgets.QAction("&Open", self)
        open_action.triggered.connect(self.main_window.open_input_data)

        save_settings = QtWidgets.QAction("&Save settings", self)
        save_settings.triggered.connect(self.main_window.save_settings)

        file_menu.addAction(open_action)
        file_menu.addAction(save_settings)
        file_menu.addSeparator()
        file_menu.addAction(self.open_data_view)

        output_dir_action = QtWidgets.QAction("&Directory", self)
        output_dir_action.triggered.connect(self.main_window.select_output_dir)

        output_menu.addAction(self.issue_development_csv)
        output_menu.addAction(self.externalities_csv)
        output_menu.addAction(self.exchanges_csv)
        output_menu.addSeparator()
        output_menu.addAction(self.summary_only)
        output_menu.addAction(self.output_sqlite)
        output_menu.addAction(self.voting_positions)
        output_menu.addSeparator()
        output_menu.addAction(output_dir_action)

        debug = self.addMenu("Debug")
        log_action = QtWidgets.QAction("Show log window", self)
        log_action.triggered.connect(self.main_window.show_debug_dialog)
        debug.addAction(log_action)

    def load(self):
        """
        Copy the values from the ProgramSettings object
        """

        settings = self.settings.__dict__.items()

        for key, value in settings:
            if hasattr(self, key):
                attr = getattr(self, key)

                if isinstance(value, bool):  # type: QtWidgets.QAction
                    attr.setChecked(value)
                else:
                    attr.setValue(value)

    def save(self):
        """
        Set the attributes to the ProgramSettings object
        """
        settings = self.__dict__.items()

        for key, value in settings:
            if hasattr(self.settings, key):
                attr = getattr(self, key)

                if isinstance(attr, QtWidgets.QAction):
                    setattr(self.settings, key, value.isChecked())
                else:
                    setattr(self.settings, key, value.value())


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
    def __init__(self):
        super().__init__()

        self.data = ProgramData()
        self.settings = ProgramSettings()

        self.start = QtWidgets.QPushButton("Start")

        self.issue_widget = IssueWidget(self)
        self.actor_widget = ActorWidget(self)
        self.actor_issue_widget = ActorIssueWidget(self)
        self.settings_widget = SettingsFormWidget(self.settings)

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
        open_file("decide.log")

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

        self.setMenuBar(MenuBar(self))

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

        ex = InputWindow(self)

    def init_ui_data(self):

        if not os.path.isfile(self.settings.input_filename):
            return

        try:

            model = EqualGainModel()
            csv_parser = csvparser.CsvParser(model)
            csv_parser.read(self.settings.input_filename)

            self.data.actors = model.actors
            self.data.issues = model.issues
            self.data.actor_issues = model.actor_issues
            self.update_data_widgets()

        except Exception as e:
            self.statusBar().showMessage(str(e))
            QtWidgets.QMessageBox.about(self, "Input data invalid", str(e))
            logging.error(e)

    def run_safe(self):

        self.worker = Worker(self.settings)
        self.worker.finished.connect(self.finished)
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.update.connect(self.update_progress)
        self.thread.started.connect(self.worker.run_model)
        self.thread.start()

        print("thread started")

    def update_progress(self, repetition, iteration, start_time):

        value = repetition * (self.settings.iterations) + iteration

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

        if not self.worker._break:
            buttonReply = QtWidgets.QMessageBox.question(
                self,
                "Done",
                "Done executing. Found {} ties. Open the result directory?".format(
                    tie_count
                ),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )

            if buttonReply == QtWidgets.QMessageBox.Yes:
                if self.settings.summary_only and self.settings.issue_development_csv:
                    open_file(os.path.join(output_directory, "issues", "summary"))
                else:
                    open_file(output_directory)

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
                self.menuBar().load()
                self.settings_widget.load()

            except ET.ParseError:
                logging.info("Invalid xml")

    def save_settings(self):
        self.settings_widget.save()
        self.issue_widget.save()
        self.actor_widget.save()
        self.menuBar().save()
        self.settings.save()

    def cancel(self):
        self.worker.stop()


def main():
    sys.excepthook = exception_hook
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    decide = DecideMainWindow()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
