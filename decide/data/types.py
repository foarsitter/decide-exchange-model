import typesystem
from typesystem import ValidationError

from decide.model import base


class CSVColumn:
    starts_with = None


class Comment(CSVColumn, typesystem.Schema):
    starts_with = "#/"
    description = typesystem.Text()

    def __hash__(self) -> int:
        return hash(self.description)

    def __eq__(self, other) -> bool:
        if isinstance(other, Comment):
            return self.description == other.description

        raise NotImplementedError


class IssueDescription(CSVColumn, typesystem.Schema):
    starts_with = "#O"
    description = typesystem.Text()

    def __hash__(self) -> int:
        return hash(self.description)

    def __eq__(self, other) -> bool:
        if isinstance(other, IssueDescription):
            return self.description == other.description

        raise NotImplementedError


class PartialActor(CSVColumn, typesystem.Schema):
    starts_with = "#A"
    id = typesystem.String()
    fullname = typesystem.String(allow_blank=True)
    comment = typesystem.String(allow_blank=True)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.id == other

        if isinstance(other, PartialActor):
            return self.id == other.id

        raise NotImplementedError

    def __lt__(self, other):
        return self.id < other.id

    def as_model_object(self) -> "Actor":
        return base.Actor(self.id, self.fullname)


class Actor(PartialActor):
    power = typesystem.Float(minimum=0, maximum=100)


class PartialIssue(CSVColumn, typesystem.Schema):
    """An issue as referenced in the csv data file."""

    starts_with = "#P"
    name = typesystem.String()
    description = typesystem.Text(allow_blank=True, allow_null=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.lower = None
        self.upper = None

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.name == other

        if isinstance(other, PartialIssue):
            return self.name == other.name

        raise NotImplementedError

    def __lt__(self, other):
        return self.name < other.name

    def validate_interval(self) -> None:
        if self.lower > self.upper:
            raise ValidationError(
                key="interval",
                text="lower needs to be less then upper",
            )

    def as_model_object(self) -> "Issue":
        return base.Issue(self.name, self.lower, self.upper)


class Issue(PartialIssue):
    """An issue from the InputWindow."""

    name = typesystem.String()
    upper = typesystem.Float()
    lower = typesystem.Float()
    comment = typesystem.String(allow_blank=True)


class IssuePosition(CSVColumn, typesystem.Schema):
    """#M;Issue ID;position;meaning;"""

    starts_with = "#M"
    issue = typesystem.String()
    position = typesystem.Number()
    description = typesystem.Text(allow_blank=True, allow_null=True)

    def __hash__(self) -> int:
        return hash(self.issue)

    def __eq__(self, other) -> bool:
        if isinstance(other, PartialIssue):
            return self.issue == other.name and self.position == other.position

        if isinstance(other, IssuePosition):
            return self.issue == other.issue and self.position == other.position
        raise NotImplementedError


class ActorIssue(CSVColumn, typesystem.Schema):
    """#A;actor;issue;position;salience;power."""

    starts_with = "#D"
    actor = typesystem.String()
    issue = typesystem.String()
    position = typesystem.Decimal()
    salience = typesystem.Decimal(minimum=0, maximum=100)
    power = typesystem.Decimal(minimum=0, maximum=100)
    comment = typesystem.Text(allow_blank=True, allow_null=True)

    def __str__(self) -> str:
        return str(self.actor) + "-" + str(self.issue)

    def __hash__(self) -> int:
        return hash(self.__str__())

    def __eq__(self, other) -> bool:
        if isinstance(other, PartialIssue):
            return self.__str__() == other.__str__()

        raise NotImplementedError

    def __lt__(self, other):
        return self.issue.__lt__(other.issue)

    def validate_position(self, issue: PartialIssue) -> None:
        issue.validate_interval()

        if not issue.lower <= self.position <= issue.upper:
            raise ValidationError(
                key="position",
                text=f"exceeds the issue interval of {issue.lower}-{issue.upper}",
            )
