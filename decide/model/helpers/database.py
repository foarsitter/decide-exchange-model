import datetime

import peewee

try:
    # try to use the Cython version
    from playhouse.sqlite_ext import CSqliteExtDatabase

    connection = CSqliteExtDatabase(
        None,
        c_extensions=True,
        pragmas=(
            ("cache_size", -1024 * 1024),  # 64MB page-cache.
            ("journal_mode", "wal"),  # Use WAL-mode (you should always use this!).
        ),
    )
except:
    connection = peewee.SqliteDatabase("decide")


class DictionaryIndexMixin:
    hash_field = "id"

    def __hash__(self):
        return hash(self.get_hash_field())

    def __eq__(self, other):

        if hasattr(other, "get_hash_field"):
            return self.get_hash_field() == other.get_hash_field()

        if self.get_hash_field() == other:
            return True

        if other is None:
            return False

        raise NotImplementedError()

    def get_hash_field(self):
        return getattr(self, self.__class__.hash_field)


class BaseModel(peewee.Model):
    class Meta:
        database = connection


class DataSet(DictionaryIndexMixin, BaseModel):
    name = peewee.CharField()
    hash_field = "name"


class Actor(DictionaryIndexMixin, BaseModel):
    name = peewee.CharField()
    key = peewee.CharField()

    data_set = peewee.ForeignKeyField(DataSet)

    hash_field = "key"


class Issue(DictionaryIndexMixin, BaseModel):
    name = peewee.CharField()
    key = peewee.CharField()

    lower = peewee.DecimalField()
    upper = peewee.DecimalField()

    data_set = peewee.ForeignKeyField(DataSet)

    hash_field = "key"


class ModelRun(BaseModel):
    started_at = peewee.DateTimeField(default=datetime.datetime.now)
    finished_at = peewee.DateTimeField(null=True)

    p = peewee.DecimalField(max_digits=3, decimal_places=2)
    iterations = peewee.IntegerField()
    repetitions = peewee.IntegerField()

    data_set = peewee.ForeignKeyField(DataSet)


class Repetition(DictionaryIndexMixin, BaseModel):
    """
    A repetition for a data set
    """

    pointer = peewee.IntegerField()

    hash_field = "pointer"

    model_run = peewee.ForeignKeyField(ModelRun)


class Iteration(DictionaryIndexMixin, BaseModel):
    """
    A iteration inside a repetition
    """

    pointer = peewee.IntegerField()
    repetition = peewee.ForeignKeyField(Repetition)

    hash_field = "pointer"


class ActorIssue(BaseModel):
    """
    Snapshot of a position of an actor on an issue
    """

    issue = peewee.ForeignKeyField(Issue)
    actor = peewee.ForeignKeyField(Actor)

    power = peewee.DecimalField(max_digits=20, decimal_places=15)
    position = peewee.DecimalField(max_digits=20, decimal_places=15)
    salience = peewee.DecimalField(max_digits=20, decimal_places=15)

    iteration = peewee.ForeignKeyField(Iteration)

    type = peewee.CharField(choices=("before", "after"), default="before")

    def __str__(self):
        return "{issue} {actor} {position}".format(
            issue=self.issue.name, actor=self.actor.name, position=self.position
        )


class ExchangeActor(BaseModel):
    actor = peewee.ForeignKeyField(Actor)
    supply_issue = peewee.ForeignKeyField(Issue)
    demand_issue = peewee.ForeignKeyField(Issue)

    x = peewee.DecimalField(max_digits=20, decimal_places=15)  # begin position
    y = peewee.DecimalField(max_digits=20, decimal_places=15)  # end position
    eu = peewee.DecimalField(
        max_digits=20, decimal_places=15
    )  # expected utility or gain

    demand_position = peewee.DecimalField(max_digits=20, decimal_places=15)

    # shortcut
    other_actor = peewee.ForeignKeyField("self", null=True)

    @property
    def move(self):
        return abs(self.x - self.y)


class Exchange(BaseModel):
    i = peewee.ForeignKeyField(ExchangeActor)
    j = peewee.ForeignKeyField(ExchangeActor)

    iteration = peewee.ForeignKeyField(Iteration)


class Externality(BaseModel):
    actor = peewee.ForeignKeyField(Actor)

    exchange = peewee.ForeignKeyField(Exchange)

    supply = peewee.ForeignKeyField(Issue)
    demand = peewee.ForeignKeyField(Issue)

    own = peewee.DecimalField(max_digits=20, decimal_places=15, null=True)
    inner_positive = peewee.DecimalField(max_digits=20, decimal_places=15, null=True)
    inner_negative = peewee.DecimalField(max_digits=20, decimal_places=15, null=True)
    outer_positive = peewee.DecimalField(max_digits=20, decimal_places=15, null=True)
    outer_negative = peewee.DecimalField(max_digits=20, decimal_places=15, null=True)

    iteration = peewee.ForeignKeyField(Iteration)


class Manager:
    """
    Helper for manage the state of the database.
    """

    tables = [
        DataSet,
        Actor,
        Issue,
        ModelRun,
        ActorIssue,
        Repetition,
        Iteration,
        Exchange,
        ExchangeActor,
        Externality,
    ]

    def __init__(self, database_path):
        self.database_path = database_path

    def init_database(self):
        connection.init(self.database_path)

    def create_tables(self):
        connection.create_tables(self.tables, safe=True)

    def delete_tables(self):
        connection.drop_tables(self.tables)

    def __call__(self):
        """
        Single instance only
        """
        return self
