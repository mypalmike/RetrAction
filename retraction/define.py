class DefineStack:
    def __init__(self):
        self.lookup: list[dict[str, str]] = [{}]

    def push(self):
        self.lookup.append({})

    def pop(self):
        self.lookup.pop()

    def reset_to_global(self):
        self.lookup = self.lookup[:1]

    def set(self, name: str, value: str):
        self.lookup[-1][name] = value

    def get(self, name: str) -> str | None:
        for scope in reversed(self.lookup):
            val = scope.get(name)
            if val is not None:
                return val
        return None
