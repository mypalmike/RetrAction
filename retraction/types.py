from enum import Enum, auto
from typing import Literal, cast

from retraction.error import InternalError


class SizeBytes:
    def size_bytes(self) -> int:
        raise NotImplementedError


class FundamentalType(SizeBytes, Enum):
    BYTE_T = 0
    CHAR_T = 1
    INT_T = 2
    CARD_T = 3
    VOID_T = 4

    def size_bytes(self) -> int:
        if self == FundamentalType.BYTE_T:
            return 1
        elif self == FundamentalType.CHAR_T:
            return 1
        elif self == FundamentalType.INT_T:
            return 2
        elif self == FundamentalType.CARD_T:
            return 2
        else:
            raise InternalError(f"Invalid size for {self}")

    def cast_priority(self):
        if self == FundamentalType.BYTE_T:
            return 1
        elif self == FundamentalType.CHAR_T:
            return 1
        elif self == FundamentalType.INT_T:
            return 2
        elif self == FundamentalType.CARD_T:
            return 3
        else:
            raise InternalError(f"Invalid cast priority for {self}")


class ComplexType(SizeBytes):
    pass


class RecordType(ComplexType):
    def __init__(self, name: str):
        self.name = name
        self.fields: list[tuple[str, FundamentalType]] = (
            []
        )  # Use list rather than just a dict to preserve order
        self.lookup: dict[str, int] = {}

    def add_field(self, name: str, field_type: FundamentalType):
        self.fields.append((name, field_type))
        self.lookup[name] = len(self.fields) - 1

    def get_field(self, name: str) -> tuple[str, FundamentalType]:
        return self.fields[self.lookup[name]]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RecordType):
            return False
        return self.name == other.name

    def __repr__(self) -> str:
        return f"RecordType({self.name}, {self.fields})"

    def size_bytes(self):
        return sum(f[1].size_bytes() for f in self.fields)


class PointerType(ComplexType):
    def __init__(self, reference_type: FundamentalType | RecordType):
        self.reference_type = reference_type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PointerType):
            return False
        return self.reference_type == other.reference_type

    def __repr__(self) -> str:
        return f"PointerType({self.reference_type})"

    def size_bytes(self):
        return 2


class ArrayType(ComplexType):
    def __init__(self, element_type: FundamentalType, length: int | None):
        self.element_t = element_type
        self.length = length

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self.element_t == other.element_t and self.length == other.length

    def __repr__(self) -> str:
        return f"ArrayType({self.element_t}, {self.length})"

    def size_bytes(self):
        return self.element_t.size_bytes() * self.length


type Type = FundamentalType | ComplexType


def cast_to_fundamental(t: Type) -> FundamentalType:
    if isinstance(t, FundamentalType):
        return t

    # Type for all other types is FundamentalType.CARD_T, value is the address of the variable
    return FundamentalType.CARD_T


def binary_expression_type(t1: Type, t2: Type) -> FundamentalType:
    t1_fund = cast_to_fundamental(t1)
    t2_fund = cast_to_fundamental(t2)
    pri1, pri2 = t1_fund.cast_priority(), t2_fund.cast_priority()
    result_priority = max(pri1, pri2)
    # print(
    #     f"binary_expression_type... t1: {t1}, t2: {t2}, result_priority: {result_priority}"
    # )
    if result_priority == 1:
        return FundamentalType.BYTE_T
    elif result_priority == 2:
        return FundamentalType.INT_T
    elif result_priority == 3:
        return FundamentalType.CARD_T
    else:
        raise InternalError(f"Invalid cast priority: {result_priority}")
