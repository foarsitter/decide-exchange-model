import logging
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog

from decide.model.base import AbstractModel, Actor, Issue, ActorIssue
from decide.model.helpers import csvparser

logging.basicConfig(filename='decide.log', level=logging.DEBUG)


class Example(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.input_filename = ''
        self.model = AbstractModel()
        self.issues = None
        self.actors = None
        self.actor_issues = None
        self.initUI()

    def init_model(self):
        self.model = AbstractModel()
        try:
            csv_parser = csvparser.CsvParser(self.model)
            csv_parser.read(self.input_filename)
        except ValueError as e:
            self.statusBar().showMessage(str(e))
            QtWidgets.QMessageBox.about(self, 'Input data invalid', str(e))

        self.actors.clear()
        self.issues.clear()

        for actor in self.model.actors.values():  # type: Actor
            self.actors.addItem(str(actor))

        for issue in self.model.issues.values():  # type: Issue
            self.issues.addItem(str(issue.issue_id))

        self.show_issue_data(issue.issue_id)

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

    def open_input_data(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                   "All Files (*);;Python Files (*.py)", options=options)
        if file_name:
            print(file_name)
            self.input_filename = file_name

            self.init_model()

    def actor_changed(self, curr, prev):
        if curr:
            self.show_issue_data(curr.text())

    def issue_changed(self, curr, prev):
        if curr:
            self.show_issue_data(curr.text())
            print(curr.text())

    def initUI(self):
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

        output_menu.addAction(self.sqlite)
        output_menu.addAction(self.csv)
        output_menu.addAction(self.voting_positions)

        open_action = QtWidgets.QAction('&Open', self)
        open_action.triggered.connect(self.open_input_data)

        file_menu.addAction(open_action)

        main = QtWidgets.QHBoxLayout()

        start = QtWidgets.QPushButton('Start')
        self.actor_issues = QtWidgets.QGridLayout()

        self.actors = QtWidgets.QListWidget()
        self.actors.addItems(['Actor 1', 'Actor 2'])
        self.actors.currentItemChanged.connect(self.actor_changed)

        self.issues = QtWidgets.QListWidget()
        self.issues.addItems(['Issue 1', 'Issue 2'])
        self.issues.currentItemChanged.connect(self.issue_changed)

        left = QtWidgets.QVBoxLayout()

        left_top = QtWidgets.QHBoxLayout()

        left_top.addWidget(self.actors)
        left_top.addWidget(self.issues)

        left.addLayout(left_top)
        left.addLayout(self.actor_issues)

        form_layout = QtWidgets.QFormLayout()

        fixed_weight = QtWidgets.QDoubleSpinBox()
        fixed_weight.setSingleStep(0.05)
        fixed_weight.setDecimals(2)
        fixed_weight.setValue(0.10)

        salience_weight = QtWidgets.QDoubleSpinBox()
        salience_weight.setSingleStep(0.05)
        salience_weight.setDecimals(2)
        salience_weight.setValue(0.40)

        randomized_value = QtWidgets.QDoubleSpinBox()
        randomized_value.setSingleStep(0.05)

        rounds = QtWidgets.QSpinBox()
        rounds.setValue(10)
        repetitions = QtWidgets.QSpinBox()
        repetitions.setValue(10)

        form_layout.addRow(QtWidgets.QLabel('Fixed weight'), fixed_weight)
        form_layout.addRow(QtWidgets.QLabel('Salience weight'), salience_weight)
        form_layout.addRow(QtWidgets.QLabel('Randomize value'), randomized_value)
        form_layout.addRow(QtWidgets.QLabel('Negotiation rounds'), rounds)
        form_layout.addRow(QtWidgets.QLabel('Simulation repetitions'), repetitions)

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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
