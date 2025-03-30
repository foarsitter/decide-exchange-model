from collections import defaultdict
from decimal import Decimal
from typing import NoReturn

from PyQt6 import QtCore
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtWidgets import QGroupBox
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QListWidget
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from decide.data.types import ActorIssue
from decide.qt.inputwindow import signals
from decide.qt.inputwindow.models import ActorInputModel
from decide.qt.inputwindow.models import ActorIssueInputModel
from decide.qt.inputwindow.models import IssueInputModel
from decide.qt.mainwindow.helpers import DoubleInput
from decide.qt.mainwindow.helpers import clear_layout
from decide.qt.mainwindow.helpers import normalize


class BoxLayout(QGroupBox):
    def __init__(self, title: str, btn=True) -> None:
        super().__init__(title)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.grid_layout = QGridLayout(self.scroll_area_widget)
        self.grid_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.layout_container = QVBoxLayout()
        self.layout_container.addWidget(self.scroll_area)

        if btn:
            container = QHBoxLayout()

            self.add_button = QPushButton("Add")

            container.addWidget(self.add_button)

            self.layout_container.addLayout(container)
            self.layout_container.addWidget(self.add_button)

        self.setLayout(self.layout_container)

        self.actor_issues = {}

        self._row_pointer = 0

    def clear(self) -> None:
        clear_layout(self.grid_layout)

        self.actor_issues = {}
        self._row_pointer = 0

    def add_heading(self) -> NoReturn:
        raise NotImplementedError

    def add_row(self, *args, pointer=None):
        row = pointer if pointer else self._row_pointer

        for column, arg in enumerate(args):
            if isinstance(arg, str):
                arg = QLabel(arg)

            self.grid_layout.addWidget(arg, row, column)

        self._row_pointer += 1

        return row

    def delete_row_callback(self):
        sending_button: QPushButton = self.sender()

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.actor_issues[row]

        del self.actor_issues[row]

        for column in range(self.grid_layout.count()):
            item = self.grid_layout.itemAtPosition(row, column)
            if item:
                item.widget().deleteLater()
            self.grid_layout.removeItem(item)

        return obj


class ActorWidget(BoxLayout):
    key = "actor_box"

    NEW_ACTOR_POINTER = 0

    def __init__(self) -> None:
        super().__init__("Actors")
        self.add_heading()
        self.add_button.clicked.connect(self.add_action)

    def add_heading(self) -> None:
        self.add_row("Actor", "Power")

    def add_delete_button(self) -> QPushButton:
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row_callback)
        delete_button.setObjectName("actor-" + str(self._row_pointer))

        return delete_button

    def add_power_input(self, actor_input: ActorInputModel, power) -> DoubleInput:
        power_input = DoubleInput()
        power_input.setValue(power)
        power_input.valueChanged.connect(actor_input.set_power)

        actor_input.widgets["power"] = power_input

        return power_input

    def add_comment_button(self) -> QPushButton:
        comment_button = QPushButton("Comment")
        comment_button.clicked.connect(self.comment_window)
        comment_button.setObjectName("actor-" + str(self._row_pointer))

        return comment_button

    def add_name_input(self, actor_input: ActorInputModel, name) -> QLineEdit:
        name_input = QLineEdit()
        name_input.setText(name)
        name_input.textChanged.connect(actor_input.set_name)

        actor_input.widgets["id"] = name_input

        return name_input

    def add_actor(self, name=None, power: Decimal = Decimal("0.0")) -> ActorInputModel:
        if not name:
            name = self.create_actor_name()

        actor_input = ActorInputModel(name, power)
        actor_input.id = self._row_pointer

        name_input = self.add_name_input(actor_input, name)
        power_input = self.add_power_input(actor_input, power)
        delete_button = self.add_delete_button()
        comment_button = self.add_comment_button()

        self.actor_issues[actor_input.id] = actor_input

        self.add_row(name_input, power_input, comment_button, delete_button)

        return actor_input

    @staticmethod
    def create_actor_name() -> str:
        ActorWidget.NEW_ACTOR_POINTER += 1

        return f"Actor-{ActorWidget.NEW_ACTOR_POINTER}"

    def add_action(self) -> None:
        a = self.add_actor()

        signals.actor_created.send(a)

    def delete_row_callback(self) -> None:
        row = super().delete_row_callback()

        signals.actor_deleted.send(row)

    def comment_window(self) -> None:
        sending_button: QPushButton = self.sender()

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.actor_issues[row]

        text, ok_pressed = QInputDialog.getMultiLineText(
            self,
            "Comment",
            "Comment",
            obj.comment,
        )

        if ok_pressed and text != "":
            obj.comment = text


class IssueWidget(BoxLayout):
    key = "issue_box"

    NEW_ISSUE_POINTER = 0

    def __init__(self) -> None:
        super().__init__("Issues")
        self.add_heading()
        self.add_button.clicked.connect(self.add_action)

    @staticmethod
    def create_issue_name() -> str:
        IssueWidget.NEW_ISSUE_POINTER += 1

        return f"Issue-{IssueWidget.NEW_ISSUE_POINTER}"

    def add_heading(self) -> None:
        self.add_row("Issue", "Lower", "Upper")

    def add_delete_button(self) -> QPushButton:
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row_callback)
        delete_button.setObjectName("issue-" + str(self._row_pointer))

        return delete_button

    def add_comment_button(self) -> QPushButton:
        comment_button = QPushButton("Comment")
        comment_button.clicked.connect(self.comment_window)
        comment_button.setObjectName("issue-" + str(self._row_pointer))

        return comment_button

    def add_issue(
        self, name=None, lower: Decimal = Decimal(0), upper: Decimal = Decimal("100.0")
    ) -> IssueInputModel:
        if not name:
            name = self.create_issue_name()
        issue_input = IssueInputModel(name, lower, upper)
        issue_input.id = self._row_pointer

        lower_input = DoubleInput()
        lower_input.setValue(lower)

        upper_input = DoubleInput()
        upper_input.setValue(upper)

        name_input = QLineEdit()
        name_input.setText(name)

        # call the setter on a change
        name_input.textChanged.connect(issue_input.set_name)
        lower_input.valueChanged.connect(issue_input.set_lower)
        upper_input.valueChanged.connect(issue_input.set_upper)

        issue_input.widgets["name"] = name_input
        issue_input.widgets["lower"] = lower_input
        issue_input.widgets["upper"] = upper_input

        comment_button = self.add_comment_button()
        delete_button = self.add_delete_button()

        self.actor_issues[issue_input.id] = issue_input

        self.add_row(
            name_input,
            lower_input,
            upper_input,
            comment_button,
            delete_button,
        )

        return issue_input

    def add_action(self) -> None:
        issue = self.add_issue()

        signals.issue_created.send(issue)

    def delete_row_callback(self) -> None:
        row = super().delete_row_callback()

        signals.issue_deleted.send(row)

    def comment_window(self) -> None:
        sending_button = self.sender()  # type: QtWidgets.QPushButton

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.actor_issues[row]

        text, ok_pressed = QInputDialog.getMultiLineText(
            self,
            "Comment",
            "Comment",
            obj.comment,
        )

        if ok_pressed and text != "":
            obj.comment = text


class ActorIssueWidget(BoxLayout):
    """The ActorIssueBox is an hidden box behind the scenes, so there is a single point of truth."""

    def add_heading(self) -> None:
        pass

    def __init__(self, actor_box: ActorWidget, issue_box: IssueWidget) -> None:
        super().__init__("Hidden Box")

        self.actor_box = actor_box
        self.issue_box = issue_box

        self.actor_issues = defaultdict(dict)

        self.actors = set()
        self.issues = set()

    def clear(self) -> None:
        super().clear()
        self.actor_issues = defaultdict(dict)

        self.actors = set()
        self.issues = set()

    def delete_actor(self, row) -> None:
        if row in self.actors:
            self.actors.remove(row)

            for issue in self.issue_box.actor_issues.values():
                if row.id in self.actor_issues and issue.id in self.actor_issues[row.id]:
                    del self.actor_issues[row.id][issue.id]

    def delete_issue(self, row) -> None:
        if row in self.issues:
            self.issues.remove(row)
            for actor in self.actor_box.actor_issues.values():
                del self.actor_issues[actor.id][row.id]

    def add_issue(self, value) -> None:
        self.issues.add(value)
        for actor in self.actor_box.actor_issues.values():
            self.add_actor_issue(actor, value)

    def add_actor(self, value) -> None:
        self.actors.add(value)
        for issue in self.issue_box.actor_issues.values():
            self.add_actor_issue(value, issue)

    def add_actor_issue(
        self,
        actor: ActorInputModel,
        issue: IssueInputModel,
        actor_issue: ActorIssue = None,
    ) -> None:
        actor_issue_input = ActorIssueInputModel(actor, issue)
        actor_issue_input.id = self._row_pointer

        self.actor_issues[actor.id][issue.id] = actor_issue_input

        if actor_issue:
            actor_issue_input.set_position(actor_issue.position, silence=True)
            actor_issue_input.set_salience(actor_issue.salience, silence=True)
            actor_issue_input.set_power(actor_issue.power, silence=True)

        self._row_pointer += 1


class PositionSalienceWidget(QWidget):
    def __init__(self, actor_issue_box: ActorIssueWidget, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.actor_issue_box = actor_issue_box

        self._row_pointer = 0

        self.choices_list_widget = QListWidget(self)
        self.choices_list_widget.setMaximumHeight(100)
        self.choices_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.choices_list_widget.itemSelectionChanged.connect(self.redraw)

        self.choices_list_widget_items = {}

        self.container = QVBoxLayout(self)
        self.container.addWidget(self.choices_list_widget)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.grid_layout = QGridLayout(self.scroll_area_widget)
        self.grid_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        self.container.addWidget(self.scroll_area)

        self.add_heading()

    def clear(self) -> None:
        self._row_pointer = 0
        clear_layout(self.grid_layout)

    def add_heading(self) -> NoReturn:
        raise NotImplementedError

    def add_row(self, *args, pointer=None):
        row = pointer if pointer else self._row_pointer

        for column, arg in enumerate(args):
            if isinstance(arg, str):
                arg = QLabel(arg)

            self.grid_layout.addWidget(arg, row, column)

        self._row_pointer += 1

        return row

    def redraw(self) -> None:
        clear_layout(self.grid_layout)

        self.add_heading()

        for issue in self.actor_issue_box.issues:
            for actor in self.actor_issue_box.actors:
                if (
                    actor.id in self.actor_issue_box.actor_issues
                    and issue.id in self.actor_issue_box.actor_issues[actor.id]
                ):
                    actor_issue = self.actor_issue_box.actor_issues[actor.id][issue.id]  # type: ActorIssueInputModel

                    self.draw_actor_issue(actor_issue)

    def draw_actor_issue(self, actor_issue: ActorIssueInputModel) -> NoReturn:
        raise NotImplementedError

    def add_choice(self, key, value) -> None:
        item = QListWidgetItem(self.choices_list_widget)
        item.setText(value)

        self.choices_list_widget_items[key] = item

        self.choices_list_widget.addItem(item)

        self.choices_list_widget.sortItems()

    def delete_choice(self, key) -> None:
        item = self.choices_list_widget_items[key]  # type: QListWidgetItem

        self.choices_list_widget.takeItem(self.choices_list_widget.row(item))

    def update_choice(self, key, value) -> None:
        item = self.choices_list_widget_items[key]

        item.setText(value)

    def set_choices(self, choices) -> None:
        self.choices_list_widget.clear()

        for item in choices:
            if item.name != "":
                item_widget = QListWidgetItem(self.choices_list_widget)
                item_widget.setText(item.name)
                self.choices_list_widget_items[item.id] = item_widget
                self.choices_list_widget.addItem(item_widget)

        self.choices_list_widget.sortItems()

    def is_selected(self, value: str) -> bool:
        items = self.choices_list_widget.selectedItems()

        if len(items) == 0:
            return True

        return any(item.text() == value for item in items)


class PositionWidget(PositionSalienceWidget):
    def add_heading(self) -> None:
        self.add_row("Issue", "Actor", "Power", "Position")

    def draw_actor_issue(self, actor_issue: ActorIssueInputModel) -> None:
        if self.is_selected(actor_issue.issue.name):
            position = DoubleInput()
            position.setValue(actor_issue.position)
            position.valueChanged.connect(actor_issue.set_position)

            actor_issue.widgets["position"] = position

            self.add_row(
                QLabel(actor_issue.issue.name),
                QLabel(actor_issue.actor.name),
                QLabel(normalize(actor_issue.actor.power)),
                position,
            )


class SalienceWidget(PositionSalienceWidget):
    def add_heading(self) -> None:
        self.add_row("Actor", "Issue", "Power", "Position", "Salience")

    def draw_actor_issue(self, actor_issue: ActorIssueInputModel) -> None:
        if self.is_selected(actor_issue.actor.name):
            salience = DoubleInput()
            salience.setValue(actor_issue.salience)
            salience.valueChanged.connect(actor_issue.set_salience)

            self.add_row(
                QLabel(actor_issue.actor.name),
                QLabel(actor_issue.issue.name),
                QLabel(normalize(actor_issue.actor.power)),
                QLabel(normalize(actor_issue.position)),
                salience,
            )
