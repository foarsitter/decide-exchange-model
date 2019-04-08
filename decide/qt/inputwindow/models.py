import uuid
from decimal import Decimal

from PyQt5 import QtWidgets

from decide.qt.helpers import DoubleInput
from decide.qt.inputwindow import signals


class ActorInputModel(object):
    """
    Object containing a name and power
    """

    def __init__(self, name: str, power: Decimal):
        super().__init__()
        self.id = None
        self._name = name
        self._power = power
        self._comment = ""
        self.key = "actor_input"

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
            signals.actor_changed.send(self, key='name', value=value)

    def set_power(self, value, silence=False):

        self._power = value

        if not silence:
            signals.actor_changed.send(self, key='power', value=value)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self.set_comment(value)

    def set_comment(self, value):
        self._comment = value


class IssueInputModel(object):
    """
    Object containing a name, lower and upper bounds
    """

    def __init__(self, name: str, lower: Decimal, upper: Decimal):
        super().__init__()
        self.id = None
        self._name = name
        self._lower = lower
        self._upper = upper
        self._comment = ""
        self.key = "issue_input"

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

    def set_name(self, value, silence=False):
        self._name = value

        if not silence:
            signals.issue_changed.send(self, key='name', value=value)

    def set_lower(self, value, silence=False):
        self._lower = value

        if not silence:
            signals.issue_changed.send(self, key='lower', value=value)

    def set_upper(self, value, silence=False):
        self._upper = value

        if not silence:
            signals.issue_changed.send(self, key='upper', value=value)

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, value):
        self.set_comment(value)

    def set_comment(self, value):
        self._comment = value


class ActorIssueInputModel(object):

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
        if not silence:
            signals.actor_issue_changed.send(self, key='position', value=value)

    def set_power(self, value: Decimal, silence=False):
        self._power = value
        if not silence:
            signals.actor_issue_changed.send(self, key='power', value=value)

    def set_salience(self, value: Decimal, silence=False):
        self._salience = value
        if not silence:
            signals.actor_issue_changed.send(self, key='salience', value=value)
