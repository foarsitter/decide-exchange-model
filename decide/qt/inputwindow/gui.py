import logging
import os
import sys

import requests
from PyQt5 import QtWidgets, QtGui

from decide import log_filename, input_folder
from decide.data.reader import InputDataFile
from decide.qt.inputwindow import signals
from decide.qt.inputwindow.models import IssueInputModel, ActorInputModel
from decide.qt.inputwindow.widgets import (
    ActorWidget,
    IssueWidget,
    ActorIssueWidget,
    PositionWidget,
    SalienceWidget,
)
from decide.qt.mainwindow.gui import DecideMainWindow
from decide.qt.mainwindow.helpers import esc, normalize
from decide.qt.utils import show_user_error


class InputWindow(QtWidgets.QMainWindow):
    def __init__(self, main_window: DecideMainWindow = None, *args, **kwargs):
        super(InputWindow, self).__init__(*args, **kwargs)

        # save the filename which we are editing
        self.input_filename = None

        # refresh the main windows after editing
        self.main_window = main_window

        self.main = QtWidgets.QHBoxLayout()
        self.left = QtWidgets.QVBoxLayout()

        self.tabs = QtWidgets.QTabWidget()

        self.actor_widget = ActorWidget()
        self.issue_widget = IssueWidget()

        self.actor_issue_widget = ActorIssueWidget(self.actor_widget, self.issue_widget)

        self.position_widget = PositionWidget(self.actor_issue_widget)
        self.salience_widget = SalienceWidget(self.actor_issue_widget)

        self.left.addWidget(self.actor_widget)
        self.left.addWidget(self.issue_widget)

        self.tabs.addTab(self.position_widget, "Positions (by Issue)")
        self.tabs.addTab(self.salience_widget, "Salience (by Actor)")

        self.main.addLayout(self.left)
        self.main.addWidget(self.tabs)

        q = QtWidgets.QWidget()
        q.setLayout(self.main)

        self.menubar = QtWidgets.QMenuBar(self)

        self.init_menu()
        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle("Decide Exchange Model")
        self.show()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.input_filename:
            self.main_window.load_input_data(self.input_filename)

    def init_menu(self):

        self.menubar.setNativeMenuBar(False)
        self.setMenuBar(self.menubar)

        file_menu = self.menubar.addMenu("File")
        example_menu = self.menubar.addMenu("Examples")

        load_kopenhagen = QtWidgets.QAction("&load Kopenhagen", self.menubar)
        load_kopenhagen.triggered.connect(self.load_copenhagen)

        load_cop = QtWidgets.QAction("&load Parijs", self.menubar)
        load_cop.triggered.connect(self.load_cop21)

        open_action = QtWidgets.QAction("Open", self.menubar)
        open_action.triggered.connect(self.open_dialog)

        save_action = QtWidgets.QAction("Save", self.menubar)
        save_action.triggered.connect(self.save_location)

        example_menu.addAction(load_kopenhagen)
        example_menu.addAction(load_cop)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)

    def load_copenhagen(self):
        self.load_input_file(
            "https://raw.githubusercontent.com/foarsitter/decide-exchange-model/master/data/input/copenhagen.csv")

    def load_sample_data(self):
        self.load_input_file(
            "https://raw.githubusercontent.com/foarsitter/decide-exchange-model/master/data/input/sample_data.txt")

    def load_cop21(self):
        self.load_input_file(
            "https://raw.githubusercontent.com/foarsitter/decide-exchange-model/master/data/input/cop21.csv"
        )

    def load_input_file(self, file_path):

        if file_path.startswith('http'):
            response = requests.get(file_path)

            file_path = file_path.split('/')[-1]

            download_dir = os.path.join(input_folder, 'downloads')

            if not os.path.isdir(download_dir):
                os.mkdir(download_dir)

            with open(os.path.join(download_dir, file_path), 'wb') as file:
                file.write(response.content)

        file = os.path.join(input_folder, file_path)

        if os.path.isfile(file):
            self.load(file)
        else:
            show_user_error(self, "Cannot load {}".format(file))

    def open_dialog(self):

        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select input data")

        if file_name:
            try:
                self.load(file_name)
            except Exception as ex:
                error_dialog = QtWidgets.QErrorMessage(self)
                error_dialog.showMessage(str(ex))

                raise ex

    def save_location(self):

        if self.input_filename:

            button_reply = QtWidgets.QMessageBox.question(
                self,
                "Save",
                "Overwrite existing file {}".format(
                    self.input_filename
                ),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
        else:
            button_reply = QtWidgets.QMessageBox.No

        if button_reply == QtWidgets.QMessageBox.Yes:
            file_name = self.input_filename
        else:
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Select input data")

        if file_name:
            self.save(file_name)

    def load(self, input_filename):

        data_file = InputDataFile.open(input_filename)

        actor_inputs = {}
        issue_inputs = {}
        actor_powers = {}

        self.actor_widget.clear()
        self.issue_widget.clear()
        self.actor_issue_widget.clear()
        self.position_widget.clear()
        self.salience_widget.clear()

        # collect all the power values for the Actor widget
        for actor_issue in data_file.actor_issues.values():
            if actor_issue.actor not in actor_powers:
                actor_powers[actor_issue.actor] = actor_issue.power

        for actor in data_file.actors.values():
            actor_input = self.actor_widget.add_actor(
                actor.id, actor_powers[actor.id]
            )

            actor_input.comment = str(actor.comment)

            actor_inputs[actor] = actor_input

            self.actor_issue_widget.actors.add(actor_input)

        for issue in data_file.issues.values():
            issue_input = self.issue_widget.add_issue(
                issue.name, issue.lower, issue.upper
            )
            issue_input.comment = issue.description

            issue_inputs[issue_input.name] = issue_input

            self.actor_issue_widget.issues.add(issue_input)

        for actor_issue in data_file.actor_issues.values():
            actor_input = actor_inputs[actor_issue.actor]
            issue_input = issue_inputs[actor_issue.issue]

            self.actor_issue_widget.add_actor_issue(
                actor_input, issue_input, actor_issue
            )

        self.position_widget.redraw()
        self.position_widget.set_choices(self.actor_issue_widget.issues)

        self.salience_widget.redraw()
        self.salience_widget.set_choices(self.actor_issue_widget.actors)

        self.input_filename = input_filename

    def save(self, filename):

        with open(filename, "w") as file:

            powers = {}

            for actor in self.actor_widget.actor_issues.values():
                powers[actor.name] = actor.power

                file.write(
                    "\t".join(
                        [
                            esc("#A"),
                            esc(actor.name),
                            esc(actor.name),
                            esc(actor.comment),
                            "\n",
                        ]
                    )
                )

            for issue in self.issue_widget.actor_issues.values():
                file.write(
                    "\t".join(
                        [
                            esc("#P"),
                            esc(issue.name),
                            esc(issue.name),
                            esc(issue.comment),
                            "\n",
                        ]
                    )
                )

                file.write(
                    "\t".join([esc("#M"), esc(issue.name), str(issue.lower), "\n"])
                )

                file.write(
                    "\t".join([esc("#M"), esc(issue.name), str(issue.upper), "\n"])
                )

            for actor_id, actor_issues in self.actor_issue_widget.actor_issues.items():

                for issue_id, actor_issue in actor_issues.items():
                    actor_issue = actor_issue  # type: ActorIssueInputModel

                    file.write(
                        "\t".join(
                            [
                                esc("#D"),
                                esc(actor_issue.actor.name),
                                esc(actor_issue.issue.name),
                                normalize(actor_issue.position),
                                normalize(actor_issue.salience),
                                normalize(powers[actor_issue.actor.name]),
                                "\n",
                            ]
                        )
                    )

        # open_file_natively(filename)


input_window = None


@signals.actor_created.connect
def actor_issue_box_actor_created(sender: ActorInputModel):
    input_window.actor_issue_widget.add_actor(sender)

    input_window.salience_widget.add_choice(sender.id, sender.name)


@signals.actor_deleted.connect
def actor_issue_box_delete_actor(sender: ActorInputModel, **kwargs):
    input_window.actor_issue_widget.delete_actor(sender)
    input_window.salience_widget.delete_choice(sender.id)


@signals.actor_changed.connect
def actor_issue_box_update_actor(sender: ActorInputModel, key: str, value):
    if key == "name":
        input_window.salience_widget.update_choice(sender.id, sender.name)
    elif key == "power":

        for actor_issue in input_window.actor_issue_widget.actor_issues[sender.id].values():
            actor_issue.set_power(value, True)

    input_window.position_widget.redraw()
    input_window.salience_widget.redraw()


@signals.issue_created.connect
def actor_issue_box_issue_created(sender: IssueInputModel):
    input_window.actor_issue_widget.add_issue(sender)

    input_window.position_widget.add_choice(sender.id, sender.name)


@signals.issue_deleted.connect
def actor_issue_box_delete_issue(sender: IssueInputModel, **kwargs):
    input_window.actor_issue_widget.delete_issue(sender)
    input_window.position_widget.delete_choice(sender.id)


@signals.issue_changed.connect
def actor_issue_box_update_issue(sender: IssueInputModel, key: str, value):
    if key == "name":
        input_window.position_widget.update_choice(sender.id, sender.name)

    input_window.position_widget.redraw()
    input_window.salience_widget.redraw()


def register_app(ex):
    global input_window
    input_window = ex


if __name__ == "__main__":
    logging.basicConfig(
        filename=log_filename,
        filemode="w",
        level=logging.DEBUG,
        format=" %(asctime)s - %(levelname)s - %(message)s",
    )

    #    sys.excepthook = exception_hook

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    input_window = InputWindow()

    sys.exit(app.exec_())
