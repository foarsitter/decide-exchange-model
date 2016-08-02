class ActorIssue:
    # Actor = None
    # Issue = None
    # Id = ""
    # Power = 0
    # Salience = 0
    # Position = 0
    # Left = False

    def __init__(self, actor: 'Actor', position: float, salience: float, power: float):
        self.Power = float(power)
        self.Position = float(position)
        self.Salience = float(salience)
        self.Left = False
        self.Actor = actor

    def is_left_to_nbs(self, nbs: float) -> bool:
        self.Left = self.Position < nbs
        return self.Left

    def __str__(self):
        return "Actor {0} with position={1}, salience={2}, power={3}".format(self.Actor,
                                                                             self.Position, self.Salience,
                                                                             self.Power)
