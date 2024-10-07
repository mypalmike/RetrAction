from functools import singledispatchmethod
from typing import cast
from retraction import ast
from retraction.bytecode import (
    ByteCodeOp,
    ByteCodeVariableAddressMode,
    ByteCodeVariableScope,
)
from retraction.codegen import ByteCodeGen
from retraction.error import InternalError
from retraction.types import ArrayType, FundamentalType, PointerType, RecordType
from retraction import symtab


PARAMS_OFFSET = -4

# Note: AND and OR are short-circuiting operators, so they are
# not implemented as binary operators in the bytecode.
OP_MAP: dict[ast.Op, ByteCodeOp] = {
    ast.Op.ADD: ByteCodeOp.ADD,
    ast.Op.SUB: ByteCodeOp.SUBTRACT,
    ast.Op.MUL: ByteCodeOp.MULTIPLY,
    ast.Op.DIV: ByteCodeOp.DIVIDE,
    ast.Op.MOD: ByteCodeOp.MOD,
    ast.Op.EQ: ByteCodeOp.EQ,
    ast.Op.NE: ByteCodeOp.NE,
    ast.Op.LT: ByteCodeOp.LT,
    ast.Op.LE: ByteCodeOp.LE,
    ast.Op.GT: ByteCodeOp.GT,
    ast.Op.GE: ByteCodeOp.GE,
    ast.Op.BIT_AND: ByteCodeOp.BIT_AND,
    ast.Op.BIT_OR: ByteCodeOp.BIT_OR,
    ast.Op.BIT_XOR: ByteCodeOp.BIT_XOR,
    ast.Op.LSH: ByteCodeOp.LSH,
    ast.Op.RSH: ByteCodeOp.RSH,
}


class BCWalk:
    def __init__(self, codegen: ByteCodeGen):
        self.codegen = codegen

        self.symbol_table: symtab.SymTab | None = None
        self.current_routine: ast.Routine | None = None
        self.next_param_addr: int | None = None
        self.next_local_addr: int | None = None
        self.local_param_index: int = 0

    @singledispatchmethod
    def walk(self, node: ast.Node):
        raise InternalError(f"Unsupported node type {node}")  # {type(node)}")

    @walk.register
    def _(self, program: ast.Program):
        self.symbol_table = program.symbol_table
        for module in program.modules:
            self.walk(module)

    @walk.register
    def _(self, module: ast.Module):
        for decl in module.decls:
            self.walk(decl)

        for routine in module.routines:
            self.walk(routine)

    @walk.register
    def _(self, var_decl: ast.VarDecl):
        is_global = self.current_routine is None
        # Global vars are emitted as raw data
        if is_global:
            init_opts = var_decl.init_opts
            if init_opts is not None and init_opts.is_address:
                addr = init_opts.initial_values[0]
                # return init_opts.initial_values[0]
            #            addr = len(self.code)
            # Depending on the type of the variable, we need to emit a different number of bytes
            if isinstance(var_decl.var_t, ArrayType):
                array_t = cast(ArrayType, var_decl.var_t)
                length = array_t.length
                init_opts = var_decl.init_opts
                element_t = array_t.element_t
                if init_opts is not None and init_opts.is_address:
                    # Variable is initialized with an address
                    addr = init_opts.initial_values[0]
                elif length is None and init_opts is None:
                    # Legal but unusual for a global, array is declared with no
                    # length and no initial values. Just get the address.
                    addr = self.codegen.get_next_addr()
                else:
                    values = []
                    if length is not None:
                        values = [0] * length
                    if init_opts is not None:
                        values = init_opts.initial_values
                    size_bytes = element_t.size_bytes
                    if size_bytes == 1:
                        addr = self.codegen.emit_bytes(values)
                    elif size_bytes == 2:
                        addr = self.codegen.emit_shorts(values)
                    else:
                        raise InternalError(
                            f"Unsupported array element type {element_t}"
                        )
            elif isinstance(var_decl.var_t, PointerType):
                values = [0]
                if init_opts is not None:
                    values = init_opts.initial_values
                addr = self.codegen.emit_shorts(values)
            elif isinstance(var_decl.var_t, RecordType):
                # Record types have no initial values, emit zeroes
                record_t = cast(RecordType, var_decl.var_t)
                addr = self.codegen.emit_bytes([0] * record_t.size_bytes)
            elif isinstance(var_decl.var_t, FundamentalType):
                fund_t = cast(FundamentalType, var_decl.var_t)
                values = [0]
                if init_opts is not None:
                    values = init_opts.initial_values
                size_bytes = fund_t.size_bytes
                if size_bytes == 1:
                    addr = self.codegen.emit_bytes(values)
                elif size_bytes == 2:
                    addr = self.codegen.emit_shorts(values)
                else:
                    raise InternalError(f"Unsupported variable type {var_decl.var_t}")
            var_decl.addr = addr
        elif self.next_param_addr is not None:
            # Assign an offset address to the parameter.
            size_bytes = 0
            if isinstance(var_decl.var_t, FundamentalType):
                size_bytes = var_decl.var_t.size_bytes
            elif isinstance(var_decl.var_t, PointerType):
                size_bytes = 2
            elif isinstance(var_decl.var_t, ArrayType):
                # TODO: Arrays are passed as pointers?
                size_bytes = 2
            elif isinstance(var_decl.var_t, RecordType):
                raise InternalError("RecordType not supported for parameters")
            var_decl.addr = self.next_param_addr - size_bytes
            self.next_param_addr = var_decl.addr
        elif self.next_local_addr is not None:
            # Assign an offset address to the local variable.
            var_decl.addr = self.next_local_addr
            self.next_local_addr += var_decl.var_t.size_bytes

            # Local var initialization is emitted as instructions
            if var_decl.init_opts is not None:
                self.codegen.emit_numerical_constant(
                    var_decl.init_opts.initial_values[self.local_param_index]
                )
                self.codegen.emit_store_variable(
                    var_decl.var_t,
                    ByteCodeVariableScope.LOCAL,
                    ByteCodeVariableAddressMode.DEFAULT,
                    var_decl.addr,
                )

    @walk.register
    def _(self, routine: ast.Routine):
        try:
            self.symbol_table = routine.local_symtab
            self.current_routine = routine
            routine.addr = self.codegen.get_next_addr()
            # Reverse the parameter list
            if routine.params is not None:
                try:
                    # initial negative offset from frame pointer
                    self.next_param_addr = PARAMS_OFFSET
                    for param in reversed(routine.params):
                        self.walk(param)
                finally:
                    self.next_param_addr = None
            if routine.decls is not None:
                try:
                    self.next_local_addr = 0
                    self.local_param_index = 0
                    for decl in routine.decls:
                        self.walk(decl)
                finally:
                    self.next_local_addr = None
            if routine.statements is not None:
                for statement in routine.statements:
                    self.walk(statement)
            self.current_routine = None
        finally:
            self.symbol_table = self.symbol_table.parent

    @walk.register
    def _(self, assign: ast.Assign):
        target = assign.target
        expr = assign.expr
        self.walk(expr)
        if isinstance(target, ast.Var):
            var = cast(ast.Var, target)
            if self.symbol_table is None:
                raise InternalError("Symbol table not set")
            entry, depth = self.symbol_table.find(var.name)
            var_decl = cast(ast.VarDecl, entry.node)
            if var_decl.addr is None:
                raise InternalError("Address not found")
            if not isinstance(var_decl.var_t, FundamentalType):
                raise InternalError("Default variable access should be FundamentalType")
            scope = ByteCodeVariableScope.GLOBAL
            if depth > 0:
                if var_decl.addr < 0:
                    scope = ByteCodeVariableScope.PARAM
                else:
                    scope = ByteCodeVariableScope.LOCAL
            if expr.fund_t.size_bytes != var_decl.var_t.size_bytes:
                # Emit a cast
                self.codegen.emit_cast(expr.fund_t, var_decl.var_t)
            self.codegen.emit_store_variable(
                var_decl.var_t,
                scope,
                ByteCodeVariableAddressMode.DEFAULT,
                var_decl.addr,
            )
        elif isinstance(target, ast.ArrayAccess):
            raise NotImplementedError()
        elif isinstance(target, ast.Dereference):
            raise NotImplementedError()
        elif isinstance(target, ast.Dereference):
            raise NotImplementedError()

        else:
            raise InternalError("Unsupported assignment target")

    @walk.register
    def _(self, numerical_const: ast.NumericalConst):
        self.codegen.emit_numerical_constant(
            numerical_const.expr_t, numerical_const.value
        )

    @walk.register
    def _(self, var: ast.Var):
        if self.symbol_table is None:
            raise InternalError("Symbol table not set")
        entry, depth = self.symbol_table.find(var.name)
        var_decl = cast(ast.VarDecl, entry.node)
        if var_decl.addr is None:
            raise InternalError("Address not found")
        if not isinstance(var_decl.var_t, FundamentalType):
            raise InternalError("Default variable access should be FundamentalType")
        scope = ByteCodeVariableScope.GLOBAL
        if depth > 0:
            if var_decl.addr < 0:
                scope = ByteCodeVariableScope.PARAM
            else:
                scope = ByteCodeVariableScope.LOCAL
        self.codegen.emit_load_variable(
            var_decl.var_t,
            scope,
            ByteCodeVariableAddressMode.DEFAULT,
            var_decl.addr,
        )

    @walk.register
    def _(self, binary_expr: ast.BinaryExpr):
        op = binary_expr.op
        if op in OP_MAP:
            self.walk(binary_expr.left)
            self.walk(binary_expr.right)
            bytecode_op = OP_MAP[op]
            self.codegen.emit_binary_op(
                bytecode_op, binary_expr.left.fund_t, binary_expr.right.fund_t
            )
        elif op == ast.Op.AND:
            # Short-circuiting AND
            self.walk(binary_expr.left)
            self.codegen.emit_dup(binary_expr.left.fund_t)
            jump_end = self.codegen.emit_jump_if_false(binary_expr.left.fund_t)
            self.codegen.emit_pop(binary_expr.left.fund_t)
            self.walk(binary_expr.right)
            target_addr = self.codegen.get_next_addr()
            self.codegen.fixup_jump(jump_end, target_addr)
        elif op == ast.Op.OR:
            # Short-circuiting OR
            self.walk(binary_expr.left)
            self.codegen.emit_dup(binary_expr.left.fund_t)
            jump_else = self.codegen.emit_jump_if_false(binary_expr.left.fund_t)
            jump_end = self.codegen.emit_jump()
            self.codegen.fixup_jump(jump_else, self.codegen.get_next_addr())
            self.codegen.emit_pop(binary_expr.left.fund_t)
            self.walk(binary_expr.right)
            self.codegen.fixup_jump(jump_end, self.codegen.get_next_addr())

    @walk.register
    def _(self, unary_expr: ast.UnaryExpr):
        self.walk(unary_expr.expr)
        if unary_expr.op == ast.Op.SUB:
            self.codegen.emit_unary_minus(unary_expr.expr.fund_t)
        else:
            raise InternalError(f"Unsupported unary operator {unary_expr.op}")

    @walk.register
    def _(self, return_node: ast.Return):
        if return_node.expr is not None:
            self.walk(return_node.expr)
            self.codegen.emit_return(return_node.expr.fund_t)
        else:
            self.codegen.emit_return(FundamentalType.VOID_T)

    @walk.register
    def _(self, call_stmt: ast.CallStmt):
        # This is a wrapper around the expression call.
        # TODO: Maybe pop the return value?
        self.walk(call_stmt.call)

    @walk.register
    def _(self, call_expr: ast.Call):
        if self.symbol_table is None:
            raise InternalError("Symbol table not set")
        routine_name = call_expr.name
        routine_entry, _ = self.symbol_table.find(routine_name)
        if routine_entry is None:
            raise InternalError(f"Routine {routine_name} not found")
        routine = cast(ast.Routine, routine_entry.node)
        if not isinstance(routine, ast.Routine):
            raise InternalError(f"Routine {routine_name} not found")
        addr = routine.addr
        locals_size = routine.locals_size
        params_size = routine.params_size

        # Walk the args in reverse order
        if call_expr.args is not None:
            for i in range(len(call_expr.args) - 1, -1, -1):
                arg = call_expr.args[i]
                self.walk(arg)
                param_t = routine.params[i].var_t
                param_fund_t = FundamentalType.BYTE_T
                if isinstance(param_t, FundamentalType):
                    param_fund_t = param_t
                else:
                    param_fund_t = FundamentalType.CARD_T
                arg_t = arg.fund_t
                # If the argument type is not the same as the parameter type, emit a cast
                if param_t.size_bytes != arg_t.size_bytes:
                    self.codegen.emit_cast(arg_t, param_fund_t)

        # Emit the call
        self.codegen.emit_routine_call(call_expr.fund_t, locals_size, addr)
        self.codegen.emit_routine_postlude(routine.return_t, params_size)

    @walk.register
    def _(self, if_stmt: ast.If):
        jump_end_addrs: list[int] = []
        for conditional in if_stmt.conditionals:
            self.walk(conditional.condition)
            jump_over_addr = self.codegen.emit_jump_if_false(
                conditional.condition.fund_t
            )
            for statement in conditional.body:
                self.walk(statement)
            jump_end_addrs.append(self.codegen.emit_jump())
            self.codegen.fixup_jump(jump_over_addr, self.codegen.get_next_addr())
        if if_stmt.else_body is not None:
            for statement in if_stmt.else_body:
                self.walk(statement)
        end_addr = self.codegen.get_next_addr()
        for jump_end_addr in jump_end_addrs:
            self.codegen.fixup_jump(jump_end_addr, end_addr)

    @walk.register
    def _(self, devprint: ast.DevPrint):
        expr = devprint.expr
        self.walk(expr)
        self.codegen.emit_devprint(expr.fund_t)
