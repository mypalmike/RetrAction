from enum import Enum, auto


class ByteCodeOp(Enum):
    BREAK = 0
    ADD = 1
    SUBTRACT = 2
    MULTIPLY = 3
    DIVIDE = 4
    MOD = 5
    LSH = 6
    RSH = 7
    EQ = 8
    NE = 9
    GT = 10
    GE = 11
    LT = 12
    LE = 13
    XOR = 14
    BIT_AND = 15
    BIT_OR = 16
    BIT_XOR = 17
    UNARY_MINUS = 18
    JUMP_IF_FALSE = 19
    JUMP = 20
    POP = 21
    NUMERICAL_CONSTANT = 22
    GET_VARIABLE = 23
    PUSH_PARAM = 24
    ROUTINE_CALL = 25
    RETURN = 26
    CAST = 27
    NOP = 28
    # GET_GLOBAL = 24
    # GET_ADDR_GLOBAL = 25
    # GET_PTR_GLOBAL = 26
    # SET_GLOBAL = 27
    # SET_PTR_GLOBAL = 28
    # GET_LOCAL = 29
    # SET_LOCAL = 30
    # GET_ADDR_LOCAL = 31
    # GET_PARAM = 32
    # SET_PARAM = 33
    # GET_ADDR_PARAM = 34
    # TODO: Remove when not needed
    DEVPRINT = 200


# class ByteCodeType(Enum):
#     BYTE = auto()
#     CHAR = auto()
#     INT = auto()
#     CARD = auto()
#     BOOL_INTERNAL = auto()
#     POINTER = auto()
#     RECORD = auto()
#     ARRAY = auto()


# class ByteCode:
#     def __init__(self, op: ByteCodeOp, value: int | None = None):
#         self.op = op
#         self.value = value

#     def __repr__(self):
#         if self.value is not None:
#             return f"ByteCode {self.op.name} #{self.value}"
#         return f"ByteCode {self.op.name}"

#     def __eq__(self, other: object) -> bool:
#         if not isinstance(other, ByteCode):
#             return False
#         return (self.value, self.op) == (other.value, other.op)


class ByteCodeVariableScope(Enum):
    GLOBAL = 0
    LOCAL = 1
    PARAM = 2
    ROUTINE_REFERENCE = 3


class ByteCodeVariableAddressMode(Enum):
    DEFAULT = 0
    POINTER = 1
    REFERENCE = 2
    OFFSET = 3
