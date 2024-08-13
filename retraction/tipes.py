from enum import Enum, auto


class BaseTipe(Enum):
    BYTE = auto()
    CHAR = auto()
    INT = auto()
    CARD = auto()
    BOOL_INTERNAL = auto()
    POINTER = auto()
    RECORD = auto()
    ARRAY = auto()

    def is_fundamental(self):
        return self in {BaseTipe.BYTE, BaseTipe.CHAR, BaseTipe.INT, BaseTipe.CARD}


class Tipe:
    def __init__(self, base_tipe: BaseTipe):
        self.base_tipe = base_tipe

    def is_fundamental(self):
        return self.base_tipe.is_fundamental()

    def is_pointer(self):
        return self.base_tipe == BaseTipe.POINTER

    def is_record(self):
        return self.base_tipe == BaseTipe.RECORD

    def is_array(self):
        return self.base_tipe == BaseTipe.ARRAY

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tipe):
            return False
        return self.base_tipe == other.base_tipe


# Fundamental types.
BYTE_TIPE = Tipe(BaseTipe.BYTE)
CHAR_TIPE = Tipe(BaseTipe.CHAR)
INT_TIPE = Tipe(BaseTipe.INT)
CARD_TIPE = Tipe(BaseTipe.CARD)

# There is no boolean type in the language, but we need a way to represent
# boolean values in the compiler and vm for intermediate values of relational
# operations.
BOOL_INTERNAL_TIPE = Tipe(BaseTipe.BOOL_INTERNAL)


class RecordTipe(Tipe):
    def __init__(self, name: str):
        super().__init__(BaseTipe.RECORD)
        self.name = name
        self.fields = []
        self.lookup = {}

    def add_field(self, name: str, field_tipe: BaseTipe):
        # Fields must be fundamental types
        if not field_tipe.is_fundamental():
            raise ValueError(
                f"Field {name} must be a fundamental type, not {field_tipe}"
            )
        self.fields.append((name, field_tipe))
        self.lookup[name] = len(self.fields) - 1

    def get_field(self, name: str) -> tuple[str, BaseTipe]:
        return self.fields[self.lookup[name]]

    def __eq__(self, other: object) -> bool:
        if not super().__eq__(other):
            return False
        return self.name == other.name


class ArrayTipe(Tipe):
    def __init__(self, element_tipe: BaseTipe, length: int | None = None):
        # Arrays must be of fundamental types
        if not element_tipe.is_fundamental():
            raise ValueError(
                f"Array elements must be a fundamental type, not {element_tipe}"
            )
        super().__init__(BaseTipe.ARRAY)
        self.element_tipe = element_tipe
        self.length = length

    def __eq__(self, other: object) -> bool:
        if not super().__eq__(other):
            return False
        return self.element_tipe == other.element_tipe and self.length == other.length


class PointerTipe(Tipe):
    def __init__(self, reference_tipe: BaseTipe):
        # Pointers must point to fundamental types
        if not reference_tipe.is_fundamental():
            raise ValueError(
                f"Pointers must point to fundamental types, not {reference_tipe}"
            )
        super().__init__(BaseTipe.POINTER)
        self.reference_tipe = reference_tipe

    def __eq__(self, other: object) -> bool:
        if not super().__eq__(other):
            return False
        return self.reference_tipe == other.reference_tipe


class Routine:
    def __init__(
        self,
        name: str,
        entry_point: int,
        param_tipes: list[Tipe],
        return_tipe: Tipe | None,
    ):
        self.name = name
        self.entry_point = entry_point
        self.param_tipes = param_tipes
        self.return_tipe = return_tipe

    def __repr__(self) -> str:
        return f"Routine({self.name}, {self.entry_point}, {self.param_tipes}, {self.return_tipe})"

    def is_function(self):
        return self.return_tipe is not None

    def is_procedure(self):
        return self.return_tipe is None
