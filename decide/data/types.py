import typesystem
from decide.model import base
from typesystem import ValidationError


class CSVColumn:
    starts_with = None


class Comment(CSVColumn, typesystem.Schema):
    starts_with = "#/"
    description = typesystem.Text()

    def __hash__(self):
        return hash(self.description)

    def __eq__(self, other):
        if isinstance(other, Comment):
            return self.description == other.description

        return NotImplemented


class IssueDescription(CSVColumn, typesystem.Schema):
    starts_with = "#O"
    description = typesystem.Text()

    def __hash__(self):
        return hash(self.description)

    def __eq__(self, other):
        if isinstance(other, IssueDescription):
            return self.description == other.description

        return NotImplemented


class PartialActor(CSVColumn, typesystem.Schema):
    starts_with = "#A"
    id = typesystem.String()
    fullname = typesystem.String(allow_blank=True)
    comment = typesystem.String(allow_blank=True)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):

        if isinstance(other, str):
            return self.id == other

        if isinstance(other, PartialActor):
            return self.id == other.id

        return NotImplemented

    def __lt__(self, other):
        return self.id < other.id

    def as_model_object(self):

        actor = base.Actor(self.id, self.fullname)

        return actor


class Actor(PartialActor):
    power = typesystem.Float(minimum=0, maximum=100)


class PartialIssue(CSVColumn, typesystem.Schema):
    """
    An issue as referenced in the csv data file
    """
    starts_with = "#P"
    name = typesystem.String()
    description = typesystem.Text(
        allow_blank=True, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super(PartialIssue, self).__init__(*args, **kwargs)
        self.lower = None
        self.upper = None

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):

        if isinstance(other, str):
            return self.name == other

        if isinstance(other, PartialIssue):
            return self.name == other.name

        return NotImplemented

    def __lt__(self, other):
        return self.name < other.name

    def validate_interval(self):

        if self.lower > self.upper:
            raise ValidationError(key='interval', text='lower needs to be less then upper')

    def as_model_object(self):

        issue = base.Issue(self.name, self.lower, self.upper)

        return issue


class Issue(PartialIssue):
    """
    An issue from the InputWindow
    """
    name = typesystem.String()
    upper = typesystem.Float()
    lower = typesystem.Float()
    comment = typesystem.String(allow_blank=True)


class IssuePosition(CSVColumn, typesystem.Schema):
    """
    #M;Issue ID;position;meaning;
    """

    starts_with = "#M"
    issue = typesystem.String()
    position = typesystem.Number()
    description = typesystem.Text(allow_blank=True, allow_null=True)

    def __hash__(self):
        return hash(self.issue)

    def __eq__(self, other):
        if isinstance(other, PartialIssue):
            return self.issue == other.issue and self.position == other.position

        return NotImplemented


class ActorIssue(CSVColumn, typesystem.Schema):
    """
    #A;actor;issue;position;salience;power
    """

    starts_with = "#D"
    actor = typesystem.String()
    issue = typesystem.String()
    position = typesystem.Decimal()
    salience = typesystem.Decimal(minimum=0, maximum=100)
    power = typesystem.Decimal(minimum=0, maximum=100)
    comment = typesystem.Text(allow_blank=True, allow_null=True)

    def __str__(self):
        return str(self.actor) + "-" + str(self.issue)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):

        if isinstance(other, PartialIssue):
            return self.__str__() == other.__str__()

        return NotImplemented

    def __lt__(self, other):
        return self.issue.__lt__(other.issue)

    def validate_position(self, issue: PartialIssue):

        issue.validate_interval()

        if not issue.lower <= self.position <= issue.upper:
            raise ValidationError(
                key='position',
                text='exceeds the issue interval of {}-{}'.format(issue.lower, issue.upper)
            )
