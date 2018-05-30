import sys
import uuid

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot


def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


class BaseInputControl(QtWidgets.QHBoxLayout):

    def __init__(self, *args, **kwargs):
        super(BaseInputControl, self).__init__(*args, **kwargs)

        self.uuid = uuid.uuid4()

    def attach(self):
        raise NotImplementedError

    def connect(self, obj):
        raise NotImplementedError

    def values(self):
        raise NotImplementedError


class ActorInputControl(BaseInputControl):

    def __init__(self):
        super(ActorInputControl, self).__init__()
        self.name_input = QtWidgets.QLineEdit()

    def attach(self):
        self.addWidget(self.name_input)

    def connect(self, obj):
        self.name_input.editingFinished.connect(obj)

    def values(self):
        name = self.name_input.text()
        return {'name': name, 'uuid': self.uuid}

    @staticmethod
    def heading():
        return ['Name']


class IssueInputControl(BaseInputControl):

    def __init__(self):
        super(IssueInputControl, self).__init__()

        self.name_input = QtWidgets.QLineEdit()
        self.lower_input = QtWidgets.QLineEdit()
        self.upper_input = QtWidgets.QLineEdit()

        self.lower_input.setText(str(0))
        self.upper_input.setText(str(100))

    def connect(self, obj):
        self.name_input.editingFinished.connect(obj)
        self.lower_input.editingFinished.connect(obj)
        self.upper_input.editingFinished.connect(obj)

    def attach(self):
        self.addWidget(self.name_input)
        self.addWidget(self.lower_input)
        self.addWidget(self.upper_input)

    @staticmethod
    def heading():
        return ['Name', 'Lower (min)', 'Upper (max)']

    def values(self):
        return {
            'name': self.name_input.text(),
            'lower': self.lower_input.text(),
            'upper': self.upper_input.text(),
            'uuid': self.uuid
        }


class ActorIssueInputControl(BaseInputControl):

    def connect(self, obj):
        pass

    def values(self):
        pass

    def __init__(self):
        super(ActorIssueInputControl, self).__init__()
        self.actor_input_control = None
        self.issue_input_control = None

        self.layout = QtWidgets.QGridLayout()

        self.actor_issues = {}

    def register(self, obj):
        self.linked_input_controls.append(obj)

    def attach(self):
        self.addLayout(self.layout)

    @staticmethod
    def heading():
        return ['Actor', 'Issue', 'Position', 'Salience', 'Power']

    @pyqtSlot()
    def update_layout(self):

        clear_layout(self.layout)

        issues = self.issue_input_control.values()
        actors = self.actor_input_control.values()

        row = 0

        for issue in issues:
            for actor in actors:
                self.layout.addWidget(QtWidgets.QLabel(actor['name']), row, 0)
                self.layout.addWidget(QtWidgets.QLabel(issue['name']), row, 1)
                self.layout.addWidget(QtWidgets.QDoubleSpinBox(), row, 2)
                self.layout.addWidget(QtWidgets.QDoubleSpinBox(), row, 3)
                self.layout.addWidget(QtWidgets.QDoubleSpinBox(), row, 4)
                row += 1


class DynamicInputControlList(QtWidgets.QVBoxLayout):
    """
    A plus button
    rows with a certain widget
    A delete button per row
    """

    updated = pyqtSignal()

    def __init__(self, input_control_class, actor_issues_input_control: ActorIssueInputControl):
        super(DynamicInputControlList, self).__init__()

        self.add_button = QtWidgets.QPushButton('add')
        self.add_button.clicked.connect(self.add_action)

        self.input_control_class = input_control_class
        self.rows = {}
        self.input_controls = {}
        self.row_container = QtWidgets.QVBoxLayout()
        self.actor_issues_input_control = actor_issues_input_control

    def attach(self):
        self.add_heading()
        self.addLayout(self.row_container)
        self.addWidget(self.add_button)

        self.updated.connect(self.actor_issues_input_control.update_layout)

    def add_heading(self):

        heading = self.input_control_class.heading()
        labels = QtWidgets.QHBoxLayout()

        for x in heading:
            labels.addWidget(QtWidgets.QLabel(x))

        self.addLayout(labels)

    def add_action(self):
        self.add_row()
        self.updated.emit()

    def add_row(self):

        layout = QtWidgets.QHBoxLayout()

        input_control = self.input_control_class()
        input_control.attach()
        input_control.connect(self.actor_issues_input_control.update_layout)

        id = str(uuid.uuid4())

        self.input_controls[id] = input_control

        layout.addLayout(input_control)
        layout.setObjectName('layout_{}'.format(id))
        layout.addWidget(self.delete_button(id))

        self.rows[id] = layout

        self.row_container.addLayout(layout)

    def delete_button(self, object_name):

        button = QtWidgets.QPushButton('delete')
        button.clicked.connect(self.delete_action)
        button.setObjectName(object_name)

        return button

    def delete_action(self):

        obj = self.sender()

        self.delete_row(obj.objectName())

    def delete_row(self, object_name):

        if object_name in self.rows:
            layout = self.rows[object_name]
            clear_layout(layout)
            self.row_container.removeItem(layout)
            del self.rows[object_name]

    def values(self):
        values = []
        for key, value in self.input_controls.items():
            values.append(value.values())

        return values


class InputWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(InputWindow, self).__init__()

        main = QtWidgets.QHBoxLayout()
        left = QtWidgets.QVBoxLayout()
        right = ActorIssueInputControl()
        right.attach()

        main.addLayout(left)
        main.addLayout(right)

        actor_layout = DynamicInputControlList(ActorInputControl, right)
        actor_layout.attach()

        issue_layout = DynamicInputControlList(IssueInputControl, right)
        issue_layout.attach()

        right.actor_input_control = actor_layout
        right.issue_input_control = issue_layout

        left.addLayout(actor_layout)
        left.addLayout(issue_layout)

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
