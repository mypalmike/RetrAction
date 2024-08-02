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
    AND = auto()
    OR = auto()
    XOR = auto()
    OP_BIT_AND = auto()
    OP_BIT_OR = auto()
    OP_BIT_XOR = auto()
    UNARY_MINUS = auto()
    CONSTANT = auto()
    # FUND_IDENT = auto()
    # PTR_IDENT = auto()
    # PTR_IDENT_VALUE = auto()
    # REC_IDENT = auto()
    # REC_IDENT_VAL = auto()
    ROUTINE_CALL = auto()
    RETURN = auto()
    EXIT = auto()


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
