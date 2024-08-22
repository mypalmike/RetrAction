from typing import cast


from retraction.symtab import SymbolTable
from retraction.bytecode import ByteCode, ByteCodeOp, ByteCodeType
from tipes import Tipe, BaseTipe, PointerTipe


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
# 32767) will not work


class ByteCodeGen:
    def __init__(self, symbol_table: SymbolTable, start_addr: int = 0):
        self.symbol_table = symbol_table
        self.code: bytearray = bytearray()
        # self.code: list[ByteCode] = []
        self.addr = start_addr

    def append_byte(self, byte: int):
        self.code.append(byte)

    def append_short(self, short: int):
        self.code.append(short & 0xFF)
        self.code.append(short >> 8)

    def emit_routine_call(self, routine_index):
        self.append_byte(ByteCodeOp.ROUTINE_CALL)
        self.append_short(routine_index)

    def emit_return(self):
        self.append_byte(ByteCodeOp.RETURN)

    def emit_add(self):
        self.append_byte(ByteCodeOp.ADD)

    def emit_subtract(self):
        self.append_byte(ByteCodeOp.SUBTRACT)

    def emit_multiply(self):
        self.append_byte(ByteCodeOp.MULTIPLY)

    def emit_divide(self):
        self.append_byte(ByteCodeOp.DIVIDE)

    def emit_mod(self):
        self.append_byte(ByteCodeOp.MOD)

    def emit_lsh(self):
        self.code.append(ByteCode(ByteCodeOp.LSH))

    def emit_rsh(self):
        self.code.append(ByteCode(ByteCodeOp.RSH))

    def emit_eq(self):
        self.code.append(ByteCode(ByteCodeOp.EQ))

    def emit_ne(self):
        self.code.append(ByteCode(ByteCodeOp.NE))

    def emit_gt(self):
        self.code.append(ByteCode(ByteCodeOp.GT))

    def emit_ge(self):
        self.code.append(ByteCode(ByteCodeOp.GE))

    def emit_lt(self):
        self.code.append(ByteCode(ByteCodeOp.LT))

    def emit_le(self):
        self.code.append(ByteCode(ByteCodeOp.LE))

    def emit_xor(self):
        self.code.append(ByteCode(ByteCodeOp.XOR))

    def emit_bit_and(self):
        self.code.append(ByteCode(ByteCodeOp.BIT_AND))

    def emit_bit_or(self):
        self.code.append(ByteCode(ByteCodeOp.BIT_OR))

    def emit_bit_xor(self):
        self.code.append(ByteCode(ByteCodeOp.BIT_XOR))

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
        # CONSTANT,
        self.append_byte(ByteCodeOp.NUMERICAL_CONSTANT)
        constant_value = self.symbol_table.constants[const_index]
        self.append_short(constant_value)
        if isinstance(constant_value, str):
            raise NotImplementedError
        else:
            if constant_value < 256:
                self.append_byte(BaseTipe.BYTE)
            elif constant_value > -32768 and constant_value < 32768:
                self.append_byte(BaseTipe.INT)
            else:
                self.append_byte(BaseTipe.CARD)

    def emit_get_global(self, global_index):
        # GET_GLOBAL, TYPE, INDEX
        self.append_byte(ByteCodeOp.GET_GLOBAL)
        tipe = self.symbol_table.globals[global_index].var_tipe
        self.append_byte(tipe.base_tipe)
        self.append_short(global_index)

    def emit_get_addr_global(self, global_index):
        # GET_ADDR_GLOBAL, INDEX
        self.append_byte(ByteCodeOp.GET_ADDR_GLOBAL)
        self.append_short(global_index)

    def emit_get_ptr_global(self, global_index):
        # GET_PTR_GLOBAL, TYPE, INDEX
        self.append_byte(ByteCodeOp.GET_PTR_GLOBAL)
        global_obj = self.symbol_table.globals[global_index]
        tipe = global_obj.var_tipe
        if not tipe.is_pointer():
            raise ValueError(f"Global {global_obj.name} is not a pointer")
        ptr_tipe: PointerTipe = cast(PointerTipe, tipe)
        ref_tipe = ptr_tipe.reference_tipe
        self.append_byte(ref_tipe)
        self.append_short(global_index)

    def emit_set_global(self, global_index):
        self.code.append(ByteCode(ByteCodeOp.SET_GLOBAL, global_index))

    def emit_set_ptr_global(self, global_index):
        self.code.append(ByteCode(ByteCodeOp.SET_PTR_GLOBAL, global_index))

    def emit_push_param(self):
        self.code.append(ByteCode(ByteCodeOp.PUSH_PARAM))

    def emit_zero(self):
        self.code.append(ByteCode(ByteCodeOp.ZERO))

    def emit_devprint(self):
        self.code.append(ByteCode(ByteCodeOp.DEVPRINT))

    def get_next_addr(self):
        return len(self.code)
