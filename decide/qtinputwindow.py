import logging
import sys
import uuid
from collections import defaultdict

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QListWidgetItem

from decide import log_file, open_file, exception_hook
from decide.cli import init_model
from decide.model.base import ActorIssue
from decide.model.helpers import csvparser
from decide.model.helpers.helpers import data_file_path

logging.basicConfig(
    filename=log_file,
    filemode="w",
    level=logging.DEBUG,
    format=" %(asctime)s - %(levelname)s - %(message)s",
)


def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


class DoubleInput(QtWidgets.QLineEdit):
    def __init__(self):
        super(DoubleInput, self).__init__()

        self.setFixedWidth(75)

    def setValue(self, value):
        self.setText(str(value))

    @property
    def valueChanged(self):
        return self.textChanged


def esc(value):
    return "'{}'".format(value)


class Observer:
    """
    Listener
    """

    key = "AbstractObserver"

    def add(self, observer, value):
        raise NotImplementedError

    def delete(self, observer, row):
        raise NotImplementedError

    def change(self, observer, key, value, extra):
        raise NotImplementedError


class Observable:
    """
    Event
    """

    def __init__(self):
        self.observers = []

    def notify_add(self, value):
        for observer in self.observers:
            observer.add(self, value)

    def notify_delete(self, row):

        for observer in self.observers:
            observer.delete(self, row)

    def notify_change(self, key, value, observer=None, extra=None):
        for _observer in self.observers:

            if observer is None:
                observer = self
            _observer.change(observer, key, value, extra)

    def register(self, obj):
        self.observers.append(obj)


class PrintObserver(Observer):
    """
    For debugging
    """

    def add(self, observer, value):
        pass

    def delete(self, observer, row):
        pass

    def change(self, observer, key, value, extra):
        pass


class ActorInput(Observable):
    """
    Object containing a name and power
    """

    def __init__(self, name, power):
        super().__init__()
        self.id = None
        self._name = name
        self._power = power
        self._comment = ""
        self.key = "actor_input"

        self.register(PrintObserver())

        self.uuid = uuid.uuid4()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self.set_name(value)

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, value):
        self.set_power(value)

    def set_name(self, value, silence=False):
        self._name = value

        if not silence:
            self.notify_change("name", value)

    def set_power(self, value, silence=False):

        self._power = value

        if not silence:
            self.notify_change("power", value)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self.set_comment(value)

    def set_comment(self, value):
        self._comment = value


class IssueInput(Observable):
    """
    Object containing a name, lower and upper bounds
    """

    def __init__(self, name, lower, upper):
        super().__init__()
        self.id = None
        self._name = name
        self._lower = lower
        self._upper = upper
        self._comment = ""
        self.key = "issue_input"

        self.register(PrintObserver())

        self.uuid = uuid.uuid4()

    @property
    def name(self):
        return self._name

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    @name.setter
    def name(self, value):
        self.set_name(value)

    @lower.setter
    def lower(self, value):
        self.set_lower(value)

    @upper.setter
    def upper(self, value):
        self.set_upper(value)

    def set_name(self, value):
        self._name = value
        self.notify_change("name", value)

    def set_lower(self, value):
        self._lower = value
        self.notify_change("lower", value)

    def set_upper(self, value):
        self._upper = value
        self.notify_change("upper", value)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self.set_comment(value)

    def set_comment(self, value):
        self._comment = value


class ActorIssueInput(Observer, Observable):
    def add(self, key=None, value=None):
        self.actor_input.setText(self.actor.name)
        self.issue_input.setText(self.issue.name)
        self.power_input.setText(self.actor.power)

    def delete(self, observer, row):
        """
        Remove ... this row when the actor or issue is deleted
        """
        print("delete this actor issue")

    def change(self, observer, key, value, extra):

        if observer == self:
            return

        if isinstance(observer, ActorInput):
            if key == "name":
                self.actor_input.setText(value)
                self.notify_change("choices", True, observer=observer, extra=extra)
            if key == "power":
                self.power_input.setText(str(value))

        if isinstance(observer, IssueInput):
            if key == "name":
                self.issue_input.setText(value)
                self.notify_change("choices", True, observer=observer, extra=extra)
            if key == "upper":
                pass
            if key == "lower":
                pass

        if key == "position":
            self.set_position(value)

        if key == "power":
            self.set_power(value)

        self.notify_change("redraw", True, observer=observer, extra=extra)

    def __init__(self, actor: ActorInput, issue: IssueInput):
        super().__init__()
        self.id = None

        self.actor = actor
        self.issue = issue

        self.actor.register(self)
        self.issue.register(self)

        self.actor_input = QtWidgets.QLabel(actor.name)
        self.issue_input = QtWidgets.QLabel(issue.name)

        self.power_input = QtWidgets.QLabel(str(actor.power))

        self.position_input = DoubleInput()
        self.position_input.valueChanged.connect(self.set_position)

        self.salience_input = DoubleInput()

        self.meta = dict()

        self.uuid = uuid.uuid4()

        self._power = 0.0
        self._position = 0.0
        self._salience = 0.0

    @property
    def position(self):
        return self._position

    @property
    def salience(self):
        return self._salience

    @property
    def power(self):
        return self._power

    def set_position(self, value, silence=False, extra=None):
        self._position = value
        if not silence:
            self.notify_change("position", value, extra=extra)

    def set_power(self, value, silence=False, extra=None):
        self._power = value
        if not silence:
            self.notify_change("power", value, extra=extra)

    def set_salience(self, value, silence=False):
        self._salience = value
        if not silence:
            self.notify_change("salience", value)


class PositionInput(ActorIssueInput):
    """
    For editing the position
    """

    def __init__(self, actor_issue: ActorIssueInput):
        super().__init__(actor_issue.actor, actor_issue.issue)

        actor_issue.register(self)


class SalienceInput(ActorIssueInput):
    def __init__(self, actor_issue: ActorIssueInput):
        super().__init__(actor_issue.actor, actor_issue.issue)

        actor_issue.register(self)


class BoxLayout(QtWidgets.QGroupBox):
    def __init__(self, title, btn=True):
        super(BoxLayout, self).__init__(title)

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.grid_layout = QtWidgets.QGridLayout(self.scroll_area_widget)
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop)

        self.layout_container = QtWidgets.QVBoxLayout()
        self.layout_container.addWidget(self.scroll_area)

        if btn:
            container = QtWidgets.QHBoxLayout()

            self.refresh_button = QtWidgets.QPushButton("Refresh")
            self.add_button = QtWidgets.QPushButton("Add")
            self.refresh_button.clicked.connect(self.refresh)
            # self.layout_container.addWidget(QtWidgets.QTextEdit())
            container.addWidget(self.add_button)
            container.addWidget(self.refresh_button)
            self.layout_container.addLayout(container)
            self.layout_container.addWidget(self.add_button)

        self.setLayout(self.layout_container)

        self.items = {}

        self._row_pointer = 0

    def refresh(self):
        self.notify_change("redraw", True)

    def clear(self):
        clear_layout(self.grid_layout)

        self.items = {}
        self._row_pointer = 0

    def add_heading(self):
        raise NotImplementedError

    def add_row(self, *args, pointer=None):

        if pointer:
            row = pointer
        else:
            row = self._row_pointer

        for column, arg in enumerate(args):
            if isinstance(arg, str):
                arg = QtWidgets.QLabel(arg)

            self.grid_layout.addWidget(arg, row, column)

        self._row_pointer += 1

        return row

    def delete_row(self):

        sending_button = self.sender()  # type: QtWidgets.QPushButton

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.items[row]

        del self.items[row]

        for column in range(self.grid_layout.count()):

            item = self.grid_layout.itemAtPosition(row, column)
            if item:
                item.widget().deleteLater()
            self.grid_layout.removeItem(item)

        return obj


class ActorBox(BoxLayout, Observable):
    key = "actor_box"

    def __init__(self):
        super(ActorBox, self).__init__("Actors")

        self.add_button.clicked.connect(self.add_action)

        self.register(PrintObserver())

    def add_heading(self):
        self.add_row("Actor")

    def add_actor(self, name="", power=0.0):
        actor_input = ActorInput(name, str(power))
        actor_input.id = self._row_pointer

        name_input = QtWidgets.QLineEdit()
        name_input.setText(name)
        # call the setter on a change
        name_input.textChanged.connect(actor_input.set_name)

        power_input = DoubleInput()
        power_input.setValue(power)
        power_input.valueChanged.connect(actor_input.set_power)

        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row)
        delete_button.setObjectName("actor-" + str(self._row_pointer))

        comment_button = QtWidgets.QPushButton("Comment")
        comment_button.clicked.connect(self.comment_window)
        comment_button.setObjectName("actor-" + str(self._row_pointer))

        self.items[actor_input.id] = actor_input

        self.add_row(name_input, power_input, comment_button, delete_button)

        return actor_input

    def add_action(self):
        a = self.add_actor()
        self.notify_add(a)

    def delete_row(self):
        row = super().delete_row()
        self.notify_delete(row)

    def comment_window(self):
        sending_button = self.sender()  # type: QtWidgets.QPushButton

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.items[row]

        text, ok_pressed = QtWidgets.QInputDialog.getMultiLineText(
            self, "Comment", "Comment", obj.comment
        )
        if ok_pressed and text != "":
            obj.comment = text


class IssueBox(BoxLayout, Observable):
    key = "issue_box"

    def __init__(self):
        super(IssueBox, self).__init__("Issues")

        self.add_button.clicked.connect(self.add_action)

        self.register(PrintObserver())

    def add_heading(self):
        self.add_row("Issue", "Lower", "Upper")

    def add_issue(self, name="", lower=0, upper=100.0):
        issue_input = IssueInput(name, lower, upper)
        issue_input.id = self._row_pointer

        lower_input = DoubleInput()
        lower_input.setValue(lower)

        upper_input = DoubleInput()
        upper_input.setValue(upper)

        name_input = QtWidgets.QLineEdit()
        name_input.setText(name)
        # call the setter on a change
        name_input.textChanged.connect(issue_input.set_name)

        lower_input.valueChanged.connect(issue_input.set_lower)

        upper_input.valueChanged.connect(issue_input.set_upper)

        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row)
        delete_button.setObjectName("issue-" + str(self._row_pointer))

        comment_button = QtWidgets.QPushButton("Comment")
        comment_button.clicked.connect(self.comment_window)
        comment_button.setObjectName("issue-" + str(self._row_pointer))

        self.items[issue_input.id] = issue_input

        self.add_row(
            name_input, lower_input, upper_input, comment_button, delete_button
        )

        return issue_input

    def add_action(self):
        issue = self.add_issue()
        self.notify_add(issue)

    def delete_row(self):
        row = super().delete_row()

        self.notify_delete(row)

    def comment_window(self):
        sending_button = self.sender()  # type: QtWidgets.QPushButton

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.items[row]

        text, ok_pressed = QtWidgets.QInputDialog.getMultiLineText(
            self, "Comment", "Comment", obj.comment
        )
        if ok_pressed and text != "":
            obj.comment = text


class ActorIssueBox(BoxLayout, Observer, Observable):
    """
    The ActorIssueBox is an hidden box behind the scenes, so there is a single point of truth
    """

    def add_heading(self):
        pass

    def __init__(self, actor_box: ActorBox, issue_box: IssueBox):
        super(ActorIssueBox, self).__init__("Hidden Box")
        Observable.__init__(self)

        self.actor_box = actor_box
        self.issue_box = issue_box

        self.actor_box.register(self)
        self.issue_box.register(self)

        self.items = defaultdict(lambda: dict())

        self.actors = set()
        self.issues = set()

    def clear(self):
        super(ActorIssueBox, self).clear()
        self.items = defaultdict(lambda: dict())

        self.actors = set()
        self.issues = set()

    def delete(self, observer, row):
        if observer.key == IssueBox.key:
            self.issues.remove(row)
            for actor in self.actor_box.items.values():
                item = self.items[actor.id][row.id]
                self.notify_delete(item)
                del self.items[actor.id][row.id]

        if observer.key == ActorBox.key:
            self.actors.remove(row)
            for issue in self.issue_box.items.values():
                item = self.items[row.id][issue.id]
                self.notify_delete(item)
                del self.items[row.id][issue.id]

    def add(self, observer, value):
        # if an issue is added, we need to add all the existing actors for the issue
        if observer.key == IssueBox.key:
            self.issues.add(value)
            for actor in self.actor_box.items.values():
                self.add_actor_issue(actor, value)

        # if an actor is added, we need to add all the existing issues for the actor
        if observer.key == ActorBox.key:
            self.actors.add(value)
            for issue in self.issue_box.items.values():
                self.add_actor_issue(value, issue)

        self.notify_change("redraw", True, observer=observer)

    def add_actor_issue(
            self, actor: ActorInput, issue: IssueInput, actor_issue=None, silence=False
    ):

        actor_issue_input = ActorIssueInput(actor, issue)
        actor_issue_input.id = self._row_pointer

        self.items[actor.id][issue.id] = actor_issue_input

        if actor_issue:
            actor_issue_input.set_position(
                str(actor_issue.issue.de_normalize(actor_issue.position)), silence=True
            )
            actor_issue_input.set_salience(str(actor_issue.salience), silence=True)

        self._row_pointer += 1

        if not silence:
            self.notify_add(actor_issue_input)

    def change(self, observer, key, value, extra):
        self.notify_change(key, value, observer=observer, extra="ActorIssueBox")


class PositionSalienceBox(QtWidgets.QWidget, Observer, Observable):
    def __init__(self, actor_issue_box: ActorIssueBox):
        super(PositionSalienceBox, self).__init__()

        self.actor_issue_box = actor_issue_box
        self.actor_issue_box.register(self)

        self._row_pointer = 0

        self.choices = QtWidgets.QListWidget(self)
        self.choices.setMaximumHeight(100)
        self.choices.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        self.choices.itemSelectionChanged.connect(self.redraw)

        self.container = QtWidgets.QVBoxLayout(self)
        self.container.addWidget(self.choices)

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.grid_layout = QtWidgets.QGridLayout(self.scroll_area_widget)
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop)

        self.container.addWidget(self.scroll_area)

    def clear(self):

        self._row_pointer = 0
        clear_layout(self.grid_layout)

    def change(self, observer, key, value, extra):

        self.update_choices()
        self.redraw()

    def delete(self, observer, actor_issue_input):
        self.redraw()
        self.update_choices()

    def add(self, observer: Observer, value):
        value.register(self)
        self.redraw()
        self.update_choices()

    def add_heading(self):
        raise NotImplementedError

    def add_row(self, *args, pointer=None):

        if pointer:
            row = pointer
        else:
            row = self._row_pointer

        for column, arg in enumerate(args):
            if isinstance(arg, str):
                arg = QtWidgets.QLabel(arg)

            self.grid_layout.addWidget(arg, row, column)

        self._row_pointer += 1

        return row

    def redraw(self):

        clear_layout(self.grid_layout)

        self.add_heading()

        for issue in self.actor_issue_box.issues:
            for actor in self.actor_issue_box.actors:

                if (
                        actor.id in self.actor_issue_box.items
                        and issue.id in self.actor_issue_box.items[actor.id]
                ):
                    actor_issue = self.actor_issue_box.items[actor.id][
                        issue.id
                    ]  # type: ActorIssueInput

                    self.add_actor_issue(actor_issue)

    def add_actor_issue(self, actor_issue: ActorIssueInput):
        raise NotImplementedError

    def update_choices(self):

        self.choices.clear()

        for issue in self.actor_issue_box.issues:
            if issue.name != "":
                item = QListWidgetItem(self.choices)
                item.setText(issue.name)
                self.choices.addItem(item)

        self.choices.sortItems()

    def is_selected(self, value):

        items = self.choices.selectedItems()

        if len(items) == 0:
            return True

        for item in items:
            if item.text() == value:
                return True

        return False


class PositionBox(PositionSalienceBox):
    def add_heading(self):
        self.add_row("Issue", "Actor", "Power", "Position")

    def add_actor_issue(self, actor_issue):
        if self.is_selected(actor_issue.issue.name):
            position = DoubleInput()
            position.setValue(actor_issue.position)
            position.valueChanged.connect(actor_issue.set_position)

            self.add_row(
                QtWidgets.QLabel(actor_issue.issue.name),
                QtWidgets.QLabel(actor_issue.actor.name),
                QtWidgets.QLabel(str(round(float(actor_issue.actor.power), 3))),
                position,
            )

    def change(self, observer, key, value, extra):
        if key != "position":
            super(PositionBox, self).change(observer, key, value, extra)


class SalienceBox(PositionSalienceBox):
    def add_heading(self):
        self.add_row("Actor", "Issue", "Power", "Position", "Salience")

    def add_actor_issue(self, actor_issue: ActorIssueInput):
        if self.is_selected(actor_issue.actor.name):
            salience = DoubleInput()
            salience.setValue(actor_issue.salience)
            salience.valueChanged.connect(actor_issue.set_salience)

            self.add_row(
                QtWidgets.QLabel(actor_issue.actor.name),
                QtWidgets.QLabel(actor_issue.issue.name),
                QtWidgets.QLabel(str(actor_issue.actor.power)),
                QtWidgets.QLabel(str(actor_issue.position)),
                salience,
            )

    def update_choices(self):

        self.choices.clear()

        items = [str(x.name) for x in self.actor_issue_box.actors if x != ""]
        items.sort()

        for x in items:
            if x != "":
                item = QtWidgets.QListWidgetItem(self.choices)
                item.setText(x)

                self.choices.addItem(item)

    def change(self, observer, key, value, extra):
        if key != "salience":
            super(SalienceBox, self).change(observer, key, value, extra)


class InputWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(InputWindow, self).__init__(parent)

        self.main = QtWidgets.QHBoxLayout()
        self.left = QtWidgets.QVBoxLayout()

        self.tabs = QtWidgets.QTabWidget()

        self.actor_input_control = ActorBox()
        self.actor_input_control.add_heading()

        self.issue_input_control = IssueBox()
        self.issue_input_control.add_heading()

        self.actor_issues = ActorIssueBox(
            self.actor_input_control, self.issue_input_control
        )

        self.position_box = PositionBox(self.actor_issues)
        self.position_box.add_heading()

        self.left.addWidget(self.actor_input_control)
        self.left.addWidget(self.issue_input_control)

        self.tabs.addTab(self.position_box, "Positions (by Issue)")

        self.salience_box = SalienceBox(self.actor_issues)
        self.salience_box.add_heading()
        self.tabs.addTab(self.salience_box, "Saliences (by Actor)")

        self.main.addLayout(self.left)
        self.main.addWidget(self.tabs)

        q = QtWidgets.QWidget()
        q.setLayout(self.main)

        menubar = QtWidgets.QMenuBar()
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File")
        example_menu = menubar.addMenu("Examples")

        load_kopenhagen = QtWidgets.QAction("&load Kopenhagen", menubar)
        load_kopenhagen.triggered.connect(self.load_kopenhagen)

        load_cop = QtWidgets.QAction("&load Parijs", menubar)
        load_cop.triggered.connect(self.load_parijs)

        open_action = QtWidgets.QAction("Open", menubar)
        open_action.triggered.connect(self.open_dialog)

        save_action = QtWidgets.QAction("Save", menubar)
        save_action.triggered.connect(self.save_location)

        example_menu.addAction(load_kopenhagen)
        example_menu.addAction(load_cop)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)

        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle("Decide Exchange Model")
        self.show()

    def load_kopenhagen(self):
        self.load(data_file_path("kopenhagen"))

    def load_parijs(self):
        self.load(data_file_path("CoP21"))

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

        self.actor_input_control.clear()
        self.issue_input_control.clear()
        self.actor_issues.clear()
        self.position_box.clear()
        self.salience_box.clear()

        for issue, actor_issues in model.actor_issues.items():
            issue_input = self.issue_input_control.add_issue(
                issue.name, issue.lower, issue.upper
            )
            issue_input.comment = issue.comment
            self.actor_issues.issues.add(issue_input)

            for actor, actor_issue in actor_issues.items():
                if actor not in actor_inputs:
                    actor_issue = actor_issue  # type: ActorIssue
                    actor_input = self.actor_input_control.add_actor(
                        actor.name, actor_issue.power
                    )
                    actor_input.comment = actor.comment
                    actor_inputs[actor] = actor_input

                    self.actor_issues.actors.add(actor_input)
                else:
                    actor_input = actor_inputs[actor]

                self.actor_issues.add_actor_issue(
                    actor_input, issue_input, actor_issue, silence=True
                )

        self.position_box.redraw()
        self.salience_box.redraw()
        self.position_box.update_choices()
        self.salience_box.update_choices()

    def save(self, filename):

        with open(filename, "w") as file:

            for actor in self.actor_input_control.items.values():
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

            for issue in self.issue_input_control.items.values():
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

            for actor_id, actor_issues in self.actor_issues.items.items():

                for issue_id, actor_issue in actor_issues.items():
                    actor_issue = actor_issue  # type: ActorIssueInput

                    file.write(
                        "\t".join(
                            [
                                esc("#D"),
                                esc(actor_issue.actor.name),
                                esc(actor_issue.issue.name),
                                str(actor_issue.position),
                                str(actor_issue.salience),
                                str(actor_issue.power),
                                "\n",
                            ]
                        )
                    )

        open_file(filename)


def main():
    sys.excepthook = exception_hook

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    input_window = InputWindow()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
