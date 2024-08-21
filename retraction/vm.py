from retraction.bytecode import ByteCodeOp, ByteCode
from retraction.symtab import SymbolTable
from retraction.tipes import CARD_TIPE, INT_TIPE, Tipe


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


class VirtualMachine:
    def __init__(self, code: bytearray, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.memory = bytearray(0x10000)  # 64K memory
        # Copy code to memory
        self.initial_pc = 0x2000
        self.memory[self.initial_pc : self.initial_pc + len(code)] = code
        self.param_sp = START_PARAMS
        self.local_sp = START_LOCALS
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

    def extract_binary_operands(self, pc_offset) -> tuple[Tipe, Tipe, int, int]:
        operand_types = self.memory[self.pc + pc_offset]
        operand_1_type = operand_types >> 4
        operand_2_type = operand_types & 0x0F
        # Depending on size of operands, read 1 or 2 bytes each from local stack
        if operand_2_type.size_bytes == 2:
            self.local_sp -= 2
            operand_2 = self.read_card(self.local_sp)
        else:
            self.local_sp -= 1
            operand_2 = self.read_byte(self.local_sp)
        if operand_1_type.size_bytes == 2:
            self.local_sp -= 2
            operand_1 = self.read_card(self.local_sp)
        else:
            self.local_sp -= 1
            operand_1 = self.read_byte(self.local_sp)

        return operand_1_type, operand_2_type, operand_1, operand_2

    def run(self):
        self.pc = self.initial_pc
        while True:
            instr = self.memory[self.pc]
            op = ByteCodeOp(instr)
            if op == ByteCodeOp.ADD:
                op1_t, op2_t, op1, op2 = self.extract_binary_operands(1)
                op_t = self.memory[self.pc + 2]

            elif instr.op == ByteCodeOp.SUBTRACT:
                self.work_stack[-2] -= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.MULTIPLY:
                self.work_stack[-2] *= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.DIVIDE:
                self.work_stack[-2] //= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.MOD:
                self.work_stack[-2] %= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.LSH:
                self.work_stack[-2] <<= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.RSH:
                self.work_stack[-2] >>= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_EQ:
                self.work_stack[-2] = self.work_stack[-2] == self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_NE:
                self.work_stack[-2] = self.work_stack[-2] != self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_GT:
                self.work_stack[-2] = self.work_stack[-2] > self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_GE:
                self.work_stack[-2] = self.work_stack[-2] >= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_LT:
                self.work_stack[-2] = self.work_stack[-2] < self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_LE:
                self.work_stack[-2] = self.work_stack[-2] <= self.work_stack[-1]
                self.work_stack.pop()
            # elif instr.op == ByteCodeOp.AND:
            #     self.work_stack[-2] = self.work_stack[-2] and self.work_stack[-1]
            #     self.work_stack.pop()
            # elif instr.op == ByteCodeOp.OR:
            #     self.work_stack[-2] = self.work_stack[-2] or self.work_stack[-1]
            #     self.work_stack.pop()
            elif instr.op == ByteCodeOp.XOR:
                self.work_stack[-2] = self.work_stack[-2] ^ self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_BIT_AND:
                self.work_stack[-2] &= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_BIT_OR:
                self.work_stack[-2] |= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.OP_BIT_XOR:
                self.work_stack[-2] ^= self.work_stack[-1]
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.UNARY_MINUS:
                self.work_stack[-1] = -self.work_stack[-1]
            elif instr.op == ByteCodeOp.CONSTANT:
                const_value = self.symbol_table.constants[instr.value]
                # TODO : Deal with string constants
                if type(const_value) == str:
                    raise NotImplementedError
                self.work_stack.append(const_value)
            elif instr.op == ByteCodeOp.JUMP_IF_FALSE:
                if not self.work_stack.pop():
                    self.pc = instr.value
            elif instr.op == ByteCodeOp.JUMP:
                self.pc = instr.value
            elif instr.op == ByteCodeOp.GET_GLOBAL:
                global_obj = self.symbol_table.globals[instr.value]
                self.work_stack.append(global_obj.value)
            elif instr.op == ByteCodeOp.SET_GLOBAL:
                global_obj = self.symbol_table.globals[instr.value]
                global_obj.value = self.work_stack.pop()
            elif instr.op == ByteCodeOp.PUSH_PARAM:
                self.call_params.append(self.work_stack.pop())
            elif instr.op == ByteCodeOp.ROUTINE_CALL:
                routine = self.symbol_table.routines[instr.value]
                self.routine_stack.append(self.pc)
                self.pc = routine.entry_point
                for param in self.call_params:
                    self.params.append(param)
                self.call_params.clear()
            elif instr.op == ByteCodeOp.RETURN:
                if self.routine_stack:
                    self.pc = self.routine_stack.pop()
                else:
                    break
            elif instr.op == ByteCodeOp.POP:
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.ZERO:
                self.work_stack.append(0)
            elif instr.op == ByteCodeOp.DEVPRINT:
                print(self.work_stack.pop())
            else:
                raise ValueError(f"Unknown instruction {instr.op}")
            self.pc += 1
