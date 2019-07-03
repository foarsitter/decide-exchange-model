from typing import List, Dict

from decide.data import types
from decide.data.reader import InputDataFile
from decide.model.base import AbstractModel


class ModelFactory:
    """
    The goal of this object is to initiate a model object with the correct begin state
    """

    def __init__(
            self,
            date_file: InputDataFile,
            actor_whitelist: List[str] = None,
            issue_whitelist: List[str] = None,
            *args,
            **kwargs
    ):
        super(ModelFactory, self).__init__(*args, **kwargs)
        self.data_file = date_file
        self.actor_whitelist = actor_whitelist
        self.issue_whitelist = issue_whitelist

    def filter_actors(self) -> Dict[str, types.Actor]:

        if not self.actor_whitelist or len(self.actor_whitelist) == 0:
            return self.data_file.actors

        return {x: y for x, y in self.data_file.actors.items() if y.id in self.actor_whitelist}

    def filter_issues(self) -> Dict[str, types.Issue]:

        if not self.issue_whitelist or len(self.issue_whitelist) == 0:
            return self.data_file.issues

        return {x: y for x, y in self.data_file.issues.items() if y.name in self.issue_whitelist}

    def filter_actor_issues(self, actors: Dict[str, types.Actor], issues: Dict[str, types.Issue]):

        actor_issues = []

        for actor_issue in self.data_file.actor_issues.values():

            if actor_issue.actor in actors and actor_issue.issue in issues:
                actor_issues.append(actor_issue)

        return actor_issues

    def create(self, *args, model_klass=AbstractModel, **kwargs):

        model = model_klass(*args, **kwargs)

        filtered_actors = self.filter_actors()
        filtered_issues = self.filter_issues()

        filtered_actor_issues = self.filter_actor_issues(filtered_actors, filtered_issues)

        for actor in filtered_actors.values():
            model.add_actor(actor.id, actor.fullname)

        for issue in filtered_issues.values():
            model_issue = model.add_issue(issue.name, issue.description)
            model_issue.lower = issue.lower
            model_issue.upper = issue.upper

            model_issue.calculate_delta()
            model_issue.calculate_step_size()

        for actor_issue in filtered_actor_issues:
            model.add_actor_issue(
                actor=actor_issue.actor,
                issue=actor_issue.issue,
                position=actor_issue.position,
                salience=actor_issue.salience,
                power=actor_issue.power
            )

        return model

    def __call__(self, *args, **kwargs):
        return self.create(*args, **kwargs)
