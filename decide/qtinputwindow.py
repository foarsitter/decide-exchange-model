import os
import sys
from collections import defaultdict

from PyQt5 import QtWidgets, QtCore


def open_file(path):
    import subprocess, os
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', path))
    elif os.name == 'nt':
        os.startfile(path)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', path))

def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


class Observer:
    key = 'AbstractObserver'

    def notify_add(self, observer, value):
        raise NotImplementedError

    def notify_delete(self, observer, row):
        raise NotImplementedError


class Observable:

    def __init__(self):

        self.observers = []

    def notify_add(self, value):

        for observer in self.observers:
            observer.notify_add(self, value)

    def notify_delete(self, row):

        for observer in self.observers:
            observer.notify_delete(self, row)

    def register(self, obj):
        self.observers.append(obj)


class ActorInput(Observable):

    def __init__(self, name):
        super().__init__()
        self.id = None
        self._name = name
        self.key = 'actor_input'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        print('actor name to ' + self._name)
        self.notify_add(value)

    def set_name(self, value):
        self.name = value


class IssueInput(Observable):

    def __init__(self, name, lower, upper):
        super().__init__()
        self.id = None
        self._name = name
        self._lower = lower
        self._upper = upper
        self.key = 'issue_input'

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
        self._name = value
        print('issue name to ' + self._name)
        self.notify_add(value)

    def set_name(self, value):
        self.name = value


class ActorIssueInput(Observer):

    def notify_add(self, key=None, value=None):
        print('notify')

        print(self.actor.name)
        print(self.issue.name)

        self.actor_input.setText(self.actor.name)
        self.issue_input.setText(self.issue.name)

    def __init__(self, layout, actor: ActorInput, issue: IssueInput, position, salience, power):
        super().__init__()
        self.id = None
        self.layout = layout

        self.actor = actor
        self.issue = issue

        self.actor.register(self)
        self.issue.register(self)

        self.position = position
        self.salience = salience
        self.power = power

        self.actor_input = QtWidgets.QLabel(actor.name)
        self.issue_input = QtWidgets.QLabel(issue.name)

        self.position_input = QtWidgets.QDoubleSpinBox()
        self.salience_input = QtWidgets.QDoubleSpinBox()
        self.power_input = QtWidgets.QDoubleSpinBox()


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
            self.add_button = QtWidgets.QPushButton('Add')
            self.layout_container.addWidget(self.add_button)

        self.setLayout(self.layout_container)

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

    def delete_row(self):

        sending_button = self.sender()  # type: QtWidgets.QPushButton

        print(sending_button.objectName())

        row = int(sending_button.objectName().split('-')[-1])

        obj = self.items[row]
        del self.items[row]

        for column in range(self.grid_layout.count()):

            item = self.grid_layout.itemAtPosition(row, column)
            if item:
                item.widget().deleteLater()
            self.grid_layout.removeItem(item)

        return obj


class ActorBox(BoxLayout, Observable):
    key = 'actor_box'

    def __init__(self):
        super(ActorBox, self).__init__('Actors')

        self.add_button.clicked.connect(self.add_action)

    def add_heading(self):
        self.add_row('Actor')

    def add_actor(self):
        actor_input = ActorInput('')
        actor_input.id = self._row_pointer

        name = QtWidgets.QLineEdit()
        # call the setter on a change
        name.textChanged.connect(actor_input.set_name)

        delete_button = QtWidgets.QPushButton('Delete')
        delete_button.clicked.connect(self.delete_row)
        delete_button.setObjectName('actor-' + str(self._row_pointer))

        self.items[actor_input.id] = actor_input

        self.add_row(name, delete_button)

        return actor_input

    def add_action(self):
        a = self.add_actor()

        self.notify_add(a)

    def delete_row(self):
        row = super().delete_row()
        self.notify_delete(row)


class IssueBox(BoxLayout, Observable):
    key = 'issue_box'

    def __init__(self):
        super(IssueBox, self).__init__('Issues')

        self.add_button.clicked.connect(self.add_action)

    def add_heading(self):
        self.add_row('Issue', 'Lower', 'Upper')

    def add_issue(self):
        issue_input = IssueInput('', '0.00', '100.00')
        issue_input.id = self._row_pointer
        lower = QtWidgets.QDoubleSpinBox()
        upper = QtWidgets.QDoubleSpinBox()

        name = QtWidgets.QLineEdit()
        # call the setter on a change
        name.textChanged.connect(issue_input.set_name)

        delete_button = QtWidgets.QPushButton('Delete')
        delete_button.clicked.connect(self.delete_row)
        delete_button.setObjectName('issue-' + str(self._row_pointer))

        self.items[issue_input.id] = issue_input

        self.add_row(name, lower, upper, delete_button)

        return issue_input

    def add_action(self):
        issue = self.add_issue()

        self.notify_add(issue)

    def delete_row(self):
        row = super().delete_row()

        self.notify_delete(row)


class ActorIssueBox(BoxLayout, Observer):

    def notify_delete(self, observer, row):

        if observer.key == IssueBox.key:
            for actor in self.actor_box.items.values():
                item = self.items[actor.id][row.id]
                self.delete_row(item.id)
                del self.items[actor.id][row.id]

        if observer.key == ActorBox.key:
            for issue in self.issue_box.items.values():
                item = self.items[row.id][issue.id]
                self.delete_row(item.id)
                del self.items[row.id][issue.id]

    def notify_add(self, observer: Observer, value):

        if observer.key == IssueBox.key:

            for actor in self.actor_box.items.values():
                self.add_actor_issue(actor, value)

        if observer.key == ActorBox.key:
            for issue in self.issue_box.items.values():
                self.add_actor_issue(value, issue)

    def __init__(self, actor_box: ActorBox, issue_box: IssueBox):
        super(ActorIssueBox, self).__init__('Actor issues')
        self.add_button.setText('Save')
        self.add_button.clicked.connect(self.add_action)
        self.actor_box = actor_box
        self.issue_box = issue_box

        self.actor_box.register(self)
        self.issue_box.register(self)
        self.issue_box.register(self)

        self.items = defaultdict(lambda: dict())

    def add_action(self):

        with open("test.csv", 'w') as file:

            for actor in self.actor_box.items.values():
                file.write(';'.join(['#A', actor.name, os.linesep]))

            for issue in self.issue_box.items.values():
                file.write(';'.join(['#P', issue.name, issue.lower, issue.upper, os.linesep]))

            for actor_id, actor_issues in self.items.items():

                for issue_id, actor_issue in actor_issues.items():
                    actor_issue = actor_issue  # type: ActorIssueInput

                    file.write(';'.join(
                        ['#M', actor_issue.actor.name, actor_issue.issue.name, str(actor_issue.position_input.value()),
                         str(actor_issue.salience_input.value()), str(actor_issue.power_input.value()), os.linesep]))

        open_file('test.csv')

    def add_heading(self):
        self.add_row('Actor', 'Issue', 'Power', 'Salience', 'Position')

    def add_actor_issue(self, actor: ActorInput, issue: IssueInput):

        actor_issue = ActorIssueInput(self, actor, issue, 0, 0, 0)
        actor_issue.id = self._row_pointer

        self.items[actor.id][issue.id] = actor_issue

        self.add_row(actor_issue.actor_input, actor_issue.issue_input, actor_issue.position_input,
                     actor_issue.salience_input, actor_issue.power_input)

    def delete_row(self, row):
        for column in range(self.grid_layout.count()):

            item = self.grid_layout.itemAtPosition(row, column)

            if item:
                item.widget().deleteLater()
            self.grid_layout.removeItem(item)


class InputWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(InputWindow, self).__init__()

        main = QtWidgets.QHBoxLayout()
        left = QtWidgets.QVBoxLayout()
        right = QtWidgets.QVBoxLayout()

        actor_input_control = ActorBox()
        actor_input_control.add_heading()

        issue_input_control = IssueBox()
        issue_input_control.add_heading()

        actor_issue_control = ActorIssueBox(actor_input_control, issue_input_control)
        actor_issue_control.add_heading()

        left.addWidget(actor_input_control)
        left.addWidget(issue_input_control)

        right.addWidget(actor_issue_control)

        main.addLayout(left)
        main.addLayout(right)

        q = QtWidgets.QWidget()
        q.setLayout(main)

        self.setCentralWidget(q)

        self.setGeometry(300, 300, 1024, 768)
        self.setWindowTitle('Decide Exchange Model')
        self.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    ex = InputWindow()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
