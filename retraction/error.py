class RetractionError(Exception):
    def __init__(self, msg):
        super().__init__()
        self.msg = msg


class SyntaxError(RetractionError):
    def __init__(self, msg):
        super().__init__(msg)


class InternalError(RetractionError):
    def __init__(self, msg):
        super().__init__(msg)


class RuntimeError(RetractionError):
    def __init__(self, msg):
        super().__init__(msg)
