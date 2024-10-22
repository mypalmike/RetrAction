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
        # self.var_addr: int | None = None
        # self.is_lhs: bool = False

    @singledispatchmethod
    def walk(self, node: ast.Node):
        raise InternalError(f"Unsupported node type {node}")  # {type(node)}")

    @walk.register
    def _(self, program: ast.Program):
        self.symbol_table = program.symbol_table

        # Start with main wrapper routine, which helps set up the stack frame for the first routine
        # Don't know its local size or address yet, so initially they are set to 0
        self.codegen.emit_routine_call(FundamentalType.VOID_T, 0, 0)
        self.codegen.emit_return(FundamentalType.VOID_T)

        # Walk the modules, emitting code for each
        for module in program.modules:
            self.walk(module)

        # Patch the final routine details
        final_routine = cast(ast.Routine, self.symbol_table.get_last_routine().node)
        locals_size = final_routine.locals_size
        self.codegen.write_short(2, locals_size)
        addr_final_routine = final_routine.addr
        if addr_final_routine is None:
            raise InternalError("Final routine address not found")
        self.codegen.write_short(4, addr_final_routine)

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
            # TODO: This is incomplete and broken.
            if var_decl.init_opts is not None:
                self.codegen.emit_push_constant(
                    var_decl.init_opts.initial_values[self.local_param_index]
                )
                self.codegen.emit_store_variable(
                    var_decl.var_t,
                    ByteCodeVariableScope.LOCAL,
                    ByteCodeVariableAddressMode.DEFAULT,
                    var_decl.addr,
                )

    @walk.register
    def _(self, get_var: ast.GetVar):
        # Push the address of the variable onto the stack
        # print(f"get_var: {get_var.var.name}")
        self.walk(get_var.var)
        # print(f"get_var.addr: {get_var.var.addr}")
        # addr = get_var.var.addr
        is_relative = isinstance(get_var.var, ast.Var) and get_var.var.addr_is_relative
        # if addr is None:
        #     raise InternalError("Address not found for get_var")
        # self.codegen.emit_push_constant(FundamentalType.CARD_T, addr)

        # Load the value from the address
        if is_relative:
            self.codegen.emit_load_relative(get_var.fund_t)
        else:
            self.codegen.emit_load_absolute(get_var.fund_t)

    @walk.register
    def _(self, var: ast.Var):
        print(f"var: {var.name}")
        if self.symbol_table is None:
            raise InternalError("Symbol table not set")
        entry, depth = self.symbol_table.find(var.name)
        var_decl = cast(ast.VarDecl, entry.node)
        if var_decl.addr is None:
            raise InternalError(f"Address not found for variable {var.name}")
        var.addr = var_decl.addr
        var.addr_is_relative = depth > 0
        print(f"var.addr: {var.addr}")
        print(f"var.addr_is_relative: {var.addr_is_relative}")

        if isinstance(var_decl.var_t, PointerType):
            if var.addr_is_relative:
                # If pointer, we need to convert relative address to absolute
                self.codegen.emit_push_frame_pointer()
                self.codegen.emit_push_constant(FundamentalType.INT_T, var.addr)
                self.codegen.emit_binary_op(
                    ByteCodeOp.ADD, FundamentalType.INT_T, FundamentalType.INT_T
                )
            else:
                self.codegen.emit_push_constant(FundamentalType.CARD_T, var.addr)
        else:
            self.codegen.emit_push_constant(FundamentalType.CARD_T, var.addr)

    @walk.register
    def _(self, ref: ast.Reference):
        # Compute the address of the variable
        self.walk(ref.var)

        addr = ref.var.addr
        is_relative = ref.var.addr_is_relative
        if addr is None:
            raise InternalError("Address not found for reference")

        if is_relative:
            self.codegen.emit_push_frame_pointer()
            self.codegen.emit_push_constant(FundamentalType.INT_T, addr)
            self.codegen.emit_binary_op(
                ByteCodeOp.ADD, FundamentalType.CARD_T, FundamentalType.INT_T
            )
        else:
            self.codegen.emit_push_constant(FundamentalType.CARD_T, addr)

        # self.var_addr = None

        # elif scope == ByteCodeVariableScope.PARAM:
        #     self.codegen.emit_push_frame_pointer()
        #     # Subtract the 17-bit one's complement of the address for parameters
        #     addr -= 0x10000
        #     self.codegen.emit_push_constant(FundamentalType.CARD_T, addr)
        #     self.codegen.emit_binary_op(ByteCodeOp.SUBTRACT, FundamentalType.CARD_T)

        # var = ref.var
        # # TODO: Most of this is copy/paste from ast.Assign. Should refactor.
        # if self.symbol_table is None:
        #     raise InternalError("Symbol table not set")
        # entry, depth = self.symbol_table.find(var.name)
        # var_decl = cast(ast.VarDecl, entry.node)
        # if var_decl.addr is None:
        #     raise InternalError("Address not found")
        # if not isinstance(var_decl.var_t, FundamentalType):
        #     raise InternalError("Default variable access should be FundamentalType")
        # scope = ByteCodeVariableScope.GLOBAL
        # if depth > 0:
        #     if var_decl.addr < 0:
        #         scope = ByteCodeVariableScope.PARAM
        #     else:
        #         scope = ByteCodeVariableScope.LOCAL
        # self.codegen.emit_load_variable(
        #     var_decl.var_t,
        #     scope,
        #     ByteCodeVariableAddressMode.REFERENCE,
        #     var_decl.addr,
        # )
        # xxxx
        # if expr.fund_t.size_bytes != var_decl.var_t.size_bytes:
        #     # Emit a cast
        #     self.codegen.emit_cast(expr.fund_t, var_decl.var_t)
        # self.codegen.emit_store_variable(
        #     var_decl.var_t,
        #     scope,
        #     ByteCodeVariableAddressMode.DEFAULT,
        #     var_decl.addr,
        # )

    @walk.register
    def _(self, deref: ast.Dereference):
        # Push the address of the variable onto the stack
        self.walk(deref.var)

        # addr = deref.var.addr
        # is_relative = deref.var.addr_is_relative
        # if addr is None:
        #     raise InternalError("Address not found for dereference")

        # self.codegen.emit_push_constant(FundamentalType.CARD_T, addr)

        # # var_t = deref.var.var_t
        # if not isinstance(var_t, PointerType):
        #     raise InternalError("Dereference should be PointerType")
        # var_fund_t = cast(PointerType, var_t).reference_type

        # TODO: Deal with pointer to record type. For now, assume it's a fundamental type.
        # if not isinstance(var_fund_t, FundamentalType):
        #     raise InternalError("Dereference to non-FundamentalType not supported")

        # Load the value from the address. The new value on the stack will be the
        # address of the value to be dereferenced.
        # if is_relative:
        #     self.codegen.emit_load_relative(
        #         FundamentalType.CARD_T
        #     )  # deref.fund_t) # TODO: Clean up commennted code here
        # else:
        self.codegen.emit_load_absolute(FundamentalType.CARD_T)  # deref.fund_t)

        # addr = self.resolve_address(deref)
        # scope = self.resolve_scope(deref, addr)
        # var = deref.var
        # self.codegen.emit_load_variable(
        #     var.fund_t, scope, ByteCodeVariableAddressMode.POINTER, addr
        # )

        # var = deref.var
        # if self.symbol_table is None:
        #     raise InternalError("Symbol table not set")
        # # TODO: More copy/paste from ast.Assign
        # entry, depth = self.symbol_table.find(var.name)
        # var_decl = cast(ast.VarDecl, entry.node)
        # if var_decl.addr is None:
        #     raise InternalError("Address not found")
        # if not isinstance(var_decl.var_t, PointerType):
        #     raise InternalError("Dereference should be PointerType")
        # scope = ByteCodeVariableScope.GLOBAL
        # if depth > 0:
        #     if var_decl.addr < 0:
        #         scope = ByteCodeVariableScope.PARAM
        #     else:
        #         scope = ByteCodeVariableScope.LOCAL
        # pointer_t = cast(PointerType, var_decl.var_t)
        # self.codegen.emit_load_variable(
        #     pointer_t.reference_type,
        #     scope,
        #     ByteCodeVariableAddressMode.POINTER,
        #     var_decl.addr,
        # )

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

        # Push the result of the expression onto the stack
        self.walk(expr)

        if expr.fund_t.size_bytes != target.fund_t.size_bytes:
            # Emit a cast
            self.codegen.emit_cast(expr.fund_t, target.fund_t)

        # addr = self.resolve_address(target)

        # scope = self.resolve_scope(target)

        # self.is_lhs = True

        # Push the address of the target onto the stack
        self.walk(target)

        # TODO : Deal with non-Var targets
        if type(target) == ast.Var:  # isinstance(target, ast.Var):
            target_var = cast(ast.Var, target)
            # addr = target_var.addr
            is_relative = target_var.addr_is_relative

            # if addr is None:
            #     raise InternalError("Address not found for assign target")

            # self.codegen.emit_push_constant(FundamentalType.CARD_T, addr)

            if is_relative:
                self.codegen.emit_store_relative(target.fund_t)
            else:
                self.codegen.emit_store_absolute(target.fund_t)
        elif isinstance(target, ast.Dereference):
            # Walking the dereference pushed the pointer value onto the stack.
            # Note: The pointer value is always the runtime absolute address.
            self.codegen.emit_store_absolute(target.fund_t)
        elif isinstance(target, ast.ArrayAccess):
            # Walking the array access pushed the array base address onto the stack,
            # so here we need to push the index value onto the stack and add it
            # to the base address to get the actual address.
            self.codegen.emit_store_absolute(target.fund_t)
            # array_access = cast(ast.ArrayAccess, target)
            # self.walk(array_access.index)
            # self.codegen.emit_binary_op(
            #     ByteCodeOp.ADD, FundamentalType.CARD_T, FundamentalType.CARD_T
            # )
        else:
            raise InternalError(f"Unsupported assignment target {target}")

        # if isinstance(target, ast.Var):
        #     var = cast(ast.Var, target)
        #     if self.symbol_table is None:
        #         raise InternalError("Symbol table not set")
        #     entry, depth = self.symbol_table.find(var.name)
        #     var_decl = cast(ast.VarDecl, entry.node)
        #     if var_decl.addr is None:
        #         raise InternalError("Address not found")
        #     scope = ByteCodeVariableScope.GLOBAL
        #     if depth > 0:
        #         if var_decl.addr < 0:
        #             scope = ByteCodeVariableScope.PARAM
        #         else:
        #             scope = ByteCodeVariableScope.LOCAL
        #     # if isinstance(var_decl.var_t, PointerType):
        #     #     self.codegen.emit_store_variable(
        #     #         FundamentalType.CARD_T,
        #     #         scope,
        #     #         ByteCodeVariableAddressMode.DEFAULT,
        #     #         var_decl.addr,
        #     #     )
        #     if isinstance(var_decl.var_t, FundamentalType) or isinstance(
        #         var_decl.var_t, PointerType
        #     ):
        #         if expr.fund_t.size_bytes != var.fund_t.size_bytes:
        #             # Emit a cast
        #             self.codegen.emit_cast(expr.fund_t, var.fund_t)
        #         self.codegen.emit_store_variable(
        #             var.fund_t,
        #             scope,
        #             ByteCodeVariableAddressMode.DEFAULT,
        #             var_decl.addr,
        #         )
        #     else:
        #         raise InternalError(
        #             f"Unsupported assignment target type {var_decl.var_t}"
        #         )
        # elif isinstance(target, ast.ArrayAccess):
        #     raise NotImplementedError()
        # elif isinstance(target, ast.Dereference):
        #     raise NotImplementedError()
        # elif isinstance(target, ast.FieldAccess):
        #     raise NotImplementedError()
        # else:
        #     raise InternalError("Unsupported assignment target")

    @walk.register
    def _(self, numerical_const: ast.NumericalConst):
        self.codegen.emit_push_constant(numerical_const.expr_t, numerical_const.value)

    # @walk.register
    # def _(self, var: ast.Var):
    #     if self.symbol_table is None:
    #         raise InternalError("Symbol table not set")
    #     entry, depth = self.symbol_table.find(var.name)
    #     var_decl = cast(ast.VarDecl, entry.node)
    #     if var_decl.addr is None:
    #         raise InternalError("Address not found")
    #     if not isinstance(var_decl.var_t, FundamentalType):
    #         raise InternalError("Default variable access should be FundamentalType")
    #     # scope = ByteCodeVariableScope.GLOBAL
    #     if depth > 0:
    #         # Local or parameter
    #         self.codegen.emit_push_constant(FundamentalType.INT_T, var_decl.addr)
    #         self.codegen.emit_load_relative(var_decl.var_t)
    #     else:
    #         # Global
    #         self.codegen.emit_push_constant(FundamentalType.CARD_T, var_decl.addr)
    #         self.codegen.emit_load_absolute(var_decl.var_t)

    #     if var_decl.addr < 0:
    #         scope = ByteCodeVariableScope.PARAM
    #     else:
    #         scope = ByteCodeVariableScope.LOCAL
    # self.codegen.emit_load_variable(
    #     var_decl.var_t,
    #     scope,
    #     ByteCodeVariableAddressMode.DEFAULT,
    #     var_decl.addr,
    # )

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
        if return_node.expr is None:
            self.codegen.emit_return(FundamentalType.VOID_T)
        else:
            self.walk(return_node.expr)
            if self.current_routine is None:
                raise InternalError("Current routine not set")
            return_t = self.current_routine.return_t
            if return_t.size_bytes != return_node.expr.fund_t.size_bytes:
                self.codegen.emit_cast(return_node.expr.fund_t, return_t)
            self.codegen.emit_return(return_t)

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

    def resolve_address(self, node: ast.Node) -> int:
        if isinstance(node, ast.Var):
            var = cast(ast.Var, node)
            if self.symbol_table is None:
                raise InternalError("Symbol table not set")
            entry, depth = self.symbol_table.find(var.name)
            var_decl = cast(ast.VarDecl, entry.node)
            if var_decl.addr is None:
                raise InternalError(f"Address not found for variable {var.name}")
            return var_decl.addr
        elif isinstance(node, ast.Dereference):
            deref = cast(ast.Dereference, node)
            return self.resolve_address(deref.var)
        elif isinstance(node, ast.Reference):
            ref = cast(ast.Reference, node)
            return self.resolve_address(ref.var)
        elif isinstance(node, ast.FieldAccess):
            field_access = cast(ast.FieldAccess, node)
            base_addr = self.resolve_address(field_access.var)
            raise InternalError("FieldAccess not implemented for resolve_address")
        elif isinstance(node, ast.ArrayAccess):
            array_access = cast(ast.ArrayAccess, node)
            # Actual address is base address + item size * index
            # But the index is an expression, so we can't just compute it at compile time.
            # (Though maybe there could be a way to optimize this for constant indexes?)
            # Instead, we'll walk the index expression and then emit the calculation
            # on the stack. The VM will then pop the index and calculate the address.
            self.walk(array_access.index)
            return self.resolve_address(array_access.var)
        raise InternalError(f"Cannot resolve address for node type {node}")

    def resolve_scope(self, node: ast.Node) -> ByteCodeVariableScope:
        var_node = None
        if isinstance(node, ast.Var):
            var_node = cast(ast.Var, node)
        elif isinstance(node, ast.Dereference):
            deref_node = cast(ast.Dereference, node)
            var_node = deref_node.var
        elif isinstance(node, ast.Reference):
            ref_node = cast(ast.Reference, node)
            var_node = ref_node.var
        elif isinstance(node, ast.FieldAccess):
            field_access_node = cast(ast.FieldAccess, node)
            var_node = field_access_node.var
        elif isinstance(node, ast.ArrayAccess):
            array_access_node = cast(ast.ArrayAccess, node)
            var_node = array_access_node.var

        if var_node is None:
            raise InternalError(f"Cannot resolve scope for node type {node}")
        if self.symbol_table is None:
            raise InternalError("Symbol table not set")
        entry, depth = self.symbol_table.find(var_node.name)
        if entry is None:
            raise InternalError(f"Variable {var_node.name} not found")
        if depth > 0:
            return ByteCodeVariableScope.LOCAL
        return ByteCodeVariableScope.GLOBAL
