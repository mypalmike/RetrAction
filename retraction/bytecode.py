from enum import Enum, auto


class ByteCodeOp(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MOD = auto()
    LSH = auto()
    RSH = auto()
    OP_EQ = auto()
    OP_NE = auto()
    OP_GT = auto()
    OP_GE = auto()
    OP_LT = auto()
    OP_LE = auto()
    XOR = auto()
    OP_BIT_AND = auto()
    OP_BIT_OR = auto()
    OP_BIT_XOR = auto()
    UNARY_MINUS = auto()
    JUMP_IF_FALSE = auto()
    JUMP = auto()
    POP = auto()
    CONSTANT = auto()
    ROUTINE_CALL = auto()
    RETURN = auto()
    GET_GLOBAL = auto()
    GET_ADDR_GLOBAL = auto()
    GET_PTR_GLOBAL = auto()
    SET_GLOBAL = auto()
    SET_PTR_GLOBAL = auto()
    GET_LOCAL = auto()
    SET_LOCAL = auto()
    GET_ADDR_LOCAL = auto()
    GET_PARAM = auto()
    SET_PARAM = auto()
    GET_ADDR_PARAM = auto()
    PUSH_PARAM = auto()
    ZERO = auto()
    # TODO: Remove when not needed
    DEVPRINT = auto()


class ByteCode:
    def __init__(self, op: ByteCodeOp, value: int | None = None):
        self.op = op
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f"ByteCode {self.op.name} #{self.value}"
        return f"ByteCode {self.op.name}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ByteCode):
            return False
        return (self.value, self.op) == (other.value, other.op)
