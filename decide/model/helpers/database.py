import datetime
import os
import sqlite3

import peewee


path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..','..', '..', 'data', 'database.db'))
connection = peewee.SqliteDatabase(path)



class DictionaryIndexMixin:
    hash_field = 'id'

    def __hash__(self):
        return hash(self.get_hash_field())

    def __eq__(self, other):

        if hasattr(other, 'get_hash_field'):
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
    hash_field = 'name'


class Actor(DictionaryIndexMixin, BaseModel):
    name = peewee.CharField()
    key = peewee.CharField()

    data_set = peewee.ForeignKeyField(DataSet)

    hash_field = 'key'


class Issue(DictionaryIndexMixin, BaseModel):
    name = peewee.CharField()
    key = peewee.CharField()

    lower = peewee.DecimalField()
    upper = peewee.DecimalField()

    data_set = peewee.ForeignKeyField(DataSet)

    hash_field = 'key'


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

    hash_field = 'pointer'

    model_run = peewee.ForeignKeyField(ModelRun)


class Iteration(DictionaryIndexMixin, BaseModel):
    """
    A iteration inside a repetition
    """
    pointer = peewee.IntegerField()
    repetition = peewee.ForeignKeyField(Repetition, related_name='iterations')

    hash_field = 'pointer'


class ActorIssue(BaseModel):
    """
    Snapshot of a position of an actor on an issue
    """
    issue = peewee.ForeignKeyField(Issue)
    actor = peewee.ForeignKeyField(Actor)

    power = peewee.DecimalField(max_digits=5, decimal_places=15)
    position = peewee.DecimalField(max_digits=5, decimal_places=15)
    salience = peewee.DecimalField(max_digits=5, decimal_places=15)

    iteration = peewee.ForeignKeyField(Iteration, related_name='actor_issues')

    type = peewee.CharField(choices=('before', 'after'), default='before')

    def __str__(self):
        return '{issue} {actor} {position}' \
            .format(issue=self.issue.name,
                    actor=self.actor.name,
                    position=self.position)


class ExchangeActor(BaseModel):
    actor = peewee.ForeignKeyField(Actor)
    supply_issue = peewee.ForeignKeyField(Issue)
    demand_issue = peewee.ForeignKeyField(Issue)

    x = peewee.DecimalField(max_digits=20, decimal_places=15)  # begin position
    y = peewee.DecimalField(max_digits=20, decimal_places=15)  # end position
    eu = peewee.DecimalField(max_digits=20, decimal_places=15)  # expected utility or gain

    demand_position = peewee.DecimalField(max_digits=20, decimal_places=15)

    # shortcut
    other_actor = peewee.ForeignKeyField('self')

    @property
    def move(self):
        return abs(self.x - self.y)


class Exchange(BaseModel):
    i = peewee.ForeignKeyField(ExchangeActor)
    j = peewee.ForeignKeyField(ExchangeActor)

    iteration = peewee.ForeignKeyField(Iteration)


class Manager:
    """
    Helper for manage the state of the database.
    """
    tables = [DataSet, Actor, Issue, ModelRun, ActorIssue, Repetition, Iteration, Exchange, ExchangeActor]

    def create_tables(self):
        with connection:
            connection.create_tables(self.tables)

    def delete_tables(self):
        with connection:
            connection.drop_tables(self.tables)
