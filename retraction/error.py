class RetractionError(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + repr(self.msg) + ")"


class SyntaxError(RetractionError):
    def __init__(self, msg):
        super().__init__(msg)


class IdentifierError(RetractionError):
    def __init__(self, msg):
        super().__init__(msg)


class InternalError(RetractionError):
    def __init__(self, msg):
        super().__init__(msg)


class RuntimeError(RetractionError):
    def __init__(self, msg):
        super().__init__(msg)
