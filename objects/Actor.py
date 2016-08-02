class Actor:
    # Id = ""
    # Name = ""
    # Human = ""

    def __init__(self, name: str) -> None:
        self.Name = name

    def __str__(self):
        return self.Name
