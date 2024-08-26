from retraction.bytecode import (
    ByteCodeOp,
    ByteCodeVariableAddressMode,
    ByteCodeVariableScope,
)
from retraction.error import InternalError
from retraction.symtab import SymbolTable
from retraction.types import CAST_PRIORITY, SIZE_BYTES, Type


# Virtualized 8-bit computer memory layout:
# +---------------------------------------------------------+
# + 2K (unused/reserved)                                    + 0x0000 - 0x07FF (2048 bytes)
# +---------------------------------------------------------+
# + 6K stack                                                + 0x0800 - 0x1FFF (6144 bytes)
# +---------------------------------------------------------+
# + 40K program space                                       + 0x2000 - 0xBFFF (40960 bytes)
# +---------------------------------------------------------+
# + 16K (unused/reserved/"ROM")                             + 0xC000 - 0xFFFF (16384 bytes)
# +---------------------------------------------------------+

START_RESERVED = 0x0000
END_RESERVED = 0x07FF
START_STACK = 0x0800
END_STACK = 0x1FFF
# START_PARAMS = 0x1C00
# END_PARAMS = 0x1FFF
START_PROGRAM = 0x2000
END_PROGRAM = 0xBFFF
START_ROM = 0xC000
END_ROM = 0xFFFF


# Action! does not use a stack for parameters, locals, and return addresses,
# as an optimization for the 6502. But we do use a stack for this VM.
#
# Stack layout: Stack grows upwards
# +----------------------------------------------------------+
# + CALLED ROUTINE                                           +
# + stack pointer (top) -->                                  +
# +                          work area         (dynamic)     +
# + frame pointer -->        local variables   (per routine) +
# +                          calling frame ptr (2 bytes)     +
# +                          return address    (2 bytes)     +
# +                          parameters size   (2 bytes)     +
# +                          parameters        (per routine) +
# +----------------------------------------------------------+
# + CALLING ROUTINE                                          +
# +                          work area for computation       +
# +                          local variables                 +
# +                          calling frame ptr               +
# +                          return address                  +
# +                          parameters size                 +
# +                          parameters                      +
# +----------------------------------------------------------+
# + (etc)                                                    +
# +----------------------------------------------------------+

# This is fairly typical of frame-pointer based stack management.
# However, the "parameters size" is needed here because the parameters are
# pushed onto the stack in the order they are declared, and the called routine
# references them by offset in the same order. So the parameters
# can't be a simple negative offset from the frame pointer as is
# commonly done by pushing parameters in reverse order. The order
# of parameters was chosen to match the Action! parameter layout on the
# 6502, which is not stack-based.


def binary_op_result_type(op1_t: Type, op2_t: Type) -> Type:
    pri1, pri2 = CAST_PRIORITY[op1_t], CAST_PRIORITY[op2_t]

    if pri1 < 1 or pri2 < 1:
        raise InternalError(f"Invalid types for result_type: {op1_t}, {op2_t}")

    if pri1 == pri2:
        return op1_t
    if pri1 > pri2:
        return op1_t
    return op2_t


def fit_to_type(value: int, t: Type) -> int:
    if t == CARD_TIPE or t == INT_TIPE:
        return value % 0x10000
    elif t == Type.BYTE or t == Type.CHAR:
        return value % 0x100

    raise InternalError(f"Invalid type for fit_to_type: {t}")


def add(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return fit_to_type(a + b, result_t), result_t


def subtract(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return fit_to_type(a - b, result_t), result_t


def multiply(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return fit_to_type(a * b, result_t), result_t


def divide(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return fit_to_type(a // b, result_t), result_t


def mod(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return fit_to_type(a % b, result_t), result_t


def lsh(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return fit_to_type(a << b, result_t), result_t


def rsh(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return fit_to_type(a >> b, result_t), result_t


def eq(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    return int(a == b), Type.BYTE


def ne(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    return int(a != b), Type.BYTE


def gt(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    return int(a > b), Type.BYTE


def ge(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    return int(a >= b), Type.BYTE


def lt(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    return int(a < b), Type.BYTE


def le(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    return int(a <= b), Type.BYTE


def xor(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return a ^ b, result_t


def bit_and(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return a & b, result_t


def bit_or(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return a | b, result_t


def bit_xor(a: int, b: int, a_t: Type, b_t: Type) -> tuple[int, Type]:
    result_t = binary_op_result_type(a_t, b_t)
    return a ^ b, result_t


# Function dispatch table for binary operations
# TODO: Could be an array of functions for performance, but this is more flexible for now
BINARY_OPS = {
    ByteCodeOp.ADD: add,
    ByteCodeOp.SUBTRACT: subtract,
    ByteCodeOp.MULTIPLY: multiply,
    ByteCodeOp.DIVIDE: divide,
    ByteCodeOp.MOD: mod,
    ByteCodeOp.LSH: lsh,
    ByteCodeOp.RSH: rsh,
    ByteCodeOp.EQ: eq,
    ByteCodeOp.NE: ne,
    ByteCodeOp.GT: gt,
    ByteCodeOp.GE: ge,
    ByteCodeOp.LT: lt,
    ByteCodeOp.LE: le,
    ByteCodeOp.XOR: xor,
    ByteCodeOp.BIT_AND: bit_and,
    ByteCodeOp.BIT_OR: bit_or,
    ByteCodeOp.BIT_XOR: bit_xor,
}


class VirtualMachine:
    def __init__(self, code: bytearray, symbol_table: SymbolTable = None):
        self.symbol_table = symbol_table
        self.memory = bytearray(0x10000)  # 64K memory
        # Copy code to memory
        self.initial_pc = 0x2000
        self.memory[self.initial_pc : self.initial_pc + len(code)] = code
        self.frame_ptr = START_STACK
        self.params_size = 0
        # TODO : Maybe define VM to start at address near end of memory, or maybe at start of ROM space
        # For now, start at Program Space. Still, this will require jumping to the start of the program,
        # which is the beginning of the last defined routine.

    def read_byte(self, address: int) -> int:
        return self.memory[address]

    def write_byte(self, address: int, value: int):
        # TODO: May be unnecessary eventually, but ensure value is positive
        if value < 0:
            value = value % 0x100
        self.memory[address] = value

    def read_card(self, address: int) -> int:
        # Little-endian
        return self.memory[address] + (self.memory[address + 1] << 8)

    def write_card(self, address: int, value: int):
        # Little-endian
        # TODO: May be unnecessary eventually, but ensure value is positive
        if value < 0:
            value = value % 0x10000
        self.memory[address] = value & 0xFF
        self.memory[address + 1] = value >> 8

    def read(self, t: Type, address: int) -> int:
        if SIZE_BYTES(t) == 2:
            return self.read_card(address)
        elif SIZE_BYTES(t) == 1:
            return self.read_byte(address)
        else:
            raise InternalError(f"Invalid size for type {t}")

    def push(self, value: int, t: Type):
        size_bytes = SIZE_BYTES(t)
        if self.stack_ptr + size_bytes > END_STACK + 1:
            raise InternalError("Stack overflow")
        if size_bytes == 2:
            self.write_card(self.stack_ptr, value)
            self.stack_ptr += 2
        elif size_bytes == 1:
            self.write_byte(self.stack_ptr, value)
            self.stack_ptr += 1
        else:
            raise InternalError(f"Invalid size for type {t}")

    def pop(self, t: Type) -> int:
        size_bytes = SIZE_BYTES(t)
        if self.stack_ptr - size_bytes < START_STACK:
            raise InternalError("Stack underflow")
        if SIZE_BYTES(t) == 2:
            self.stack_ptr -= 2
            value = self.read_card(self.stack_ptr)
        elif SIZE_BYTES(t) == 1:
            self.stack_ptr -= 1
            value = self.read_byte(self.stack_ptr)
        else:
            raise InternalError(f"Invalid size for type {t}")
        return value

    def extract_binary_operands(self) -> tuple[Type, Type, int, int]:
        operand1_t = self.memory[self.pc + 1]
        operand2_t = self.memory[self.pc + 2]
        operand2 = self.pop(operand2_t)
        operand1 = self.pop(operand1_t)
        return operand1_t, operand2_t, operand1, operand2

    def run(self):
        self.pc = self.initial_pc
        while True:
            # TODO: Optimize by reading the instruction and then dispatching
            instr = self.memory[self.pc]
            op = ByteCodeOp(instr)
            if op in BINARY_OPS:
                op1_t, op2_t, op1, op2 = self.extract_binary_operands()
                result, result_t = BINARY_OPS[op](op1, op2, op1_t, op2_t)
                self.push(result, result_t)
                self.pc += 3
            elif op == ByteCodeOp.UNARY_MINUS:
                operand_t = Type(self.memory[self.pc + 1])
                operand = self.pop(operand_t)
                result = -operand
                self.push(result, operand_t)
                self.pc += 2
            elif op == ByteCodeOp.NUMERICAL_CONSTANT:
                constant_t = Type(self.memory[self.pc + 1])
                const_value = self.read(constant_t, self.pc + 2)
                self.push(const_value, constant_t)
                self.pc += 3 if SIZE_BYTES(constant_t) == 2 else 2
            elif op == ByteCodeOp.JUMP_IF_FALSE:
                operand_t = Type(self.memory[self.pc + 1])
                operand = self.pop(operand_t)
                if operand == 0:
                    jump_addr = self.read_card(self.pc + 2)
                    self.pc = jump_addr
                else:
                    self.pc += 4
            elif op == ByteCodeOp.JUMP:
                jump_addr = self.memory[self.pc + 1]
                self.pc = jump_addr
            elif instr.op == ByteCodeOp.GET_VARIABLE:
                value_t = Type(self.memory[self.pc + 1])
                scope = ByteCodeVariableScope(self.memory[self.pc + 2])
                address_mode = ByteCodeVariableAddressMode(self.memory[self.pc + 3])
                address = self.read_card(self.pc + 4)
                # Adjust address based on scope
                if scope == ByteCodeVariableScope.LOCAL:
                    # Skip return address and calling frame pointer
                    address += self.frame_ptr
                elif scope == ByteCodeVariableScope.PARAM:
                    param_size = self.read_card(self.frame_ptr - 6)
                    address += self.frame_ptr - 6 - param_size
                # Get value from address based on address mode
                value = None
                if address_mode == ByteCodeVariableAddressMode.DEFAULT:
                    if SIZE_BYTES(value_t) == 2:
                        value = self.read_card(address)
                    else:
                        value = self.read_byte(address)
                elif address_mode == ByteCodeVariableAddressMode.POINTER:
                    if SIZE_BYTES(value_t) == 2:
                        value = self.read_card(self.read_card(address))
                    else:
                        value = self.read_byte(self.read_card(address))
                elif address_mode == ByteCodeVariableAddressMode.REFERENCE:
                    value = address
                elif address_mode == ByteCodeVariableAddressMode.OFFSET:
                    offset = self.read_card(self.pc + 6)
                    if SIZE_BYTES(value_t) == 2:
                        value = self.read_card(address + offset)
                    else:
                        value = self.read_byte(address + offset)
                if value is None:
                    raise InternalError("Invalid value")
                self.push(value, value_t)
                self.pc += (
                    8 if address_mode == ByteCodeVariableAddressMode.OFFSET else 6
                )
            elif op == ByteCodeOp.PUSH_PARAM:
                value_t = Type(self.memory[self.pc + 1])
                # In theory, we pop this and then push it. But since the value is already on the
                # stack, we just count the size.
                self.params_size += SIZE_BYTES(value_t)
            elif op == ByteCodeOp.ROUTINE_CALL:
                return_t = Type(self.memory[self.pc + 1])  # TODO: Unused?
                params_size = self.read_card(self.pc + 2)
                locals_size = self.read_card(self.pc + 4)
                routine_addr = self.read_card(self.pc + 6)
                self.push(params_size, Type.CARD)
                # Push return address
                self.push(self.pc + 8, Type.CARD)
                # Push frame pointer
                self.push(self.frame_ptr, Type.CARD)
                # Set new frame pointer to top of stack
                self.frame_ptr = self.stack_ptr
                # Advance stack pointer to work area
                self.stack_ptr += locals_size
                # Jump to routine
                self.pc = routine_addr
            elif op == ByteCodeOp.RETURN:
                # TODO: Make sure to add a cast in the parser to ensure that the actual return type
                # matches the routine's declared return type
                return_t = Type(self.memory[self.pc + 1])
                return_value = None
                if return_t != Type.VOID_T:
                    return_value = self.pop(return_t)
                # Pop frame pointer
                self.frame_ptr = self.pop(Type.CARD)
                # Pop return address
                self.pc = self.pop(Type.CARD)
                # Pop params size
                self.pop(Type.CARD)
                # Push return value
                if return_t != Type.VOID_T:
                    self.push(return_value, return_t)
            elif op == ByteCodeOp.CAST:
                from_t = Type(self.memory[self.pc + 1])
                to_t = Type(self.memory[self.pc + 2])
                value = self.pop(from_t)
                self.push(value, to_t)
                self.pc += 3
            elif op == ByteCodeOp.NOP:
                self.pc += 1
            elif op == ByteCodeOp.POP:
                pop_t = Type(self.memory[self.pc + 1])
                self.pop(pop_t)
                self.pc += 2
            elif op == ByteCodeOp.DEVPRINT:
                value_t = Type(self.memory[self.pc + 1])
                value = self.pop(value_t)
                print(value)
            else:
                raise ValueError(f"Unknown instruction {instr.op}")
