from enum import Enum, auto
from typing import cast

from retraction.error import InternalError
from retraction.types import (
    ArrayType,
    FundamentalType,
    RecordType,
    Type,
    binary_expression_type,
    cast_to_fundamental,
)


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
    def __init__(self, initial_values: list[int], is_address: bool):
        self.initial_values = initial_values
        self.is_address = is_address

    def __repr__(self) -> str:
        return f"InitOpts({self.initial_values}, {self.is_address})"


class Decl(Node):
    pass


class VarDecl(Decl):
    def __init__(self, name: str, var_t: Type, init_opts: InitOpts | None):
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
    # TODO: Look into python typing.Protocol to enforce this statically
    @property
    def fund_t(self) -> FundamentalType:
        raise NotImplementedError("Every expression must have a fundamental type")


class Var(Expr):
    def __init__(self, symbol_name: str, var_t: Type):
        self.symbol_name = symbol_name
        self.var_t = var_t

    def __repr__(self) -> str:
        return f"Var({self.symbol_name}, {self.var_t})"

    @property
    def fund_t(self) -> FundamentalType:
        return cast_to_fundamental(self.var_t)


class Dereference(Expr):
    def __init__(self, expr: Expr):
        self.expr = expr

    def __repr__(self) -> str:
        return f"Dereference({self.expr})"

    @property
    def fund_t(self) -> FundamentalType:
        # Any valid dereference refers to a pointer type
        return cast(Var, self.expr).fund_t


class Reference(Expr):
    def __init__(self, expr: Expr):
        self.expr = expr

    def __repr__(self) -> str:
        return f"Reference({self.expr})"

    @property
    def fund_t(self) -> FundamentalType:
        return FundamentalType.CARD_T


class FieldAccess(Expr):
    def __init__(self, expr: Expr, field_name: str):
        self.expr = expr
        self.field_name = field_name

    def __repr__(self) -> str:
        return f"FieldAccess({self.expr}, {self.field_name})"

    @property
    def fund_t(self) -> FundamentalType:
        # A valid field access refers to a var
        access_var = cast(Var, self.expr)
        # Look up the field name in the struct
        struct_t = cast(RecordType, access_var.var_t)
        for field in struct_t.fields:
            if field[0] == self.field_name:
                return field[1]
        raise InternalError(f"Field {self.field_name} not found in struct {struct_t}")


class ArrayAccess(Expr):
    def __init__(self, expr: Expr, index: Expr):
        self.expr = expr
        self.index = index

    def __repr__(self) -> str:
        return f"ArrayAccess({self.expr}, {self.index})"

    @property
    def fund_t(self) -> FundamentalType:
        # A valid array access refers to a var
        access_var = cast(Var, self.expr)
        array_t = cast(ArrayType, access_var.var_t)
        return array_t.element_t


# class PointerVar(Var):
#     def __init__(self, symbol_name: str):
#         self.symbol_name = symbol_name

#     def __repr__(self) -> str:
#         return f"PointerVar({self.symbol_name})"


# class ArrayVar(Var):
#     def __init__(self, symbol_name: str, index: Expr):
#         self.symbol_name = symbol_name
#         self.index = index

#     def __repr__(self) -> str:
#         return f"ArrayVar({self.symbol_name}, {self.index})"


# class StructVar(Var):
#     def __init__(self, symbol_name: str, field_name: str):
#         self.symbol_name = symbol_name
#         self.field_index = field_name

#     def __repr__(self) -> str:
#         return f"StructVar({self.symbol_name}, {self.field_index})"


# class ReferenceVar(Var):
#     def __init__(self, symbol_name: str):
#         self.symbol_name = symbol_name

#     def __repr__(self) -> str:
#         return f"ReferenceVar({self.symbol_name})"


class Assign(Statement):
    def __init__(self, target: Expr, expr: Expr):
        self.target = target
        self.expr = expr

    def __repr__(self) -> str:
        return f"Assign({self.target}, {self.expr})"


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
        var_target: Var,
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

        # Determine the type of the expression based on the operator and operands
        if op.is_conditional():
            self.expr_t = FundamentalType.BYTE_T
        elif op in [Op.MOD, Op.DIV, Op.MUL]:
            self.expr_t = FundamentalType.INT_T
        else:
            # Most binary expression types are derived from the types of their operands
            self.expr_t = binary_expression_type(left.fund_t, right.fund_t)

    def __repr__(self) -> str:
        return f"BinaryExpr({self.op}, {self.left}, {self.right})"

    @property
    def fund_t(self) -> FundamentalType:
        return self.expr_t


class UnaryExpr(Expr):
    def __init__(self, op: Op, expr: Expr):
        self.op = op
        self.expr = expr

    def __repr__(self) -> str:
        return f"UnaryExpr({self.op}, {self.expr})"

    @property
    def fund_t(self) -> FundamentalType:
        # The only unary operator is negation, which is implicitly INT
        return FundamentalType.INT_T


class Routine(Node):
    def __init__(
        self,
        name: str,
        params: list[VarDecl],
        decls: list[Decl] | None,
        body: list[Statement] | None,
        fixed_addr: int | None,
        return_t: FundamentalType | None,
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


class Call(Expr):
    def __init__(self, name: str, args: list[Expr], return_t: FundamentalType | None):
        self.name = name
        self.args = args
        self.return_t = return_t

    def __repr__(self) -> str:
        return f"Call({self.name}, {self.args}, {self.return_t})"

    @property
    def fund_t(self) -> FundamentalType:
        if self.return_t is None:
            raise InternalError("Call expression has no return type")
        return cast_to_fundamental(self.return_t)


class CallStmt(Statement):
    def __init__(self, call: Call):
        self.call = call

    def __repr__(self) -> str:
        return f"CallStmt({self.call})"


class NumericConst(Expr):
    def __init__(self, value: int):
        self.value = value

        if value < 0 or value < 0x8000:
            self.expr_t = FundamentalType.INT_T
        elif value < 256:
            self.expr_t = FundamentalType.BYTE_T
        else:
            self.expr_t = FundamentalType.CARD_T

    def __repr__(self) -> str:
        return f"Const({self.value})"

    @property
    def fund_t(self) -> FundamentalType:
        return self.expr_t


# class GetVar(Expr):
#     def __init__(self, var: Var):
#         self.var = var

#     def __repr__(self) -> str:
#         return f"GetVar({self.var})"


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

    def visit_setvar(self, assign: Assign):
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

    def visit_call(self, call: Call):
        raise NotImplementedError()

    def visit_call_stmt(self, call_stmt: CallStmt):
        raise NotImplementedError()

    def visit_numeric_const(self, numeric_const: NumericConst):
        raise NotImplementedError()

    def visit_init_opts(self, init_opts: InitOpts):
        raise NotImplementedError()
