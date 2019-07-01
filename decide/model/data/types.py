import typesystem


class CSVColumn:
    starts_with = None
    comment = typesystem.Text(allow_null=True)


class Comment(CSVColumn, typesystem.Schema):
    starts_with = '#/'
    description = typesystem.Text()

    def __hash__(self):
        return hash(self.description)

    def __eq__(self, other):

        if isinstance(other, Comment):
            return self.description == other.description

        return NotImplemented


class IssueDescription(CSVColumn, typesystem.Schema):
    starts_with = '#O'
    description = typesystem.Text()

    def __hash__(self):
        return hash(self.description)

    def __eq__(self, other):

        if isinstance(other, IssueDescription):
            return self.description == other.description

        return NotImplemented


class Actor(CSVColumn, typesystem.Schema):
    starts_with = '#A'
    id = typesystem.String(max_length=100)
    fullname = typesystem.String(max_length=100)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):

        if isinstance(other, Actor):
            return self.id == other.id

        return NotImplemented


class Issue(CSVColumn, typesystem.Schema):
    starts_with = '#P'
    name = typesystem.String(max_length=100)
    description = typesystem.String(max_length=100)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):

        if isinstance(other, Issue):
            return self.name == other.name

        return NotImplemented


class IssuePosition(CSVColumn, typesystem.Schema):
    """
    #M;Issue ID;position;meaning;
    """
    starts_with = '#M'
    issue = typesystem.String(max_length=100)
    name = typesystem.String(max_length=100)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):

        if isinstance(other, Issue):
            return self.name == other.name

        return NotImplemented


class ActorIssue(CSVColumn, typesystem.Schema):
    """
    #A;actor;issue;position;salience;power
    """
    starts_with = '#D'
    actor = typesystem.String(max_length=100)
    issue = typesystem.String(max_length=100)
    position = typesystem.Decimal()
    salience = typesystem.Decimal(minimum=0, maximum=1)
    power = typesystem.Decimal(minimum=0, maximum=1)
    comment = typesystem.Text(allow_blank=True, allow_null=True)

    def __str__(self):
        return str(self.actor) + '-' + str(self.issue)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):

        if isinstance(other, Issue):
            return self.__str__() == other.__str__()

        return NotImplemented
