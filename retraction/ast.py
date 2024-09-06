from enum import Enum, auto

from retraction.types import Type


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


class InitOpts:
    def __init__(self, initial_value: int = 0, is_address: bool = False):
        self.initial_value = initial_value
        self.is_address = is_address


class Node:
    pass


class Program(Node):
    def __init__(self, modules: list[Module]):
        self.modules = modules

    def __repr__(self) -> str:
        return f"Program({self.modules})"


class Module(Node):
    def __init__(self, decls: DeclList, routines: list[Routine]):
        self.decls = decls
        self.routines = routines

    def __repr__(self) -> str:
        return f"Module({self.decls}, {self.routines})"


class DeclList(Node):
    def __init__(self, decls: list[Decl]):
        self.decls = decls

    def __repr__(self) -> str:
        return f"DeclList({self.decls})"


class Decl(Node):
    pass


class VarDecl(Decl):
    def __init__(self, name: str, var_t: Type, init_opts: InitOpts):
        self.name = name
        self.var_t = var_t
        self.init_opts = init_opts
        self.symtab_index = None

    def __repr__(self) -> str:
        return f"VarDecl({self.name}, {self.var_t}, {self.init_opts})"


class StructDecl(Decl):
    def __init__(self, name: str, fields: StructFieldList):
        self.name = name
        self.fields = fields

    def __repr__(self) -> str:
        return f"StructDecl({self.name}, {self.fields})"


class StructFieldList(Node):
    def __init__(self, fields: list[VarDecl]):
        self.fields = fields

    def __repr__(self) -> str:
        return f"StructFieldList({self.fields})"


class StatementList(Node):
    def __init__(self, statements: list[Statement]):
        self.statements = statements

    def __repr__(self) -> str:
        return f"StatementList({self.statements})"


class Statement(Node):
    pass


class Assign(Statement):
    def __init__(self, var_node: VarDecl, expr: Expr):
        self.var_node = var_node
        self.expr = expr

    def __repr__(self) -> str:
        return f"Assign({self.var_node.name}, {self.expr})"


class Expr(Node):
    pass


class Conditional(Node):
    def __init__(self, condition: Expr, body: list[Statement]):
        self.condition = condition
        self.body = body

    def __repr__(self) -> str:
        return f"Conditional({self.condition}, {self.body})"


class If(Statement):
    def __init__(self, conditionals: list[Conditional], else_body: list[Statement]):
        self.conditionals = conditionals
        self.else_body = else_body

    def __repr__(self) -> str:
        return f"If({self.conditionals}, {self.else_body})"


class Do(Statement):
    def __init__(self, body: list[Statement]):
        self.body = body

    def __repr__(self) -> str:
        return f"Do({self.body})"


class While(Statement):
    def __init__(self, condition: Expr, body: list[Statement]):
        self.condition = condition
        self.body = body

    def __repr__(self) -> str:
        return f"While({self.condition}, {self.body})"


class Until(Statement):
    def __init__(self, condition: Expr, body: list[Statement]):
        self.condition = condition

    def __repr__(self) -> str:
        return f"Until({self.condition}"


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


class RoutineList(Node, list[Routine]):
    def __init__(self, routines: list[Routine]):
        self.routines = routines

    def __repr__(self) -> str:
        return f"RoutineList({self.routines})"


class Routine(Node):
    def __init__(
        self,
        name: str,
        params: list[VarDecl],
        decl_list: DeclList | None,
        body: list[Statement] | None,
        fixed_addr: int | None,
        return_t: Type | None,
        symtab_index: int | None,
    ):
        self.name = name
        self.params = params
        self.decl_list = decl_list
        self.body = body
        self.fixed_addr = fixed_addr
        self.return_t = return_t
        self.symtab_index = symtab_index

    def __repr__(self) -> str:
        return f"Routine({self.name}, {self.params}, {self.decl_list}, {self.body}, {self.return_t})"
