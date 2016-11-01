class Actor:
    def __init__(self, name: str) -> None:
        self.Name = name.lower()

    def __str__(self):
        return self.Name
