import decimal
import logging
import os
import sys
import xml.etree.cElementTree as ET
from datetime import datetime

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, qApp

from decide.cli import init_model, init_output_directory
from decide.model.base import Issue, ActorIssue
from decide.model.equalgain import EqualGainModel
from decide.model.helpers import csvparser, helpers
from decide.model.observers.exchanges_writer import ExchangesWriter
from decide.model.observers.externalities import Externalities
from decide.model.observers.issue_development import IssueDevelopment
from decide.model.observers.observer import Observable
from decide.model.observers.sqliteobserver import SQLiteObserver

logging.basicConfig(filename='decide.log', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')


class QPlainTextEditLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit()
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MyDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        logTextBox = QPlainTextEditLogger()
        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(logTextBox)
        # You can control the logging level
        logging.getLogger().setLevel(logging.DEBUG)

        self._button = QtWidgets.QPushButton(self)
        self._button.setText('Test Me')

        layout = QtWidgets.QVBoxLayout()
        # Add the new logging box widget to the layout
        layout.addWidget(logTextBox.widget)
        layout.addWidget(self._button)
        self.setLayout(layout)

        # Connect signal to slot
        self._button.clicked.connect(self.test)

    def test(self):
        logging.debug('damn, a bug')
        logging.info('something to remember')
        logging.warning('that\'s not right')
        logging.error('foobar')


class Example(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.input_filename = ''
        self.model = EqualGainModel()
        self.csv_parser = csvparser.CsvParser(self.model)
        self.issues = None
        self.actors = QtWidgets.QFormLayout()
        self.actor_checkboxes = []
        self.actor_issues = None

        self.output_directory = ''

        self.init_ui()

    def init_model(self):

        try:
            self.csv_parser.read(self.input_filename)
        except Exception as e:
            self.statusBar().showMessage(str(e))
            QtWidgets.QMessageBox.about(self, 'Input data invalid', str(e))
            logging.error(e)

        self.issues.clear()

        self.show_actors()

        for issue in self.model.issues.values():  # type: Issue
            self.issues.addItem(str(issue.issue_id))

        try:
            self.show_issue_data(issue.issue_id)
        except Exception as e:
            logging.error(e)

    def show_issue_data(self, issue):

        for i in reversed(range(self.actor_issues.count())):
            self.actor_issues.itemAt(i).widget().deleteLater()

        row = 0

        for actor_issue in self.model.actor_issues[issue].values():  # type: ActorIssue
            self.actor_issues.addWidget(QtWidgets.QLabel(actor_issue.issue.name), row, 0)
            self.actor_issues.addWidget(QtWidgets.QLabel(str(actor_issue.actor)), row, 1)
            self.actor_issues.addWidget(QtWidgets.QLabel(str(round(actor_issue.position, 2))), row, 2)
            self.actor_issues.addWidget(QtWidgets.QLabel(str(actor_issue.salience)), row, 3)
            self.actor_issues.addWidget(QtWidgets.QLabel(str(actor_issue.power)), row, 4)

            row += 1

    def show_actors(self):
        # clear the layout
        for i in reversed(range(self.actors.count())):
            self.actors.itemAt(i).widget().deleteLater()

        row = 0
        self.actor_checkboxes = []

        for actor in self.model.actors.values():
            checkbox = QtWidgets.QCheckBox(str(actor))
            checkbox.setObjectName(actor.actor_id)
            self.actor_checkboxes.append(checkbox)

            self.actors.addRow(checkbox)
            row += 1

    def open_input_data(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                   "All Files (*);;Python Files (*.py)", options=options)
        if file_name:
            self.statusBar().showMessage('Input file set to {} '.format(file_name))

            self.input_filename = file_name

            self.init_model()

    def issue_changed(self, curr, prev):
        if curr:
            self.show_issue_data(curr.text())
            logging.info(curr.text())

    def select_output_dir(self):
        self.output_directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        self.statusBar().showMessage('Output directory set to: {} '.format(self.output_directory))

    def init_ui(self):
        self.statusBar().showMessage('Ready')

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        output_menu = menubar.addMenu('&Output')

        self.sqlite = QtWidgets.QAction('&sqlite', self)
        self.sqlite.setCheckable(True)

        self.csv = QtWidgets.QAction('&.csv', self)
        self.csv.setCheckable(True)

        self.voting_positions = QtWidgets.QAction('&voting positions', self)
        self.voting_positions.setCheckable(True)

        open_action = QtWidgets.QAction('&Open', self)
        open_action.triggered.connect(self.open_input_data)

        output_dir_action = QtWidgets.QAction('&Directory', self)
        output_dir_action.triggered.connect(self.select_output_dir)

        output_menu.addAction(self.sqlite)
        output_menu.addAction(self.csv)
        output_menu.addAction(self.voting_positions)
        output_menu.addAction(output_dir_action)

        file_menu.addAction(open_action)

        main = QtWidgets.QHBoxLayout()

        start = QtWidgets.QPushButton('Start')
        start.clicked.connect(self.run)
        self.actor_issues = QtWidgets.QGridLayout()

        self.issues = QtWidgets.QListWidget()
        self.issues.currentItemChanged.connect(self.issue_changed)

        left = QtWidgets.QVBoxLayout()

        left_top = QtWidgets.QHBoxLayout()

        left_top.addLayout(self.actors)
        left_top.addWidget(self.issues)

        left.addLayout(left_top)
        left.addLayout(self.actor_issues)

        form_layout = QtWidgets.QFormLayout()

        self.fixed_weight = QtWidgets.QDoubleSpinBox()
        self.fixed_weight.setSingleStep(0.05)
        self.fixed_weight.setDecimals(2)
        self.fixed_weight.setValue(0.10)

        self.salience_weight = QtWidgets.QDoubleSpinBox()
        self.salience_weight.setSingleStep(0.05)
        self.salience_weight.setDecimals(2)
        self.salience_weight.setValue(0.40)

        self.randomized_value = QtWidgets.QDoubleSpinBox()
        self.randomized_value.setSingleStep(0.05)

        self.iterations = QtWidgets.QSpinBox()
        self.iterations.setValue(10)

        self.repetitions = QtWidgets.QSpinBox()
        self.repetitions.setValue(10)

        form_layout.addRow(QtWidgets.QLabel('Fixed weight'), self.fixed_weight)
        form_layout.addRow(QtWidgets.QLabel('Salience weight'), self.salience_weight)
        form_layout.addRow(QtWidgets.QLabel('Randomize value'), self.randomized_value)
        form_layout.addRow(QtWidgets.QLabel('Negotiation rounds'), self.iterations)
        form_layout.addRow(QtWidgets.QLabel('Simulation repetitions'), self.repetitions)

        right = QtWidgets.QVBoxLayout()
        right.addLayout(form_layout)
        right.addWidget(start)

        main.addLayout(left)
        main.addLayout(right)

        q = QtWidgets.QWidget()
        q.setLayout(main)

        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle('Decide Exchange Model')
        self.show()

        self.load_settings()

        print(self.output_directory)

        if self.input_filename != '':
            self.init_model()

    def run(self):
        # store the current state of the app
        self.save_settings()

        # create a whitelist for the selected actors

        selected_actors = []
        for checkbox in self.actor_checkboxes:  # type: QtWidgets.QCheckBox
            if checkbox.isChecked():
                selected_actors.append(checkbox.objectName())

        start_time = datetime.now()  # for timing operations

        self.model = init_model('equal', self.input_filename, p=self.randomized_value.value())

        output_directory = init_output_directory(self.model, self.output_directory, selected_actors=selected_actors)

        self.csv_parser = csvparser.CsvParser(self.model)
        self.csv_parser.read(self.input_filename, actor_whitelist=selected_actors)

        event_handler = self.init_event_handlers(output_directory)
        event_handler.before_repetitions(repetitions=self.repetitions.value(), iterations=self.iterations.value())

        dialog = QtWidgets.QProgressDialog('Task in progress', 'Cancel', 0,
                                           self.repetitions.value() * self.iterations.value())
        dialog.show()

        for repetition in range(self.repetitions.value()):

            self.csv_parser.read(self.input_filename, actor_whitelist=selected_actors)

            model_loop = helpers.ModelLoop(self.model, event_handler, repetition)

            event_handler.before_iterations(repetition)

            for iteration_number in range(self.iterations.value()):
                logging.info("round {0}.{1}".format(repetition, iteration_number))
                dialog.setValue((repetition * self.iterations.value()) + iteration_number)
                qApp.processEvents()
                model_loop.loop()

            event_handler.after_iterations(repetition)

        event_handler.after_repetitions()

        event_handler.log(message="Finished in {0}".format(datetime.now() - start_time))

    def init_event_handlers(self, output_directory):

        event_handler = Observable(model_ref=self.model, output_directory=output_directory)

        if self.sqlite.isChecked():
            SQLiteObserver(event_handler, output_directory)

        if self.csv.isChecked():
            Externalities(event_handler)
            ExchangesWriter(event_handler)
            IssueDevelopment(event_handler)

        return event_handler

    def load_settings(self):

        if os.path.isfile("model-settings.xml"):
            try:
                for elm in ET.parse("model-settings.xml").getroot():

                    if hasattr(self, elm.tag):
                        attr = getattr(self, elm.tag)

                        if isinstance(attr, QtWidgets.QDoubleSpinBox):
                            attr.setValue(decimal.Decimal(elm.text))
                        elif isinstance(attr, QtWidgets.QSpinBox):
                            attr.setValue(int(elm.text))
                        elif isinstance(attr, QtWidgets.QAction) and attr.isCheckable():
                            attr.setChecked(True if elm.text == 'True' else False)
                        elif isinstance(attr, str):
                            setattr(self, elm.tag, elm.text)
                        else:
                            print(type(attr))

            except ET.ParseError:
                logging.info('Invalid xml')

    def save_settings(self):
        tree = ET.ElementTree(self.to_xml())
        tree.write("model-settings.xml")

    def to_xml(self):

        element = ET.Element("model-settings")

        properties = ['repetitions', 'iterations', 'randomized_value', 'sqlite', 'csv', 'salience_weight',
                      'fixed_weight', 'input_filename', 'output_directory']

        for key in properties:
            attr = getattr(self, key)
            child = ET.Element(key)

            if isinstance(attr, QtWidgets.QWidget):
                child.text = str(attr.value())
            elif isinstance(attr, QtWidgets.QAction) and attr.isCheckable():
                child.text = str(attr.isChecked())
            else:
                child.text = str(attr)
            element.append(child)

        return element


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    ex = Example()

    dlg = MyDialog()
    dlg.show()
    dlg.raise_()

    sys.exit(app.exec_())
