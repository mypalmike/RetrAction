from retraction.bytecode import ByteCodeOp, ByteCode
from retraction.symtab import SymbolTable


class VirtualMachine:
    def __init__(self, code: list[ByteCode], symbol_table: SymbolTable):
        self.code = code
        self.symbol_table = symbol_table
        self.stack = []
        self.pc = 0

    # def push(self, value):
    #     self.stack.append(value)

    # def pop(self):
    #     return self.stack.pop()

    # def top(self):
    #     return self.stack[-1]

    def run(self):
        self.stack.clear()
        self.pc = 0
        while self.pc < len(self.code):
            print(self.stack)
            instr = self.code[self.pc]
            if instr.op == ByteCodeOp.ADD:
                self.stack[-2] += self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.SUBTRACT:
                self.stack[-2] -= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.MULTIPLY:
                self.stack[-2] *= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.DIVIDE:
                self.stack[-2] //= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.MOD:
                self.stack[-2] %= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.LSH:
                self.stack[-2] <<= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.RSH:
                self.stack[-2] >>= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.OP_EQ:
                self.stack[-2] = self.stack[-2] == self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.OP_NE:
                self.stack[-2] = self.stack[-2] != self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.OP_GT:
                self.stack[-2] = self.stack[-2] > self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.OP_GE:
                self.stack[-2] = self.stack[-2] >= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.OP_LT:
                self.stack[-2] = self.stack[-2] < self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.OP_LE:
                self.stack[-2] = self.stack[-2] <= self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.AND:
                self.stack[-2] = self.stack[-2] and self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.OR:
                self.stack[-2] = self.stack[-2] or self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.XOR:
                self.stack[-2] = self.stack[-2] ^ self.stack[-1]
                self.stack.pop()
            elif instr.op == ByteCodeOp.UNARY_MINUS:
                self.stack[-1] = -self.stack[-1]
            elif instr.op == ByteCodeOp.CONSTANT:
                const_value = self.symbol_table.constants[instr.value]
                print(f"Pushing constant {const_value}")
                # TODO : Deal with string constants
                if type(const_value) == str:
                    raise NotImplementedError
                self.stack.append(const_value)
            elif instr.op == ByteCodeOp.ROUTINE_CALL:
                routine = self.symbol_table.routines[instr.value]
                raise NotImplementedError()
            elif instr.op == ByteCodeOp.RETURN:
                # TODO: Is this right?
                self.pc = self.stack.pop()
            elif instr.op == ByteCodeOp.EXIT:
                break
            self.pc += 1
        print(self.stack)
