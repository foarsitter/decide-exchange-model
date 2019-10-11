from collections import defaultdict
from decimal import Decimal

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QListWidgetItem

from decide.data.types import ActorIssue
from decide.qt.inputwindow import signals
from decide.qt.inputwindow.models import (
    ActorInputModel,
    IssueInputModel,
    ActorIssueInputModel,
)
from decide.qt.mainwindow.helpers import DoubleInput, clear_layout, normalize


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

            self.add_button = QtWidgets.QPushButton("Add")

            container.addWidget(self.add_button)

            self.layout_container.addLayout(container)
            self.layout_container.addWidget(self.add_button)

        self.setLayout(self.layout_container)

        self.actor_issues = {}

        self._row_pointer = 0

    def clear(self):
        clear_layout(self.grid_layout)

        self.actor_issues = {}
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

    def delete_row_callback(self):

        sending_button = self.sender()  # type: QtWidgets.QPushButton

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

    def __init__(self):
        super(ActorWidget, self).__init__("Actors")
        self.add_heading()
        self.add_button.clicked.connect(self.add_action)

    def add_heading(self):
        self.add_row("Actor", "Power")

    def add_delete_button(self):

        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row_callback)
        delete_button.setObjectName("actor-" + str(self._row_pointer))

        return delete_button

    def add_power_input(self, actor_input, power):

        power_input = DoubleInput()
        power_input.setValue(power)
        power_input.valueChanged.connect(actor_input.set_power)

        actor_input.widgets['power'] = power_input

        return power_input

    def add_comment_button(self):

        comment_button = QtWidgets.QPushButton("Comment")
        comment_button.clicked.connect(self.comment_window)
        comment_button.setObjectName("actor-" + str(self._row_pointer))

        return comment_button

    def add_name_input(self, actor_input, name):
        name_input = QtWidgets.QLineEdit()
        name_input.setText(name)
        name_input.textChanged.connect(actor_input.set_name)

        actor_input.widgets['id'] = name_input

        return name_input

    def add_actor(self, name=None, power=Decimal(0.0)):

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
    def create_actor_name():

        ActorWidget.NEW_ACTOR_POINTER += 1

        return "Actor-{}".format(ActorWidget.NEW_ACTOR_POINTER)

    def add_action(self):
        a = self.add_actor()

        signals.actor_created.send(a)

    def delete_row_callback(self):
        row = super().delete_row_callback()

        signals.actor_deleted.send(row)

    def comment_window(self):
        sending_button = self.sender()  # type: QtWidgets.QPushButton

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.actor_issues[row]

        text, ok_pressed = QtWidgets.QInputDialog.getMultiLineText(
            self, "Comment", "Comment", obj.comment
        )

        if ok_pressed and text != "":
            obj.comment = text


class IssueWidget(BoxLayout):
    key = "issue_box"

    NEW_ISSUE_POINTER = 0

    def __init__(self):
        super(IssueWidget, self).__init__("Issues")
        self.add_heading()
        self.add_button.clicked.connect(self.add_action)

    @staticmethod
    def create_issue_name():

        IssueWidget.NEW_ISSUE_POINTER += 1

        return "Issue-{}".format(IssueWidget.NEW_ISSUE_POINTER)

    def add_heading(self):
        self.add_row("Issue", "Lower", "Upper")

    def add_delete_button(self):

        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row_callback)
        delete_button.setObjectName("issue-" + str(self._row_pointer))

        return delete_button

    def add_comment_button(self):

        comment_button = QtWidgets.QPushButton("Comment")
        comment_button.clicked.connect(self.comment_window)
        comment_button.setObjectName("issue-" + str(self._row_pointer))

        return comment_button

    def add_issue(self, name=None, lower=Decimal(0), upper=Decimal(100.0)):
        if not name:
            name = self.create_issue_name()
        issue_input = IssueInputModel(name, lower, upper)
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

        issue_input.widgets['name'] = name_input
        issue_input.widgets['lower'] = lower_input
        issue_input.widgets['upper'] = upper_input

        comment_button = self.add_comment_button()
        delete_button = self.add_delete_button()

        self.actor_issues[issue_input.id] = issue_input

        self.add_row(
            name_input, lower_input, upper_input, comment_button, delete_button
        )

        return issue_input

    def add_action(self):
        issue = self.add_issue()

        signals.issue_created.send(issue)

    def delete_row_callback(self):
        row = super().delete_row_callback()

        signals.issue_deleted.send(row)

    def comment_window(self):
        sending_button = self.sender()  # type: QtWidgets.QPushButton

        row = int(sending_button.objectName().split("-")[-1])

        obj = self.actor_issues[row]

        text, ok_pressed = QtWidgets.QInputDialog.getMultiLineText(
            self, "Comment", "Comment", obj.comment
        )

        if ok_pressed and text != "":
            obj.comment = text


class ActorIssueWidget(BoxLayout):
    """
    The ActorIssueBox is an hidden box behind the scenes, so there is a single point of truth
    """

    def add_heading(self):
        pass

    def __init__(self, actor_box: ActorWidget, issue_box: IssueWidget):
        super(ActorIssueWidget, self).__init__("Hidden Box")

        self.actor_box = actor_box
        self.issue_box = issue_box

        self.actor_issues = defaultdict(lambda: dict())

        self.actors = set()
        self.issues = set()

    def clear(self):
        super(ActorIssueWidget, self).clear()
        self.actor_issues = defaultdict(lambda: dict())

        self.actors = set()
        self.issues = set()

    def delete_actor(self, row):
        if row in self.actors:
            self.actors.remove(row)

            for issue in self.issue_box.actor_issues.values():
                if row.id in self.actor_issues and issue.id in self.actor_issues[row.id]:
                    del self.actor_issues[row.id][issue.id]

    def delete_issue(self, row):
        if row in self.issues:
            self.issues.remove(row)
            for actor in self.actor_box.actor_issues.values():
                del self.actor_issues[actor.id][row.id]

    def add_issue(self, value):
        self.issues.add(value)
        for actor in self.actor_box.actor_issues.values():
            self.add_actor_issue(actor, value)

    def add_actor(self, value):
        self.actors.add(value)
        for issue in self.issue_box.actor_issues.values():
            self.add_actor_issue(value, issue)

    def add_actor_issue(
            self,
            actor: ActorInputModel,
            issue: IssueInputModel,
            actor_issue: ActorIssue = None,
    ):

        actor_issue_input = ActorIssueInputModel(actor, issue)
        actor_issue_input.id = self._row_pointer

        self.actor_issues[actor.id][issue.id] = actor_issue_input

        if actor_issue:
            actor_issue_input.set_position(actor_issue.position, silence=True)
            actor_issue_input.set_salience(actor_issue.salience, silence=True)
            actor_issue_input.set_power(actor_issue.power, silence=True)

        self._row_pointer += 1


class PositionSalienceWidget(QtWidgets.QWidget):
    def __init__(self, actor_issue_box: ActorIssueWidget, *args, **kwargs):
        super(PositionSalienceWidget, self).__init__(*args, **kwargs)

        self.actor_issue_box = actor_issue_box

        self._row_pointer = 0

        self.choices_list_widget = QtWidgets.QListWidget(self)
        self.choices_list_widget.setMaximumHeight(100)
        self.choices_list_widget.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        self.choices_list_widget.itemSelectionChanged.connect(self.redraw)

        self.choices_list_widget_items = {}

        self.container = QtWidgets.QVBoxLayout(self)
        self.container.addWidget(self.choices_list_widget)

        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_widget = QtWidgets.QWidget()
        self.scroll_area.setWidget(self.scroll_area_widget)

        self.grid_layout = QtWidgets.QGridLayout(self.scroll_area_widget)
        self.grid_layout.setAlignment(QtCore.Qt.AlignTop)

        self.container.addWidget(self.scroll_area)

        self.add_heading()

    def clear(self):

        self._row_pointer = 0
        clear_layout(self.grid_layout)

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
                        actor.id in self.actor_issue_box.actor_issues
                        and issue.id in self.actor_issue_box.actor_issues[actor.id]
                ):
                    actor_issue = self.actor_issue_box.actor_issues[actor.id][
                        issue.id
                    ]  # type: ActorIssueInputModel

                    self.draw_actor_issue(actor_issue)

    def draw_actor_issue(self, actor_issue: ActorIssueInputModel):
        raise NotImplementedError

    def add_choice(self, key, value):

        item = QListWidgetItem(self.choices_list_widget)
        item.setText(value)

        self.choices_list_widget_items[key] = item

        self.choices_list_widget.addItem(item)

        self.choices_list_widget.sortItems()

    def delete_choice(self, key):

        item = self.choices_list_widget_items[key]  # type: QtWidgets.QListWidgetItem

        self.choices_list_widget.takeItem(self.choices_list_widget.row(item))

    def update_choice(self, key, value):

        item = self.choices_list_widget_items[key]

        item.setText(value)

    def set_choices(self, choices):

        self.choices_list_widget.clear()

        for item in choices:
            if item.name != "":
                item_widget = QtWidgets.QListWidgetItem(self.choices_list_widget)
                item_widget.setText(item.name)
                self.choices_list_widget_items[item.id] = item_widget
                self.choices_list_widget.addItem(item_widget)

        self.choices_list_widget.sortItems()

    def is_selected(self, value):

        items = self.choices_list_widget.selectedItems()

        if len(items) == 0:
            return True

        for item in items:
            if item.text() == value:
                return True

        return False


class PositionWidget(PositionSalienceWidget):
    def add_heading(self):
        self.add_row("Issue", "Actor", "Power", "Position")

    def draw_actor_issue(self, actor_issue: ActorIssueInputModel):
        if self.is_selected(actor_issue.issue.name):
            position = DoubleInput()
            position.setValue(actor_issue.position)
            position.valueChanged.connect(actor_issue.set_position)

            actor_issue.widgets['position'] = position

            self.add_row(
                QtWidgets.QLabel(actor_issue.issue.name),
                QtWidgets.QLabel(actor_issue.actor.name),
                QtWidgets.QLabel(normalize(actor_issue.actor.power)),
                position,
            )


class SalienceWidget(PositionSalienceWidget):
    def add_heading(self):
        self.add_row("Actor", "Issue", "Power", "Position", "Salience")

    def draw_actor_issue(self, actor_issue: ActorIssueInputModel):
        if self.is_selected(actor_issue.actor.name):
            salience = DoubleInput()
            salience.setValue(actor_issue.salience)
            salience.valueChanged.connect(actor_issue.set_salience)

            self.add_row(
                QtWidgets.QLabel(actor_issue.actor.name),
                QtWidgets.QLabel(actor_issue.issue.name),
                QtWidgets.QLabel(normalize(actor_issue.actor.power)),
                QtWidgets.QLabel(normalize(actor_issue.position)),
                salience,
            )
