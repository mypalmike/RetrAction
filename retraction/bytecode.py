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
    DUP = 21
    POP = 22
    NUMERICAL_CONSTANT = 23
    LOAD_VARIABLE = 24
    STORE_VARIABLE = 25
    ROUTINE_CALL = 26
    ROUTINE_POSTLUDE = 27
    RETURN = 28
    CAST = 29
    NOP = 30
    # TODO: Remove when not needed
    DEVPRINT = 200


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
