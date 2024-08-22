from retraction.bytecode import (
    ByteCodeOp,
    ByteCode,
    ByteCodeVariableAddressMode,
    ByteCodeVariableScope,
)
from retraction.error import InternalError
from retraction.symtab import SymbolTable
from retraction.tipes import CARD_TIPE, CAST_PRIORITY, INT_TIPE, SIZE_BYTES, Tipe, Type


# Memory layout:
# +---------------------------------------------------------+
# + 2K (unused/reserved)                                    + 0x0000 - 0x07FF (2048 bytes)
# +---------------------------------------------------------+
# + 5K locals/work stack                                    + 0x0800 - 0x1BFF (5120 bytes)
# +---------------------------------------------------------+
# + 1K parameter stack                                      + 0x1C00 - 0x1FFF (1024 bytes)
# +---------------------------------------------------------+
# + 40K program space                                       + 0x2000 - 0xBFFF (40960 bytes)
# +---------------------------------------------------------+
# + 16K (unused/reserved/"ROM")                             + 0xC000 - 0xFFFF (16384 bytes)
# +---------------------------------------------------------+

START_RESERVED = 0x0000
END_RESERVED = 0x07FF
START_LOCALS = 0x0800
END_LOCALS = 0x1BFF
START_PARAMS = 0x1C00
END_PARAMS = 0x1FFF
START_PROGRAM = 0x2000
END_PROGRAM = 0xBFFF
START_ROM = 0xC000
END_ROM = 0xFFFF


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
    def __init__(self, code: bytearray, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.memory = bytearray(0x10000)  # 64K memory
        # Copy code to memory
        self.initial_pc = 0x2000
        self.memory[self.initial_pc : self.initial_pc + len(code)] = code
        self.param_ptr = START_PARAMS
        self.frame_ptr = START_LOCALS
        self.work_ptr = END_LOCALS + 1
        # TODO : Maybe define VM to start at address near end of memory, or maybe at start of ROM space
        # For now, start at Program Space. Still, this requires jumping to the start of the program,
        # which is the beginning of the last defined routine.

        # self.call_params = []
        # self.params = []
        # self.work_stack = []
        # self.routine_stack = []

    # def push(self, value):
    #     self.stack.append(value)

    # def pop(self):
    #     return self.stack.pop()

    # def top(self):
    #     return self.stack[-1]

    def read_byte(self, address: int) -> int:
        return self.memory[address]

    def write_byte(self, address: int, value: int):
        # Little-endian
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

    def push_work(self, value: int, t: Type):
        size_bytes = SIZE_BYTES(t)
        if self.work_ptr - size_bytes < self.frame_ptr:
            raise InternalError("Work stack overflow")
        if size_bytes == 2:
            self.work_ptr -= 2
            self.write_card(self.work_ptr, value)
        elif size_bytes == 1:
            self.work_ptr -= 1
            self.write_byte(self.work_ptr, value)
        else:
            raise InternalError(f"Invalid size for type {t}")

    def pop_work(self, t: Type) -> int:
        size_bytes = SIZE_BYTES(t)
        if (self.work_ptr + size_bytes) > (END_LOCALS + 1):
            raise InternalError("Work stack underflow")
        if SIZE_BYTES(t) == 2:
            value = self.read_card(self.work_ptr)
            self.work_ptr += 2
        elif SIZE_BYTES(t) == 1:
            value = self.read_byte(self.work_ptr)
            self.work_ptr += 1
        else:
            raise InternalError(f"Invalid size for type {t}")
        return value

    def push_param(self, value: int, t: Type):
        size_bytes = SIZE_BYTES(t)
        if (self.param_ptr + size_bytes) > (END_PARAMS + 1):
            raise InternalError("Parameter stack overflow")
        if size_bytes == 2:
            self.write_card(self.param_ptr, value)
            self.param_ptr += 2
        elif size_bytes == 1:
            self.write_byte(self.param_ptr, value)
            self.param_ptr += 1
        else:
            raise InternalError(f"Invalid size for type {t}")

    def extract_binary_operands(self) -> tuple[Tipe, Tipe, int, int]:
        operand1_t = self.memory[self.pc + 1]
        operand2_t = self.memory[self.pc + 2]
        operand2 = self.pop_work(operand2_t)
        operand1 = self.pop_work(operand1_t)
        return operand1_t, operand2_t, operand1, operand2

    def run(self):
        self.pc = self.initial_pc
        while True:
            instr = self.memory[self.pc]
            op = ByteCodeOp(instr)
            if op in BINARY_OPS:
                op1_t, op2_t, op1, op2 = self.extract_binary_operands()
                result, result_t = BINARY_OPS[op](op1, op2, op1_t, op2_t)
                self.push_work(result, result_t)
                self.pc += 3
            elif op == ByteCodeOp.UNARY_MINUS:
                operand_t = Type(self.memory[self.pc + 1])
                operand = self.pop_work(operand_t)
                result = -operand
                self.push_work(result, operand_t)
                self.pc += 2
            elif op == ByteCodeOp.NUMERICAL_CONSTANT:
                constant_t = Type(self.memory[self.pc + 1])
                const_value = self.read_card(self.pc + 2)
                self.push_work(const_value, constant_t)
                self.pc += 3
            elif op == ByteCodeOp.JUMP_IF_FALSE:
                operand_t = Type(self.memory[self.pc + 1])
                operand = self.pop_work(operand_t)
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
                    address += self.frame_ptr
                elif scope == ByteCodeVariableScope.PARAM:
                    address += self.param_ptr
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
                self.push_work(value, value_t)
                self.pc += (
                    8 if address_mode == ByteCodeVariableAddressMode.OFFSET else 6
                )
            elif op == ByteCodeOp.PUSH_PARAM:
                value_t = Type(self.memory[self.pc + 1])
                size_bytes = SIZE_BYTES(value_t)
                if size_bytes == 2:
                    value = self.read_card(self.pc + 2)
                elif size_bytes == 1:
                    value = self.read_byte(self.pc + 2)
                else:
                    raise InternalError(f"Invalid size for type {value_t}")
                self.push_param(value, value_t)
                self.pc += 3 if size_bytes == 2 else 2

            elif op == ByteCodeOp.ROUTINE_CALL:
                # routine = self.symbol_table.routines[instr.value]
                # self.routine_stack.append(self.pc)
                # self.pc = routine.entry_point
                # for param in self.call_params:
                #     self.params.append(param)
                # self.call_params.clear()
            elif op == ByteCodeOp.RETURN:
                if self.routine_stack:
                    self.pc = self.routine_stack.pop()
                else:
                    break
            elif op == ByteCodeOp.POP:
                self.work_stack.pop()
            elif op == ByteCodeOp.ZERO:
                self.work_stack.append(0)
            elif op == ByteCodeOp.DEVPRINT:
                print(self.work_stack.pop())
            else:
                raise ValueError(f"Unknown instruction {instr.op}")
            self.pc += 1
