from retraction import ast
from retraction.codegen import ByteCodeGen


class BCVisitor(ast.Visitor):
    def __init__(self, codegen: ByteCodeGen):
        self.codegen = codegen

        self.symbol_table: ast.SymTab | None = None
        self.current_routine: ast.Routine | None = None

    def visit_program(self, program: ast.Program):
        self.symbol_table = program.symbol_table
        for module in program.modules:
            module.accept(self)

    def visit_module(self, module: ast.Module):
        for decl in module.decls:
            decl.accept(self)

        for routine in module.routines:
            routine.accept(self)

    def visit_var_decl(self, var_decl: ast.VarDecl):
        is_global = self.current_routine is None
        # Global vars are emitted as raw data
        if is_global:
            addr = self.codegen.emit_global_data(var_decl)
            var_decl.addr = addr

    def visit_routine(self, routine: ast.Routine):
        self.current_routine = routine
        routine.addr = self.codegen.get_next_addr()
        # TODO: Probably no need to visit params and local decls? The routine call makes use of these through the symbol table
        # for param in routine.params:
        #     param.accept(self)
        # if routine.decls is not None:
        #     for decl in routine.decls:
        #         decl.accept(self)
        if routine.statements is not None:
            for statement in routine.statements:
                statement.accept(self)
        self.current_routine = None
