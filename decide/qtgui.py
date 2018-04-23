import decimal
import json
import logging
import os
import sys
import xml.etree.cElementTree as ET
from datetime import datetime
from typing import List

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from decide.cli import init_model, init_output_directory
from decide.model import base
from decide.model.base import Issue, ActorIssue
from decide.model.equalgain import EqualGainModel
from decide.model.helpers import csvparser, helpers
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver

logging.basicConfig(filename='decide.log', filemode='w', level=logging.INFO,
                    format=' %(asctime)s - %(levelname)s - %(message)s')


class QPlainTextEditLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit()
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class DecideLogDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logTextBox = QPlainTextEditLogger()
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.INFO)

        layout = QtWidgets.QVBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(logTextBox.widget)
        self.setLayout(layout)


class ProgramData:
    """
    The data used for displaying
    """

    def __init__(self):
        self.issues = {}
        self.actors = {}
        self.actor_issues = {}


class ProgramSettings:
    """
    The settings for the model parameters
    """

    def __init__(self):

        self.input_filename = ''
        self.output_directory = ''

        self.salience_weight = 0.4
        self.fixed_weight = 0.1

        self.randomized_value = 0.00

        self.repetitions = 10
        self.iterations = 10

        self.settings_file = 'decide-settings.xml'
        self.settings_type = 'xml'

        self.version = 1

        self.output_sqlite = False
        self.issue_development_csv = True
        self.externalities_csv = False
        self.exchanges_csv = False
        self.voting_positions = False
        self.summary_only = True

    def save(self):
        if self.settings_type == 'xml':
            self._save_xml()

    def _save_xml(self):

        element = ET.Element("decide-settings")

        for key, value in self.__dict__.items():
            if not key.startswith('_') and hasattr(self, key):
                child = ET.Element(key)
                child.text = str(value)
                element.append(child)

        ET.ElementTree(element).write(self.settings_file)

    def load(self):
        if self.settings_type == 'xml':
            self._load_xml()

    def _load_xml(self):
        for elm in ET.parse(self.settings_file).getroot():

            if hasattr(self, elm.tag):

                attr = getattr(self, elm.tag)

                if isinstance(attr, bool):
                    setattr(self, elm.tag, elm.text == 'True')
                elif isinstance(attr, int):
                    setattr(self, elm.tag, int(elm.text))
                elif isinstance(attr, float):
                    setattr(self, elm.tag, float(elm.text))
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

            info = QtWidgets.QPushButton('values')
            info.setObjectName(issue.issue_id)
            info.clicked.connect(self.main_window.update_actor_issue_widget)

            self.checkboxes.append(checkbox)
            self.add_row(checkbox, lower, upper, info)


class ActorWidget(DynamicFormLayout):
    """
    Form layout for customizing the Actor selection
    """

    def set_actors(self, actors: List[base.Actor]):
        self.set_values(actors)

        for actor in actors:
            checkbox = QtWidgets.QCheckBox(str(actor))
            checkbox.setObjectName(actor.actor_id)
            self.checkboxes.append(checkbox)
            self.add_row(checkbox)


class ActorIssueWidget(DynamicFormLayout):

    def set_actor_issues(self, issue: base.Issue, actor_issues=List[base.ActorIssue]):
        self.set_values(actor_issues)

        self.add_row(QtWidgets.QLabel(str(issue)))

        heading = ['Actor', 'Position', 'Salience', 'Power']

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

        self.iterations = QtWidgets.QSpinBox()
        self.iterations.setMinimum(1)
        self.iterations.setValue(10)
        self.iterations.setMaximum(10000)

        self.repetitions = QtWidgets.QSpinBox()
        self.repetitions.setMinimum(1)
        self.repetitions.setValue(10)
        self.repetitions.setMaximum(10000)

        self.addRow(QtWidgets.QLabel('Fixed weight'), self.fixed_weight)
        self.addRow(QtWidgets.QLabel('Salience weight'), self.salience_weight)
        self.addRow(QtWidgets.QLabel('Randomize value'), self.randomized_value)
        self.addRow(QtWidgets.QLabel('Negotiation rounds'), self.iterations)
        self.addRow(QtWidgets.QLabel('Simulation repetitions'), self.repetitions)

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
                setattr(self.settings, key, value.value())


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_window = main_window
        self.settings = main_window.settings

        file_menu = self.addMenu('&File')
        output_menu = self.addMenu('&Output')

        self.output_sqlite = QtWidgets.QAction('&sqlite', self)
        self.output_sqlite.setCheckable(True)

        self.issue_development_csv = QtWidgets.QAction('Issue development .csv', self)
        self.issue_development_csv.setCheckable(True)

        self.externalities_csv = QtWidgets.QAction('Externalities .csv', self)
        self.externalities_csv.setCheckable(True)

        self.exchanges_csv = QtWidgets.QAction('Exchanges .csv', self)
        self.exchanges_csv.setCheckable(True)

        self.voting_positions = QtWidgets.QAction('&voting positions', self)
        self.voting_positions.setCheckable(True)

        self.summary_only = QtWidgets.QAction('&summary only', self)
        self.summary_only.setCheckable(True)

        open_action = QtWidgets.QAction('&Open', self)
        open_action.triggered.connect(self.main_window.open_input_data)

        save_settings = QtWidgets.QAction('&Save settings', self)
        save_settings.triggered.connect(self.main_window.save_settings)

        file_menu.addAction(open_action)
        file_menu.addAction(save_settings)

        output_dir_action = QtWidgets.QAction('&Directory', self)
        output_dir_action.triggered.connect(self.main_window.select_output_dir)

        output_menu.addAction(self.output_sqlite)
        output_menu.addAction(self.issue_development_csv)
        output_menu.addAction(self.externalities_csv)
        output_menu.addAction(self.exchanges_csv)
        output_menu.addAction(self.summary_only)
        output_menu.addAction(self.voting_positions)
        output_menu.addAction(output_dir_action)

        debug = self.addMenu('Debug')
        log_action = QtWidgets.QAction('Show log window', self)
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


class DecideMainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.data = ProgramData()
        self.settings = ProgramSettings()

        self.issue_widget = IssueWidget(self)
        self.actor_widget = ActorWidget(self)
        self.actor_issue_widget = ActorIssueWidget(self)
        self.settings_widget = SettingsFormWidget(self.settings)

        self.init_ui()

        self.load_settings()

        self.init_ui_data()

    def show_debug_dialog(self):
        dlg = DecideLogDialog(self)
        dlg.setWindowTitle('Log window')
        dlg.show()

    def update_data_widgets(self):

        self.issue_widget.set_issues(list(self.data.issues.values()))
        self.actor_widget.set_actors(list(self.data.actors.values()))

        if len(self.issue_widget.objects) > 0:
            issue = self.issue_widget.objects[0]
            actor_issues = list(self.data.actor_issues[issue].values())
            self.actor_issue_widget.set_actor_issues(issue.name, actor_issues)

    def update_actor_issue_widget(self):
        """
        Button event to update the ActorIssueWidget
        """
        issue = self.data.issues[self.sender().objectName()]
        actor_issues = list(self.data.actor_issues[issue].values())

        self.actor_issue_widget.set_actor_issues(issue, actor_issues)

    def open_input_data(self):
        """
        Open the file, parse the data and update the layout
        """
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select input data")

        if file_name:
            self.statusBar().showMessage('Input file set to {} '.format(file_name))

            self.settings.input_filename = file_name

            self.init_ui_data()

    def select_output_dir(self):
        """
        Output directory
        """
        self.settings.output_directory = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.statusBar().showMessage('Output directory set to: {} '.format(self.settings.output_directory))

    def init_ui(self):
        self.statusBar().showMessage('Ready')

        self.setMenuBar(MenuBar(self))

        main = QtWidgets.QHBoxLayout()

        start = QtWidgets.QPushButton('Start')
        start.clicked.connect(self.run)

        left = QtWidgets.QVBoxLayout()

        left_top = QtWidgets.QHBoxLayout()

        left_top.setAlignment(QtCore.Qt.AlignTop)

        actor_box = QtWidgets.QGroupBox('Actors')
        issue_box = QtWidgets.QGroupBox('Issues')
        actor_issue_box = QtWidgets.QGroupBox('Actor Issues')

        actor_box.setLayout(self.actor_widget)
        issue_box.setLayout(self.issue_widget)
        actor_issue_box.setLayout(self.actor_issue_widget)

        left_top.addWidget(actor_box, 1)
        left_top.addWidget(issue_box, 1)

        left.addLayout(left_top, 1)
        left.addWidget(actor_issue_box, 1)

        settings_box = QtWidgets.QGroupBox('Model parameters')
        settings_box.setLayout(self.settings_widget)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(settings_box)
        right.addWidget(start)

        main.addLayout(left, 1)
        main.addLayout(right, 1)

        q = QtWidgets.QWidget()
        q.setLayout(main)

        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle('Decide Exchange Model')
        self.show()

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
            QtWidgets.QMessageBox.about(self, 'Input data invalid', str(e))
            logging.error(e)

    def run(self):
        # store the current state of the app
        self.save_settings()

        # create a whitelist for the selected actors

        selected_actors = self.actor_widget.get_selected()
        selected_actors.sort()

        selected_issues = self.issue_widget.get_selected()
        selected_issues.sort()

        self.setWindowTitle('Decide Exchange Model {}'.format('-'.join(selected_actors)))

        start_time = datetime.now()  # for timing operations

        input_filename = self.settings.input_filename
        repetitions = self.settings.repetitions
        iterations = self.settings.iterations

        model = init_model('equal', input_filename, p=self.settings.randomized_value)

        output_directory = init_output_directory(
            model=model,
            output_dir=self.settings.output_directory,
            selected_actors=selected_actors
        )

        csv_parser = csvparser.CsvParser(model)
        csv_parser.read(input_filename, actor_whitelist=selected_actors, issue_whitelist=selected_issues)

        event_handler = self.init_event_handlers(model, output_directory, self.menuBar().summary_only.isChecked())
        event_handler.before_repetitions(repetitions=repetitions, iterations=iterations)

        dialog = QtWidgets.QProgressDialog('Task in progress', 'Cancel', 0,
                                           repetitions * iterations)

        dialog.setWindowTitle('-'.join(selected_actors))
        dialog.show()

        for repetition in range(repetitions):

            csv_parser.read(input_filename, actor_whitelist=selected_actors)

            model_loop = helpers.ModelLoop(model, event_handler, repetition)

            event_handler.before_iterations(repetition)

            for iteration_number in range(iterations):
                logging.info("round {0}.{1}".format(repetition, iteration_number))
                dialog.setValue((repetition * iterations) + iteration_number)
                QtWidgets.qApp.processEvents()
                model_loop.loop()

            event_handler.after_iterations(repetition)

        event_handler.after_repetitions()

        print("Finished in {0}".format(datetime.now() - start_time))

    def init_event_handlers(self, model, output_directory, summary_only=False):

        event_handler = Observable(model_ref=model, output_directory=output_directory)

        if self.menuBar().output_sqlite.isChecked():
            SQLiteObserver(event_handler, self.settings.output_directory)

        if self.menuBar().externalities_csv.isChecked():
            Externalities(event_handler, summary_only)

        if self.menuBar().exchanges_csv.isChecked():
            ExchangesWriter(event_handler, summary_only)

        if self.menuBar().issue_development_csv.isChecked():
            IssueDevelopment(event_handler, summary_only=summary_only)

        return event_handler

    def load_settings(self):

        if os.path.isfile(self.settings.settings_file):
            try:
                self.settings.load()
                self.menuBar().load()
                self.settings_widget.load()

            except ET.ParseError:
                logging.info('Invalid xml')

    def save_settings(self):
        self.settings_widget.save()
        self.menuBar().save()
        self.settings.save()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    ex = DecideMainWindow()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
