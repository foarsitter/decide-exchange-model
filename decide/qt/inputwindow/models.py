import uuid
from decimal import Decimal

from PyQt5 import QtWidgets
from typesystem.base import ValidationResult

from decide.data import types
from decide.qt.inputwindow import signals
from decide.qt.mainwindow.helpers import DoubleInput


class BaseInputModel:
    type = None

    def __init__(self):
        self.elements = {}
        self.uuid = uuid.uuid4()
        self.validation_result = ValidationResult()
        self.widgets = {}
        self.stylesheets = {}

    def is_valid(self):
        self.reset_state()
        self.validation_result = self.type.validate_or_error(self.as_dict())

        if self.validation_result.error:
            self.handle_error()
            return False
        else:
            return True

    def as_dict(self):
        raise NotImplementedError

    def handle_error(self):
        for key, value in self.validation_result.error.items():
            if key in self.widgets:

                if key not in self.stylesheets:
                    self.stylesheets[key] = self.widgets[key].styleSheet()

                self.widgets[key].setStyleSheet("border: 1px solid red")
                self.widgets[key].setToolTip(self.validation_result.error[key])

    def reset_state(self):
        for key, value in self.stylesheets.items():
            self.widgets[key].setStyleSheet(value)


class ActorInputModel(BaseInputModel):
    """
    Object containing a name and power
    """

    type = types.Actor

    def __init__(self, name: str, power: Decimal):
        super().__init__()
        self.id = None
        self._name = name
        self._power = power
        self._comment = ""
        self.key = "actor_input"

    def as_dict(self):
        return {
            'id': self.name,
            'power': self.power,
            'comment': self.comment
        }

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

        if self.is_valid() and not silence:
            signals.actor_changed.send(self, key="name", value=value)

    def set_power(self, value, silence=False):
        self._power = value

        if self.is_valid() and not silence:
            signals.actor_changed.send(self, key="power", value=value)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self.set_comment(value)

    def set_comment(self, value):
        self._comment = value


class IssueInputModel(BaseInputModel):
    """
    Object containing a name, lower and upper bounds
    """

    type = types.Issue

    def __init__(self, name: str, lower: Decimal, upper: Decimal):
        super().__init__()
        self.id = None
        self._name = name
        self._lower = lower
        self._upper = upper
        self._comment = ""
        self.key = "issue_input"

    def as_dict(self):
        return {
            'name': self.name,
            'lower': self.lower,
            'upper': self.upper,
            'comment': self.comment
        }

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

    def set_name(self, value, silence=False):
        self._name = value

        if self.is_valid() and not silence:
            signals.issue_changed.send(self, key="name", value=value)

    def set_lower(self, value, silence=False):

        self._lower = value

        if self.is_valid() and not silence:
            signals.issue_changed.send(self, key="lower", value=value)

    def set_upper(self, value, silence=False):

        self._upper = value

        if self.is_valid() and not silence:
            signals.issue_changed.send(self, key="upper", value=value)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self.set_comment(value)

    def set_comment(self, value):
        self._comment = value


class ActorIssueInputModel(BaseInputModel):
    type = types.ActorIssue

    def __init__(self, actor: ActorInputModel, issue: IssueInputModel):
        super().__init__()
        self.id = None

        self.actor = actor
        self.issue = issue

        self.actor_input = QtWidgets.QLabel(actor.name)
        self.issue_input = QtWidgets.QLabel(issue.name)

        self.power_input = QtWidgets.QLabel(str(actor.power))

        self.position_input = DoubleInput()
        self.position_input.valueChanged.connect(self.set_position)

        self.salience_input = DoubleInput()

        self.meta = dict()

        self.uuid = uuid.uuid4()

        self._power = Decimal(0.0)
        self._position = Decimal(0.0)
        self._salience = Decimal(0.0)

    def as_dict(self):
        return {
            'position': self.position,
            'salience': self.salience,
            'power': self.power,
            'issue': self.issue.name,
            'actor': self.actor.name,
        }

    @property
    def position(self):
        return self._position

    @property
    def salience(self):
        return self._salience

    @property
    def power(self):
        return self._power

    def set_position(self, value: Decimal, silence=False):
        self._position = value
        if self.is_valid() and not silence:
            signals.actor_issue_changed.send(self, key="position", value=value)

    def set_power(self, value: Decimal, silence=False):
        self._power = value
        if self.is_valid() and not silence:
            signals.actor_issue_changed.send(self, key="power", value=value)

    def set_salience(self, value: Decimal, silence=False):
        self._salience = value
        if self.is_valid() and not silence:
            signals.actor_issue_changed.send(self, key="salience", value=value)
