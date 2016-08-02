class ActorIssue:
    Actor = None
    Issue = None
    Id = ""
    Power = 0
    Salience = 0
    Position = 0
    Left = False

    def __init__(self, position: float, salience: float, power: float):
        self.Power = float(power)
        self.Position = float(position)
        self.Salience = float(salience)

    def is_left_to_nbs(self, nbs: float) -> bool:
        self.Left = self.Position < nbs
        return self.Left

    def __str__(self):
        return "Actor {0} on issue {1} with position={2}, salience={3}, power={4}".format(self.Actor, self.Issue,
                                                                                          self.Position, self.Salience,
                                                                                          self.Power)
