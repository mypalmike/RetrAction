from enum import Enum, auto


class ByteCodeOp(Enum):
    ADD = 0
    SUBTRACT = 1
    MULTIPLY = 2
    DIVIDE = 3
    MOD = 4
    LSH = 5
    RSH = 6
    OP_EQ = 7
    OP_NE = 8
    OP_GT = 9
    OP_GE = 10
    OP_LT = 11
    OP_LE = 12
    XOR = 13
    OP_BIT_AND = 14
    OP_BIT_OR = 15
    OP_BIT_XOR = 16
    UNARY_MINUS = 17
    JUMP_IF_FALSE = 18
    JUMP = 19
    POP = 20
    CONSTANT = 21
    ROUTINE_CALL = 22
    RETURN = 23
    GET_GLOBAL = 24
    GET_ADDR_GLOBAL = 25
    GET_PTR_GLOBAL = 26
    SET_GLOBAL = 27
    SET_PTR_GLOBAL = 28
    GET_LOCAL = 29
    SET_LOCAL = 30
    GET_ADDR_LOCAL = 31
    GET_PARAM = 32
    SET_PARAM = 33
    GET_ADDR_PARAM = 34
    PUSH_PARAM = 35
    ZERO = 36  # ?
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
