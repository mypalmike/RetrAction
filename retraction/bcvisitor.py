from functools import singledispatchmethod
from typing import cast
from retraction import ast
from retraction.bytecode import ByteCodeVariableAddressMode, ByteCodeVariableScope
from retraction.codegen import ByteCodeGen
from retraction.error import InternalError
from retraction.types import ArrayType, FundamentalType, PointerType, RecordType
from retraction import symtab


class BCWalk:
    def __init__(self, codegen: ByteCodeGen):
        self.codegen = codegen

        self.symbol_table: symtab.SymTab | None = None
        self.current_routine: ast.Routine | None = None
        self.next_param_addr: int | None = None
        self.next_local_addr: int | None = None
        self.local_parameter_index: int = 0

    @singledispatchmethod
    def walk(self, node: ast.Node):
        raise InternalError(f"Unsupported node type {type(node)}")

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
                    size_bytes = element_t.size_bytes()
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
                addr = self.codegen.emit_bytes([0] * record_t.size_bytes())
            elif isinstance(var_decl.var_t, FundamentalType):
                fund_t = cast(FundamentalType, var_decl.var_t)
                values = [0]
                if init_opts is not None:
                    values = init_opts.initial_values
                size_bytes = fund_t.size_bytes()
                if size_bytes == 1:
                    addr = self.codegen.emit_bytes(values)
                elif size_bytes == 2:
                    addr = self.codegen.emit_shorts(values)
                else:
                    raise InternalError(f"Unsupported variable type {var_decl.var_t}")
            var_decl.addr = addr
        elif self.next_param_addr is not None:
            # Assign an offset address to the parameter.
            var_decl.addr = self.next_param_addr
            size_bytes = 0
            if isinstance(var_decl.var_t, FundamentalType):
                size_bytes = var_decl.var_t.size_bytes()
            elif isinstance(var_decl.var_t, PointerType):
                size_bytes = 2
            elif isinstance(var_decl.var_t, ArrayType):
                # TODO: Arrays are passed as pointers?
                size_bytes = 2
            elif isinstance(var_decl.var_t, RecordType):
                raise InternalError("RecordType not supported for parameters")
            self.next_param_addr -= size_bytes
        elif self.next_local_addr is not None:
            # Assign an offset address to the local variable.
            var_decl.addr = self.next_local_addr
            self.next_local_addr += var_decl.var_t.size_bytes()

            # Local var initialization is emitted as instructions
            if var_decl.init_opts is not None:
                self.codegen.emit_numerical_constant(
                    var_decl.init_opts.initial_values[self.local_parameter_index]
                )
                self.codegen.emit_store_variable(
                    var_decl.var_t,
                    ByteCodeVariableScope.LOCAL,
                    ByteCodeVariableAddressMode.DEFAULT,
                    var_decl.addr,
                )

    @walk.register
    def _(self, routine: ast.Routine):
        self.current_routine = routine
        routine.addr = self.codegen.get_next_addr()
        # Reverse the parameter list
        if routine.params is not None:
            try:
                self.next_param_addr = -6  # initial offset from frame pointer
                for param in reversed(routine.params):
                    self.walk(param)
            finally:
                self.next_param_addr = None
        if routine.decls is not None:
            try:
                self.next_local_addr = 0
                self.local_parameter_index = 0
                for decl in routine.decls:
                    self.walk(decl)
            finally:
                self.next_local_addr = None
        if routine.statements is not None:
            for statement in routine.statements:
                self.walk(statement)
        self.current_routine = None

    @walk.register
    def _(self, assign: ast.Assign):
        target = assign.target
        expr = assign.expr
        self.walk(expr)
        if isinstance(target, ast.Var):
            var = cast(ast.Var, target)
            if self.symbol_table is None:
                raise InternalError("Symbol table not set")
            var_decl = cast(ast.VarDecl, self.symbol_table.find(var.name))
            if var_decl.addr is None:
                raise InternalError("Address not found")
            if not isinstance(var_decl.var_t, FundamentalType):
                raise InternalError("Default variable access should be FundamentalType")
            self.codegen.emit_store_variable(
                var_decl.var_t,
                ByteCodeVariableScope.GLOBAL,  # TODO: Get scope based on var, probably needs to be stored during parse.
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
