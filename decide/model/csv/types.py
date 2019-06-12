import typesystem


class CSVColumn:
    starts_with = None
    comment = typesystem.Text(allow_null=True)


class Comment(CSVColumn, typesystem.Schema):
    starts_with = '#/'
    description = typesystem.Text()


class IssueDescription(CSVColumn, typesystem.Schema):
    starts_with = '#O'
    description = typesystem.Text()


class Actor(CSVColumn, typesystem.Schema):
    starts_with = '#A'
    id = typesystem.String(max_length=100)
    fullname = typesystem.String(max_length=100)


class Issue(CSVColumn, typesystem.Schema):
    starts_with = '#P'
    name = typesystem.String(max_length=100)
    description = typesystem.String(max_length=100)


class IssuePosition(CSVColumn, typesystem.Schema):
    """
    #M;Issue ID;position;meaning;
    """
    starts_with = '#M'
    name = typesystem.String(max_length=100)


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
