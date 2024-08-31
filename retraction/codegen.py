from typing import cast


from retraction.symtab import SymbolTable
from retraction.bytecode import (
    ByteCodeOp,
    ByteCodeVariableScope,
    ByteCodeVariableAddressMode,
)
from retraction.types import Routine, Type


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
        self.addr = start_addr

    def append_byte(self, value: int):
        value = value % 0x100
        self.code.append(value)

    def append_short(self, value: int):
        value = value % 0x10000
        self.code.append(value & 0xFF)
        self.code.append(value >> 8)

    def write_byte(self, addr: int, byte: int):
        self.code[addr] = byte

    def write_short(self, addr: int, value: int):
        value = value % 0x10000
        self.code[addr] = value & 0xFF
        self.code[addr + 1] = value >> 8

    def append(self, value_t: Type, value: int):
        if value_t == Type.BYTE_T:
            self.append_byte(value)
        elif value_t == Type.CHAR_T:
            self.append_byte(value)
        elif value_t == Type.INT_T:
            self.append_short(value)
        elif value_t == Type.CARD_T:
            self.append_short(value)
        else:
            raise ValueError(f"Invalid value type {value_t}")

    def emit_routine_call(self, routine_index: int):
        """
        Routine call bytecode:
            ROUTINE_CALL - 1 byte
            TYPE         - 1 byte
            PARAMS SIZE  - 2 bytes
            LOCALS SIZE  - 2 bytes
            ROUTINE ADDR - 2 bytes
        """
        self.append_byte(ByteCodeOp.ROUTINE_CALL.value)
        routine = self.symbol_table.routines[routine_index]
        self.append_byte(routine.return_t.value)
        self.append_short(routine.get_params_size())
        self.append_short(routine.get_locals_size())
        self.append_short(routine.entry_point)

    def emit_return(self, routine_index: int):
        """
        Return bytecode:
            RETURN - 1 byte
            TYPE   - 1 byte
        """
        self.append_byte(ByteCodeOp.RETURN.value)
        routine = self.symbol_table.routines[routine_index]
        self.append_byte(routine.return_t.value)

    def emit_binary_op(self, op: ByteCodeOp, operand1_t: Type, operand2_t: Type):
        """
        Binary operation bytecode:
            OP         - 1 byte
            OPERAND1_T - 1 byte
            OPERAND2_T - 1 byte
        """
        self.append_byte(op.value)
        self.append_byte(operand1_t.value)
        self.append_byte(operand2_t.value)

    def emit_unary_minus(self, operand_t: Type):
        """
        Unary minus bytecode:
            UNARY_MINUS - 1 byte
            OPERAND_T   - 1 byte
        """
        self.append_byte(ByteCodeOp.UNARY_MINUS.value)
        self.append_byte(operand_t.value)

    def emit_jump_if_false(self, operand_t: Type, addr: int = 0) -> int:
        """
        Returns the address of the jump target, for fixup later if needed
        Jump if false bytecode:
            JUMP_IF_FALSE - 1 byte
            OPERAND_T     - 1 byte
            ADDR          - 2 bytes
        """
        self.append_byte(ByteCodeOp.JUMP_IF_FALSE.value)
        self.append_byte(operand_t.value)
        curr_addr = len(self.code)
        self.append_short(addr)
        return curr_addr

    def emit_jump(self, addr: int = 0) -> int:
        """
        Returns the address of the jump target, for fixup later if needed
        Jump bytecode:
            JUMP - 1 byte
            ADDR - 2 bytes
        """
        self.append_byte(ByteCodeOp.JUMP.value)
        curr_addr = len(self.code)
        self.append_short(addr)
        return curr_addr

    def emit_pop(self, operand_t: Type):
        """
        Pop bytecode:
            POP - 1 byte
            OPERAND_T - 1 byte
        """
        self.append_byte(ByteCodeOp.POP.value)
        self.append_byte(operand_t.value)

    def emit_numerical_constant(self, const_index):
        """
        Constant bytecode:
            NUMERICAL_CONSTANT - 1 byte
            TYPE               - 1 byte
            VALUE              - 1 or 2 bytes
        """
        self.append_byte(ByteCodeOp.NUMERICAL_CONSTANT.value)
        constant_value = self.symbol_table.numerical_constants[const_index]
        if constant_value < 256:
            self.append_byte(Type.BYTE_T.value)
            self.append_byte(constant_value)
        elif constant_value > -32768 and constant_value < 32768:
            self.append_byte(Type.INT_T.value)
            self.append_short(constant_value)
        else:
            self.append_byte(Type.CARD_T.value)
            self.append_short(constant_value)

    def emit_local_data(self, local_index: int) -> int:
        """
        This VM bytecode does not store local data in the code stream. This method exists so
        that other code generators can use the same interface.
        """
        local_var = self.symbol_table.locals[local_index]
        return local_var.address

    def emit_global_data(self, global_index: int) -> int:
        """
        This places raw data in the code stream, and returns the address of the data.
        """
        addr = len(self.code)
        global_var = self.symbol_table.globals[global_index]
        if global_var.var_t in [Type.BYTE_T, Type.CHAR_T]:
            self.append_byte(global_var.init_opts.initial_value)
        elif global_var.var_t in [Type.INT_T, Type.CARD_T]:
            self.append_short(global_var.init_opts.initial_value)
        return addr

    def emit_get_variable(
        self,
        var_t: Type,
        var_scope: ByteCodeVariableScope,
        var_addr_mode: ByteCodeVariableAddressMode,
        address: int,
    ):
        """
        Get variable bytecode:
            GET_VARIABLE - 1 byte
            TYPE         - 1 byte
            SCOPE        - 1 byte
            ADDR_MODE    - 1 byte
            ADDR         - 2 bytes
        """
        self.append_byte(ByteCodeOp.GET_VARIABLE.value)
        self.append_byte(var_t.value)
        self.append_byte(var_scope.value)
        self.append_byte(var_addr_mode.value)
        self.append_short(address)

    # def emit_get_global(self, global_index):
    #     # GET_GLOBAL, TYPE, INDEX
    #     self.append_byte(ByteCodeOp.GET_GLOBAL)
    #     tipe = self.symbol_table.globals[global_index].var_tipe
    #     self.append_byte(tipe.base_tipe)
    #     self.append_short(global_index)

    # def emit_get_addr_global(self, global_index):
    #     # GET_ADDR_GLOBAL, INDEX
    #     self.append_byte(ByteCodeOp.GET_ADDR_GLOBAL)
    #     self.append_short(global_index)

    # def emit_get_ptr_global(self, global_index):
    #     # GET_PTR_GLOBAL, TYPE, INDEX
    #     self.append_byte(ByteCodeOp.GET_PTR_GLOBAL)
    #     global_obj = self.symbol_table.globals[global_index]
    #     tipe = global_obj.var_tipe
    #     if not tipe.is_pointer():
    #         raise ValueError(f"Global {global_obj.name} is not a pointer")
    #     ptr_tipe: PointerTipe = cast(PointerTipe, tipe)
    #     ref_tipe = ptr_tipe.reference_tipe
    #     self.append_byte(ref_tipe)
    #     self.append_short(global_index)

    # def emit_set_global(self, global_index):
    #     self.code.append(ByteCode(ByteCodeOp.SET_GLOBAL, global_index))

    # def emit_set_ptr_global(self, global_index):
    #     self.code.append(ByteCode(ByteCodeOp.SET_PTR_GLOBAL, global_index))

    # def emit_push_param(self):
    #     self.code.append(ByteCode(ByteCodeOp.PUSH_PARAM))

    # def emit_zero(self):
    #     self.code.append(ByteCode(ByteCodeOp.ZERO))

    def emit_devprint(self, operand_t: Type):
        """
        Devprint bytecode:
            DEVPRINT - 1 byte
            OPERAND_T - 1 byte
        """
        self.code.append(ByteCodeOp.DEVPRINT.value)
        self.code.append(operand_t.value)

    def get_next_addr(self):
        return len(self.code)

    def fixup_jump(self, addr: int, target_addr: int):
        self.write_short(addr, target_addr)
