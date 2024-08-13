from retraction.bytecode import ByteCodeOp, ByteCode
from retraction.symtab import SymbolTable


class VirtualMachine:
    def __init__(self, code: list[ByteCode], symbol_table: SymbolTable):
        self.code = code
        self.symbol_table = symbol_table
        self.call_params = []
        self.params = []
        self.work_stack = []
        self.routine_stack = []
        self.pc = 0

    # def push(self, value):
    #     self.stack.append(value)

    # def pop(self):
    #     return self.stack.pop()

    # def top(self):
    #     return self.stack[-1]

    def run(self):
        self.work_stack.clear()
        self.routine_stack.clear()
        self.pc = 0
        while self.pc < len(self.code):
            instr = self.code[self.pc]
            if instr.op == ByteCodeOp.ADD:
                self.work_stack[-2] += self.work_stack[-1]
                self.work_stack.pop()
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
                global_value = self.symbol_table.globals[instr.value]
                self.work_stack.append(global_value[2])
            elif instr.op == ByteCodeOp.SET_GLOBAL:
                global_value = self.symbol_table.globals[instr.value]
                global_value[2] = self.work_stack.pop()
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
                self.pc = self.routine_stack.pop()
            elif instr.op == ByteCodeOp.POP:
                self.work_stack.pop()
            elif instr.op == ByteCodeOp.ZERO:
                self.work_stack.append(0)
            elif instr.op == ByteCodeOp.DEVPRINT:
                print(self.work_stack.pop())
            else:
                raise ValueError(f"Unknown instruction {instr.op}")
            self.pc += 1
