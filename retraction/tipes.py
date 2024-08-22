from enum import Enum, auto
from typing import cast

from retraction.error import InternalError


class Type(Enum):
    BYTE_T = 0
    CHAR_T = 1
    INT_T = 2
    CARD_T = 3
    BYTE_POINTER_T = 4
    CHAR_POINTER_T = 5
    INT_POINTER_T = 6
    CARD_POINTER_T = 7
    BYTE_ARRAY_T = 8
    CHAR_ARRAY_T = 9
    INT_ARRAY_T = 10
    CARD_ARRAY_T = 11
    RECORD_T = 12
    BOOL_INTERNAL_T = 13
    VOID_T = 14


FUNDAMENAL_TYPES = {
    Type.BYTE_T,
    Type.CHAR_T,
    Type.INT_T,
    Type.CARD_T,
}

SIZE_BYTES = [
    1,  # BYTE_T
    1,  # CHAR_T
    2,  # INT_T
    2,  # CARD_T
    1,  # BYTE_POINTER_T
    1,  # CHAR_POINTER_T
    2,  # INT_POINTER_T
    2,  # CARD_POINTER_T
    1,  # BYTE_ARRAY_T
    1,  # CHAR_ARRAY_T
    2,  # INT_ARRAY_T
    2,  # CARD_ARRAY_T
    0,  # RECORD_T
    1,  # BOOL_INTERNAL_T
]

CAST_PRIORITY = [
    1,  # BYTE_T
    1,  # CHAR_T
    2,  # INT_T
    3,  # CARD_T
    1,  # BYTE_POINTER_T
    1,  # CHAR_POINTER_T
    2,  # INT_POINTER_T
    3,  # CARD_POINTER_T
    1,  # BYTE_ARRAY_T
    1,  # CHAR_ARRAY_T
    2,  # INT_ARRAY_T
    3,  # CARD_ARRAY_T
    0,  # RECORD_T
    1,  # BOOL_INTERNAL_T
]


class RecordType:
    def __init__(self, name: str):
        self.name = name
        self.fields: list[tuple[str, Type]] = []
        self.lookup: dict[str, int] = {}

    def add_field(self, name: str, field_type: Type):
        # Fields must be fundamental types
        if not field_type in FUNDAMENAL_TYPES:
            raise ValueError(
                f"Field {name} must be a fundamental type, not {field_type}"
            )
        self.fields.append((name, field_type))
        self.lookup[name] = len(self.fields) - 1

    def get_field(self, name: str) -> tuple[str, Type]:
        return self.fields[self.lookup[name]]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RecordType):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f"RecordType({self.name}, {self.fields})"


# class ArrayTipe:
#     def __init__(self, element_type: Type, length: int | None = None):
#         # Arrays must be of fundamental types
#         if not element_type in FUNDAMENAL_TYPES:
#             raise ValueError(
#                 f"Array elements must be a fundamental type, not {element_type}"
#             )
#         self.element_tipe = element_type
#         self.length = length

#     def __eq__(self, other: object) -> bool:
#         if not isinstance(other, ArrayTipe):
#             return False
#         return self.element_type == other.element_type and self.length == other.length

#     def __repr__(self) -> str:
#         return f"ArrayType({self.element_tipe}, {self.length})"


# class BaseTipe(Enum):
#     BYTE = auto()
#     CHAR = auto()
#     INT = auto()
#     CARD = auto()
#     BOOL_INTERNAL = auto()
#     POINTER = auto()
#     RECORD = auto()
#     ARRAY = auto()

#     def is_fundamental(self):
#         return self in {BaseTipe.BYTE, BaseTipe.CHAR, BaseTipe.INT, BaseTipe.CARD}


# class Tipe:
#     def __init__(self, base_tipe: BaseTipe, size_bytes: int):
#         self.base_tipe = base_tipe
#         self.size_bytes = size_bytes

#     def is_fundamental(self):
#         return self.base_tipe.is_fundamental()

#     def is_pointer(self):
#         return self.base_tipe == BaseTipe.POINTER

#     def is_record(self):
#         return self.base_tipe == BaseTipe.RECORD

#     def is_array(self):
#         return self.base_tipe == BaseTipe.ARRAY

#     def cast_priority(self):
#         if self.base_tipe == BaseTipe.BYTE:
#             return 1
#         elif self.base_tipe == BaseTipe.CHAR:
#             return 1
#         elif self.base_tipe == BaseTipe.INT:
#             return 2
#         elif self.base_tipe == BaseTipe.CARD:
#             return 3
#         elif self.base_tipe == BaseTipe.BOOL_INTERNAL:
#             return 1
#         elif self.base_tipe == BaseTipe.POINTER:
#             return 3
#         elif self.base_tipe == BaseTipe.RECORD:
#             raise InternalError("Cannot cast record type")
#         elif self.base_tipe == BaseTipe.ARRAY:
#             return 3
#         else:
#             raise ValueError(f"Unknown base tipe {self.base_tipe}")

#     def __eq__(self, other: object) -> bool:
#         if not isinstance(other, Tipe):
#             return False
#         return self.base_tipe == other.base_tipe

#     def __repr__(self) -> str:
#         return f"Tipe({self.base_tipe})"


# # Fundamental types.
# BYTE_TIPE = Tipe(BaseTipe.BYTE, 1)
# CHAR_TIPE = Tipe(BaseTipe.CHAR, 1)
# INT_TIPE = Tipe(BaseTipe.INT, 2)
# CARD_TIPE = Tipe(BaseTipe.CARD, 2)

# # There is no boolean type in the language, but we need a way to represent
# # boolean values in the compiler and vm for intermediate values of relational
# # operations.
# BOOL_INTERNAL_TIPE = Tipe(BaseTipe.BOOL_INTERNAL)


# class RecordTipe(Tipe):
#     def __init__(self, name: str):
#         super().__init__(BaseTipe.RECORD)
#         self.name = name
#         self.fields: list[tuple[str, BaseTipe]] = []
#         self.lookup: dict[str, int] = {}

#     def add_field(self, name: str, field_tipe: BaseTipe):
#         # Fields must be fundamental types
#         if not field_tipe.is_fundamental():
#             raise ValueError(
#                 f"Field {name} must be a fundamental type, not {field_tipe}"
#             )
#         self.fields.append((name, field_tipe))
#         self.lookup[name] = len(self.fields) - 1

#     def get_field(self, name: str) -> tuple[str, BaseTipe]:
#         return self.fields[self.lookup[name]]

#     def __eq__(self, other: object) -> bool:
#         other = cast(RecordTipe, other)
#         if not super().__eq__(other):
#             return False
#         return self.name == other.name

#     def __repr__(self) -> str:
#         return f"RecordTipe({self.name})"


# class ArrayTipe(Tipe):
#     def __init__(self, element_tipe: BaseTipe, length: int | None = None):
#         # Arrays must be of fundamental types
#         if not element_tipe.is_fundamental():
#             raise ValueError(
#                 f"Array elements must be a fundamental type, not {element_tipe}"
#             )
#         super().__init__(BaseTipe.ARRAY)
#         self.element_tipe = element_tipe
#         self.length = length

#     def __eq__(self, other: object) -> bool:
#         if not isinstance(other, ArrayTipe):
#             return False
#         if not super().__eq__(other):
#             return False
#         return self.element_tipe == other.element_tipe and self.length == other.length

#     def __repr__(self) -> str:
#         return f"ArrayTipe({self.element_tipe}, {self.length})"


# class PointerTipe(Tipe):
#     def __init__(self, reference_tipe: BaseTipe):
#         # Pointers must point to fundamental types
#         if not reference_tipe.is_fundamental():
#             raise ValueError(
#                 f"Pointers must point to fundamental types, not {reference_tipe}"
#             )
#         super().__init__(BaseTipe.POINTER)
#         self.reference_tipe = reference_tipe

#     def __eq__(self, other: object) -> bool:
#         if not isinstance(other, PointerTipe):
#             return False
#         if not super().__eq__(other):
#             return False
#         return self.reference_tipe == other.reference_tipe

#     def __repr__(self) -> str:
#         return f"PointerTipe({self.reference_tipe})"


# class Routine:
#     def __init__(
#         self,
#         name: str,
#         entry_point: int,
#         param_tipes: list[Tipe],
#         return_tipe: Tipe | None,
#     ):
#         self.name = name
#         self.entry_point = entry_point
#         self.param_tipes = param_tipes
#         self.return_tipe = return_tipe

#     def __repr__(self) -> str:
#         return f"Routine({self.name}, {self.entry_point}, {self.param_tipes}, {self.return_tipe})"

#     def is_function(self):
#         return self.return_tipe is not None

#     def is_procedure(self):
#         return self.return_tipe is None
