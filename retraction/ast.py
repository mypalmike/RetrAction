from enum import Enum, auto

from retraction.types import Type


# Forward declarations to handle circular dependencies.
# TODO: This works OK but should refactor to remove circular dependencies.
class Visitor:
    pass


class SymTab:
    pass


class Op(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    LSH = auto()
    RSH = auto()
    EQ = auto()
    NE = auto()
    GT = auto()
    GE = auto()
    LT = auto()
    LE = auto()
    XOR = auto()
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_XOR = auto()

    def is_conditional(self):
        return self in [Op.EQ, Op.NE, Op.GT, Op.GE, Op.LT, Op.LE]


class Node:
    def accept(self, visitor: Visitor):
        raise NotImplementedError()


class InitOpts(Node):
    def __init__(self, initial_value: int = 0, is_address: bool = False):
        self.initial_value = initial_value
        self.is_address = is_address

    def __repr__(self) -> str:
        return f"InitOpts({self.initial_value}, {self.is_address})"


class Decl(Node):
    pass


class VarDecl(Decl):
    def __init__(self, name: str, var_t: Type, init_opts: InitOpts):
        self.name = name
        self.var_t = var_t
        self.init_opts = init_opts

    def __repr__(self) -> str:
        return f"VarDecl({self.name}, {self.var_t}, {self.init_opts})"


class StructDecl(Decl):
    def __init__(self, name: str, fields: list[VarDecl]):
        self.name = name
        self.fields = fields

    def __repr__(self) -> str:
        return f"StructDecl({self.name}, {self.fields})"


class Statement(Node):
    pass


class Expr(Node):
    pass


class Var(Node):
    pass


class SimpleVar(Var):
    def __init__(self, symbol_name: str):
        self.symbol_name = symbol_name

    def __repr__(self) -> str:
        return f"SimpleVar({self.symbol_name})"


class PointerVar(Var):
    def __init__(self, symbol_name: str):
        self.symbol_name = symbol_name

    def __repr__(self) -> str:
        return f"PointerVar({self.symbol_name})"


class ArrayVar(Var):
    def __init__(self, symbol_name: str, index: Expr):
        self.symbol_name = symbol_name
        self.index = index

    def __repr__(self) -> str:
        return f"ArrayVar({self.symbol_name}, {self.index})"


class StructVar(Var):
    def __init__(self, symbol_name: str, field_name: str):
        self.symbol_name = symbol_name
        self.field_index = field_name

    def __repr__(self) -> str:
        return f"StructVar({self.symbol_name}, {self.field_index})"


class ReferenceVar(Var):
    def __init__(self, symbol_name: str):
        self.symbol_name = symbol_name

    def __repr__(self) -> str:
        return f"ReferenceVar({self.symbol_name})"


class SetVar(Statement):
    def __init__(self, var_target: Var, expr: Expr):
        self.var_target = var_target
        self.expr = expr

    def __repr__(self) -> str:
        return f"Assign({self.var_target}, {self.expr})"


class Conditional(Node):
    def __init__(self, condition: Expr, body: list[Statement]):
        self.condition = condition
        self.body = body

    def __repr__(self) -> str:
        return f"Conditional({self.condition}, {self.body})"


class If(Statement):
    def __init__(
        self, conditionals: list[Conditional], else_body: list[Statement] | None
    ):
        self.conditionals = conditionals
        self.else_body = else_body

    def __repr__(self) -> str:
        return f"If({self.conditionals}, {self.else_body})"


class Do(Statement):
    def __init__(self, body: list[Statement], until: Expr | None):
        self.body = body
        self.until = until

    def __repr__(self) -> str:
        return f"Do({self.body}, {self.until})"


class While(Statement):
    def __init__(self, condition: Expr, do_statement: Do):
        self.condition = condition
        self.do_statement = do_statement

    def __repr__(self) -> str:
        return f"While({self.condition}, {self.do_statement})"


class Until(Statement):
    def __init__(self, condition: Expr, body: list[Statement]):
        self.condition = condition

    def __repr__(self) -> str:
        return f"Until({self.condition}"


class For(Statement):
    def __init__(
        self,
        var_target: SimpleVar,
        start_expr: Expr,
        finish_expr: Expr,
        inc_expr: Expr,
        do_loop: Do,
    ):
        self.var_target = var_target
        self.start_expr = start_expr
        self.finish_expr = finish_expr
        self.inc_expr = inc_expr
        self.do_loop = do_loop

    def __repr__(self) -> str:
        return f"For({self.var_target}, {self.start_expr}, {self.finish_expr}, {self.inc_expr}, {self.do_loop})"


class Exit(Statement):
    def __init__(self):
        pass

    def __repr__(self) -> str:
        return f"Exit()"


class CodeBlock(Statement):
    def __init__(self, values: list[int]):
        self.values = values

    def __repr__(self) -> str:
        return f"CodeBlock({self.values})"


class Return(Statement):
    def __init__(self, expr: Expr | None):
        self.expr = expr

    def __repr__(self) -> str:
        return f"Return({self.expr})"


class DevPrint(Statement):
    def __init__(self, expr: Expr):
        self.expr = expr

    def __repr__(self) -> str:
        return f"DevPrint({self.expr})"


class BinaryExpr(Expr):
    def __init__(self, op: Op, left: Expr, right: Expr):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"BinaryExpr({self.op}, {self.left}, {self.right})"


class UnaryExpr(Expr):
    def __init__(self, op: Op, expr: Expr):
        self.op = op
        self.expr = expr

    def __repr__(self) -> str:
        return f"UnaryExpr({self.op}, {self.expr})"


class Routine(Node):
    def __init__(
        self,
        name: str,
        params: list[VarDecl],
        decls: list[Decl] | None,
        body: list[Statement] | None,
        fixed_addr: int | None,
        return_t: Type | None,
        local_symtab: SymTab | None,
    ):
        self.name = name
        self.params = params
        self.decls = decls
        self.body = body
        self.fixed_addr = fixed_addr
        self.return_t = return_t
        self.local_symtab = local_symtab

    def __repr__(self) -> str:
        return f"Routine({self.name}, {self.params}, {self.decls}, {self.body}, {self.fixed_addr}, {self.return_t})"


class RoutineCall(Expr):
    def __init__(self, name: str, args: list[Expr]):
        self.name = name
        self.args = args

    def __repr__(self) -> str:
        return f"RoutineCall({self.name}, {self.args})"


class RoutineCallStmt(Statement):
    def __init__(self, routine_call: RoutineCall):
        self.routine_call = routine_call

    def __repr__(self) -> str:
        return f"RoutineCallStmt({self.routine_call})"


class NumericConst(Expr):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self) -> str:
        return f"Const({self.value})"


class GetVar(Expr):
    def __init__(self, var: Var):
        self.var = var

    def __repr__(self) -> str:
        return f"GetVar({self.var})"


class Module(Node):
    def __init__(
        self,
        decls: list[Decl],
        routines: list[Routine],
    ):
        self.decls = decls
        self.routines = routines

    def __repr__(self) -> str:
        return f"Module({self.decls}, {self.routines})"


class Program(Node):
    def __init__(self, modules: list[Module], symbol_table: SymTab):
        self.modules = modules
        self.symbol_table = symbol_table

    def __repr__(self) -> str:
        return f"Program({self.modules})"


class Visitor:  # type: ignore
    def visit_program(self, program: Program):
        raise NotImplementedError()

    def visit_module(self, module: Module):
        raise NotImplementedError()

    def visit_var_decl(self, var_decl: VarDecl):
        raise NotImplementedError()

    def visit_struct_decl(self, struct_decl: StructDecl):
        raise NotImplementedError()

    def visit_assign(self, assign: SetVar):
        raise NotImplementedError()

    def visit_binary_expr(self, binary_expr: BinaryExpr):
        raise NotImplementedError()

    def visit_unary_expr(self, unary_expr: UnaryExpr):
        raise NotImplementedError()

    def visit_conditional(self, conditional: Conditional):
        raise NotImplementedError()

    def visit_if(self, if_stmt: If):
        raise NotImplementedError()

    def visit_do(self, do_stmt: Do):
        raise NotImplementedError()

    def visit_while(self, while_stmt: While):
        raise NotImplementedError()

    def visit_until(self, until_stmt: Until):
        raise NotImplementedError()

    def visit_exit(self, exit_stmt: Exit):
        raise NotImplementedError()

    def visit_code_block(self, code_block: CodeBlock):
        raise NotImplementedError()

    def visit_return(self, return_stmt: Return):
        raise NotImplementedError()

    def visit_dev_print(self, dev_print: DevPrint):
        raise NotImplementedError()

    def visit_routine(self, routine: Routine):
        raise NotImplementedError()
