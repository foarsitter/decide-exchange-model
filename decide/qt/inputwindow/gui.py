import logging
import sys

from PyQt5 import QtWidgets

from decide import log_filename
from decide.cli import init_model
from decide.model.base import ActorIssue
from decide.model.helpers import csvparser
from decide.model.helpers.helpers import example_data_file_path, open_file, exception_hook
from decide.qt.helpers import esc, normalize
from decide.qt.inputwindow import signals
from decide.qt.inputwindow.models import IssueInputModel, ActorInputModel
from decide.qt.inputwindow.widgets import ActorWidget, IssueWidget, ActorIssueWidget, PositionWidget, SalienceWidget


class InputWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(InputWindow, self).__init__(*args, **kwargs)

        self.main = QtWidgets.QHBoxLayout()
        self.left = QtWidgets.QVBoxLayout()

        self.tabs = QtWidgets.QTabWidget()

        self.actor_widget = ActorWidget()
        self.issue_widget = IssueWidget()

        self.actor_issue_widget = ActorIssueWidget(
            self.actor_widget, self.issue_widget
        )

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

    def init_menu(self):

        self.menubar.setNativeMenuBar(False)
        self.setMenuBar(self.menubar)

        file_menu = self.menubar.addMenu("File")
        example_menu = self.menubar.addMenu("Examples")

        load_kopenhagen = QtWidgets.QAction("&load Kopenhagen", self.menubar)
        load_kopenhagen.triggered.connect(self.load_kopenhagen)

        load_cop = QtWidgets.QAction("&load Parijs", self.menubar)
        load_cop.triggered.connect(self.load_parijs)

        open_action = QtWidgets.QAction("Open", self.menubar)
        open_action.triggered.connect(self.open_dialog)

        save_action = QtWidgets.QAction("Save", self.menubar)
        save_action.triggered.connect(self.save_location)

        example_menu.addAction(load_kopenhagen)
        example_menu.addAction(load_cop)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)

    def load_kopenhagen(self):
        self.load(example_data_file_path("kopenhagen"))

    def load_parijs(self):
        self.load(example_data_file_path("CoP21"))

    def open_dialog(self):

        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select input data")

        if file_name:
            try:
                self.load(file_name)
            except Exception as ex:
                error_dialog = QtWidgets.QErrorMessage(self)
                error_dialog.showMessage(str(ex))

    def save_location(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Select input data")

        if file_name:
            self.save(file_name)

    def load(self, input_filename):

        model = init_model("equal", input_filename, p=0.0)

        csv_parser = csvparser.CsvParser(model)

        csv_parser.read(input_filename)

        actor_inputs = {}

        self.actor_widget.clear()
        self.issue_widget.clear()
        self.actor_issue_widget.clear()
        self.position_widget.clear()
        self.salience_widget.clear()

        for issue, actor_issues in model.actor_issues.items():
            issue_input = self.issue_widget.add_issue(
                issue.name, issue.lower, issue.upper
            )
            issue_input.comment = issue.comment
            self.actor_issue_widget.issues.add(issue_input)

            for actor, actor_issue in actor_issues.items():
                if actor not in actor_inputs:
                    actor_issue = actor_issue  # type: ActorIssue
                    actor_input = self.actor_widget.add_actor(
                        actor.name, actor_issue.power
                    )
                    actor_input.comment = actor.comment
                    actor_inputs[actor] = actor_input

                    self.actor_issue_widget.actors.add(actor_input)
                else:
                    actor_input = actor_inputs[actor]

                self.actor_issue_widget.add_actor_issue(
                    actor_input, issue_input, actor_issue
                )

        self.position_widget.redraw()
        self.position_widget.set_choices(self.actor_issue_widget.issues)

        self.salience_widget.redraw()
        self.salience_widget.set_choices(self.actor_issue_widget.actors)

    def save(self, filename):

        with open(filename, "w") as file:

            for actor in self.actor_widget.items.values():
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

            for issue in self.issue_widget.items.values():
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

            for actor_id, actor_issues in self.actor_issue_widget.items.items():

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
                                normalize(actor_issue.power),
                                "\n",
                            ]
                        )
                    )

        print(filename)
        open_file(filename)


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
    if key == 'name':
        input_window.salience_widget.update_choice(sender.id, sender.name)
    elif key == 'power':

        for actor_issue in input_window.actor_issue_widget.items[sender.id].values():
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
    if key == 'name':
        input_window.position_widget.update_choice(sender.id, sender.name)

    input_window.position_widget.redraw()
    input_window.salience_widget.redraw()


if __name__ == "__main__":
    logging.basicConfig(
        filename=log_filename,
        filemode="w",
        level=logging.DEBUG,
        format=" %(asctime)s - %(levelname)s - %(message)s",
    )

    sys.excepthook = exception_hook

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    input_window = InputWindow()

    sys.exit(app.exec_())
