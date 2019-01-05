import datetime
from collections import defaultdict
from typing import List

from decide.model import calculations
from decide.model.base import AbstractExchange
from decide.model.observers.observer import Observer, Observable
from .. import base
from ..helpers import database as db


class SQLiteObserver(Observer):
    """
    Observer to store all the data in a sqlite database
    """

    def __init__(self, observable: "Observable", output_directory: str):
        super().__init__(observable)

        self.data_set = None
        self.repetitions = {}
        self.iterations = defaultdict(lambda: {})
        self.actors = {}
        self.issues = {}
        self.model_run = None

        if not output_directory.endswith(".db") and output_directory != ":memory:":
            output_directory += "/decide-data_1.db"
            print("logging to database {}".format(output_directory))

        self.manager = db.Manager(output_directory)
        self.manager.init_database()
        self.manager.create_tables()

    def before_repetitions(self, repetitions, iterations):
        """
        Create a new data set when needed and add all the actors

        """
        # create a data set row or find existing one
        # add the Issues and Actors when they are not present
        with db.connection.atomic():
            model = self.model_ref

            data_set, created = db.DataSet.get_or_create(
                name=self.model_ref.data_set_name
            )
            self.data_set = data_set

            self.model_run = db.ModelRun.create(
                p=self.model_ref.randomized_value,
                iterations=iterations,
                repetitions=repetitions,
                data_set=data_set,
            )

            for actor in model.actors.values():  # type: base.Actor
                actor, created = db.Actor.get_or_create(
                    name=actor.name, key=actor.actor_id, data_set=data_set
                )
                self.actors[actor] = actor

            for issue in model.issues.values():  # type: base.Issue
                issue, created = db.Issue.get_or_create(
                    name=issue.name,
                    key=issue.issue_id,
                    lower=issue.lower,
                    upper=issue.upper,
                    data_set=data_set,
                )
                self.issues[issue] = issue

    def before_iterations(self, repetition):
        with db.connection.atomic():
            repetition = db.Repetition.create(
                pointer=repetition,
                model_run=self.model_run,
                p=self.model_ref.randomized_value,
            )

            self.repetitions[repetition] = repetition

    def before_loop(self, iteration: int, repetition: int):
        with db.connection.atomic():
            self._write_actor_issues(iteration, repetition)

    def after_loop(
        self, realized: List[base.AbstractExchange], iteration: int, repetition: int
    ):
        iteration = self.iterations[repetition][iteration]

        with db.connection.atomic():
            for exchange in realized:
                db_exchange = db.Exchange()
                db_exchange.i = self._create_exchange_actor(exchange.i)
                db_exchange.j = self._create_exchange_actor(exchange.j)

                if db_exchange.i.eu < 1e-10:
                    pass

                if db_exchange.j.eu < 1e-10:
                    pass

                db_exchange.iteration = iteration
                db_exchange.save()

                self._write_externalities(exchange, db_exchange)

    def end_loop(self, iteration: int, repetition: int):
        with db.connection.atomic():
            self._write_actor_issues(iteration, repetition, "after")

    def after_repetitions(self):
        self.model_run.finished_at = datetime.datetime.now()
        self.model_run.save()

    def _write_externalities(
        self, exchange: AbstractExchange, db_exchange: db.Exchange
    ):

        issue_set_key = self.model_ref.create_existing_issue_set_key(
            exchange.p, exchange.q
        )
        inner = exchange.get_inner_groups()

        for actor in self.actors:

            externality = db.Externality()
            externality.actor = actor
            externality.exchange = db_exchange
            externality.supply = db_exchange.i.supply_issue
            externality.demand = db_exchange.i.demand_issue
            externality.iteration = db_exchange.iteration

            externality_size = calculations.actor_externalities(
                str(actor.key), self.model_ref, exchange
            )

            is_inner = self.model_ref.is_inner_group_member(
                str(actor.key), inner, issue_set_key
            )

            if actor.key == exchange.i.actor.actor_id:
                externality.own = exchange.i.eu
            elif actor.key == exchange.j.actor.actor_id:
                exchange.own = exchange.j.eu
            else:
                if externality_size < 0:
                    if is_inner:
                        externality.inner_negative = externality_size
                    else:
                        externality.outer_negative = externality_size
                else:
                    if is_inner:
                        externality.inner_positive = externality_size
                    else:
                        externality.outer_positive = externality_size

            externality.save()

    def _write_actor_issues(self, iteration: int, repetition: int, _type="before"):

        with db.connection.atomic():

            repetition = self.repetitions[repetition]
            iteration, _ = db.Iteration.get_or_create(
                pointer=iteration, repetition=repetition
            )

            self.iterations[repetition][iteration] = iteration

            for (
                issue_obj,
                actors,
            ) in self.model_ref.actor_issues.items():  # type: base.ActorIssue
                for actor_obj, actor_issue in actors.items():
                    db.ActorIssue.create(
                        issue=self.issues[issue_obj.issue_id],
                        actor=self.actors[actor_obj.actor_id],
                        power=actor_issue.power,
                        salience=actor_issue.salience,
                        position=actor_issue.position,
                        iteration=iteration,
                        type=_type,
                    )

    def _create_exchange_actor(self, i: base.AbstractExchangeActor):

        exchange_actor = db.ExchangeActor()
        exchange_actor.actor = self.actors[i.actor]
        exchange_actor.supply_issue = self.issues[i.supply.issue]
        exchange_actor.demand_issue = self.issues[i.demand.issue]
        exchange_actor.eu = i.eu
        exchange_actor.x = i.supply.position
        exchange_actor.y = i.y
        exchange_actor.demand_position = i.opposite_actor.demand.position
        exchange_actor.save()

        return exchange_actor
