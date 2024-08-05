from retraction.symtab import SymbolTable
from retraction.bytecode import ByteCode, ByteCodeOp


# Action calling conventions:
#
# Address     nth byte of parameters-------
# A register  1st
# X register  2nd
# Y register  3rd
# $A3         4th
# $A4         5th
# :
# :
# $AF         16th

# Mixing numerical types table:
#       BYTE    INT    CARD
# BYTE  BYTE    INT    CARD
# INT   INT     INT    CARD
# CARD  CARD    CARD   CARD

# Unary minus implies INT
# # @ implies CARD
# TECHNICAL NOTE: using the '*', '/' or 'MOD' operand results
# in an INT type, so processing of very large CARD values (>
# 32767) will not work p


class ByteCodeGen:
    def __init__(self, symbol_table: SymbolTable, start_addr: int = 0):
        self.code: list[ByteCode] = []
        self.addr = start_addr

    def emit_routine_call(self, identifier, params):
        self.code.append(ByteCode(ByteCodeOp.ROUTINE_CALL, identifier))

    def emit_return(self):
        self.code.append(ByteCode(ByteCodeOp.RETURN))

    def emit_add(self):
        self.code.append(ByteCode(ByteCodeOp.ADD))

    def emit_subtract(self):
        self.code.append(ByteCode(ByteCodeOp.SUBTRACT))

    def emit_multiply(self):
        self.code.append(ByteCode(ByteCodeOp.MULTIPLY))

    def emit_divide(self):
        self.code.append(ByteCode(ByteCodeOp.DIVIDE))

    def emit_mod(self):
        self.code.append(ByteCode(ByteCodeOp.MOD))

    def emit_lsh(self):
        self.code.append(ByteCode(ByteCodeOp.LSH))

    def emit_rsh(self):
        self.code.append(ByteCode(ByteCodeOp.RSH))

    def emit_eq(self):
        self.code.append(ByteCode(ByteCodeOp.OP_EQ))

    def emit_ne(self):
        self.code.append(ByteCode(ByteCodeOp.OP_NE))

    def emit_gt(self):
        self.code.append(ByteCode(ByteCodeOp.OP_GT))

    def emit_ge(self):
        self.code.append(ByteCode(ByteCodeOp.OP_GE))

    def emit_lt(self):
        self.code.append(ByteCode(ByteCodeOp.OP_LT))

    def emit_le(self):
        self.code.append(ByteCode(ByteCodeOp.OP_LE))

    def emit_xor(self):
        self.code.append(ByteCode(ByteCodeOp.XOR))

    def emit_bit_and(self):
        self.code.append(ByteCode(ByteCodeOp.OP_BIT_AND))

    def emit_bit_or(self):
        self.code.append(ByteCode(ByteCodeOp.OP_BIT_OR))

    def emit_bit_xor(self):
        self.code.append(ByteCode(ByteCodeOp.OP_BIT_XOR))

    def emit_unary_minus(self):
        self.code.append(ByteCode(ByteCodeOp.UNARY_MINUS))

    def emit_jump_if_false(self, addr: int | None = None) -> ByteCode:
        byte_code = ByteCode(ByteCodeOp.JUMP_IF_FALSE, addr)
        self.code.append(byte_code)
        return byte_code

    def emit_jump(self, addr: int | None = None) -> ByteCode:
        byte_code = ByteCode(ByteCodeOp.JUMP, addr)
        self.code.append(byte_code)
        return byte_code

    def emit_pop(self):
        self.code.append(ByteCode(ByteCodeOp.POP))

    def emit_constant(self, const_index):
        self.code.append(ByteCode(ByteCodeOp.CONSTANT, const_index))

    def emit_devprint(self):
        self.code.append(ByteCode(ByteCodeOp.OP_DEVPRINT))

    def get_next_addr(self):
        return len(self.code)
