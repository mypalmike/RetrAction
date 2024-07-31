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


class CodeGenForTest:
    def __init__(self):
        self.code = []
        self.addr = 0

    def emit_exit_stmt(self):
        self.code.append("EXIT")
        self.addr += 1

    def emit_fund_ident(self, fund_type, identifier):
        self.code.append(f"FUND_IDENT {fund_type} {identifier}")
        self.addr += 1

    def emit_ptr_ident_value(self, ptr_type, identifier, value):
        self.code.append(f"PTR_IDENT_VALUE {ptr_type} {identifier} {value}")
        self.addr += 1

    def emit_ptr_ident(self, ptr_type, identifier):
        self.code.append(f"PTR_IDENT {ptr_type} {identifier}")
        self.addr += 1

    def emit_rec_ident_value(self, rec_type, identifier, addr):
        self.code.append(f"REC_IDENT_VAL {rec_type} {identifier} {addr}")
        self.addr += 1

    def emit_rec_ident(self, ref_type, identifier):
        self.code.append(f"REC_IDENT {ref_type} {identifier}")
        self.addr += 1

    def emit_routine_call(self, identifier, params):
        self.code.append(f"ROUTINE_CALL {identifier} {params}")
        self.addr += 1

    def emit_return(self):
        self.code.append("RETURN")
        self.addr += 1

    def emit_define(self, addr):
        self.code.append(f"DEFINE {addr}")
        self.addr += 1

    def emit_define_value(self, name, value):
        self.code.append(f"DEFINE_VALUE {name} {value}")
        self.addr += 1

    def emit_add(self):
        self.code.append("ADD")
        self.addr += 1

    def emit_subtract(self):
        self.code.append("SUBTRACT")
        self.addr += 1

    def emit_multiply(self):
        self.code.append("MULTIPLY")
        self.addr += 1

    def emit_divide(self):
        self.code.append("DIVIDE")
        self.addr += 1

    def emit_unary_minus(self):
        self.code.append("UNARY_MINUS")
        self.addr += 1

    def emit_number(self, number):
        self.code.append(f"NUMBER {number}")
        self.addr += 1
