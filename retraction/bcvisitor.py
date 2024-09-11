from retraction import ast
from retraction.codegen import ByteCodeGen


class BCVisitor(ast.Visitor):
    def __init__(self, codegen: ByteCodeGen):
        self.codegen = codegen

        self.symbol_table: ast.SymTab | None = None
        self.current_routine = None

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
            self.codegen.emit_global_data(var_decl)
