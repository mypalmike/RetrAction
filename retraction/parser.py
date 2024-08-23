from enum import Enum, auto
import sys

from retraction.tokens import Token, TokenType
from retraction.codegen import ByteCodeGen
from retraction.bytecode import (
    ByteCodeOp,
    ByteCodeVariableAddressMode,
    ByteCodeVariableScope,
)
from retraction.error import InternalError, SyntaxError
from retraction.symtab import SymbolTable
from retraction.types import Type, Routine, RecordType


# Highest to lowest precedence:
# ( )
# - @
# * / MOD LSH RSH
# + -
# = # <> > >= < <=
# AND &
# OR %
# XOR !
class ExprPrecedence(Enum):
    NONE = 0
    XOR = 1
    OR = 2
    AND = 3
    COMPARE = 4
    TERM = 5
    FACTOR = 6
    UNARY = 7


class ExprAction(Enum):
    NONE = auto()
    NUMBER = auto()
    GROUPING = auto()
    UNARY = auto()
    BINARY = auto()
    AND = auto()
    OR = auto()
    IDENTIFIER = auto()


class ExprRule:
    def __init__(
        self,
        prefix: ExprAction,
        infix: ExprAction,
        precedence: ExprPrecedence,
    ):
        self.prefix = prefix
        self.infix = infix
        self.precedence = precedence

    def is_relational(self):
        return self.precedence in [
            ExprPrecedence.COMPARE,
            ExprPrecedence.AND,
            ExprPrecedence.OR,
            ExprPrecedence.XOR,
        ]


EXPRESSION_RULES = {
    TokenType.OP_LPAREN: ExprRule(
        ExprAction.GROUPING, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.OP_RPAREN: ExprRule(
        ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.OP_PLUS: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.TERM
    ),
    TokenType.OP_MINUS: ExprRule(
        ExprAction.UNARY, ExprAction.BINARY, ExprPrecedence.TERM
    ),
    TokenType.OP_TIMES: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
    ),
    TokenType.OP_DIVIDE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
    ),
    # TODO: Does precedence matter for this?
    TokenType.OP_AT: ExprRule(
        ExprAction.IDENTIFIER, ExprAction.NONE, ExprPrecedence.UNARY
    ),
    TokenType.MOD: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.LSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.RSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.OP_EQ: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_NE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_GT: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_GE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_LT: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_LE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.AND: ExprRule(ExprAction.NONE, ExprAction.AND, ExprPrecedence.AND),
    TokenType.OR: ExprRule(ExprAction.NONE, ExprAction.OR, ExprPrecedence.OR),
    TokenType.XOR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.XOR),
    TokenType.OP_BIT_AND: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.AND
    ),
    TokenType.OP_BIT_OR: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.OR
    ),
    TokenType.OP_BIT_XOR: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.XOR
    ),
    TokenType.INT_LITERAL: ExprRule(
        ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.HEX_LITERAL: ExprRule(
        ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.CHAR_LITERAL: ExprRule(
        ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.IDENTIFIER: ExprRule(
        ExprAction.IDENTIFIER, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.EOF: ExprRule(ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE),
}


class TypedExpressionOp(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
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
    UNARY_MINUS = auto()
    CONSTANT = auto()
    LOAD_VARIABLE = auto()
    # VARIABLE_REF = auto()
    # VARIABLE_PTR = auto()
    # GET_GLOBAL = auto()
    # GET_LOCAL = auto()
    # GET_PARAM = auto()
    FUNCTION_CALL = auto()


BINARY_OPS = {
    TypedExpressionOp.ADD,
    TypedExpressionOp.SUBTRACT,
    TypedExpressionOp.MULTIPLY,
    TypedExpressionOp.DIVIDE,
    TypedExpressionOp.MOD,
    TypedExpressionOp.LSH,
    TypedExpressionOp.RSH,
    TypedExpressionOp.EQ,
    TypedExpressionOp.NE,
    TypedExpressionOp.GT,
    TypedExpressionOp.GE,
    TypedExpressionOp.LT,
    TypedExpressionOp.LE,
    TypedExpressionOp.XOR,
    TypedExpressionOp.BIT_AND,
    TypedExpressionOp.BIT_OR,
    TypedExpressionOp.BIT_XOR,
}

RELATIONAL_OPS = {
    TypedExpressionOp.EQ,
    TypedExpressionOp.NE,
    TypedExpressionOp.GT,
    TypedExpressionOp.GE,
    TypedExpressionOp.LT,
    TypedExpressionOp.LE,
}


class TypedExpressionScope(Enum):
    GLOBAL = auto()
    LOCAL = auto()
    PARAM = auto()
    ROUTINE_REFERENCE = auto()


class TypedExpressionItem:
    def __init__(
        self,
        op: TypedExpressionOp,
        index: int | None = None,
    ):
        self.op = op
        # Index is used for constants, variables, and function calls
        self.index = index
        # Members below are computed when the item is added to a TypedPostfixExpression
        self.item_t: Tipe = None
        # For binary operations
        self.op1_const = False
        self.op2_const = False
        self.op1_t: Tipe = None
        self.op2_t: Tipe = None
        # For constants
        self.value: int = None
        # For variables
        self.address: int = None
        self.scope: TypedExpressionScope = None
        # self.is_pointer = False
        # self.is_reference = False


class TypedPostfixExpression:
    """
    A postfix expression in the form of a list of TypedExpressionItems.
    This is used as a temporary internal representation to generate bytecode
    for an expression while keeping track of the types of the expression at
    each step. This is necessary to generate the correct bytecode for things
    like adding a BYTE to an INT, particularly when the values are intermediate
    expression results.
    """

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.items: list[TypedExpressionItem] = []

    def append(self, item: TypedExpressionItem):
        op = item.op
        if op == TypedExpressionOp.UNARY_MINUS:
            # TODO: Weird case(s)? - -32768 -> 32768, which is not in INT range.
            # Might be a VM check, should automatically be handled on real CPU.
            item.item_t = self.items[-1].item_t
        elif op in RELATIONAL_OPS:
            item.item_t = Type.BYTE_T
        elif op in BINARY_OPS:
            item1, item2 = self.items[-2], self.items[-1]
            self.op1_const = item1.op == TypedExpressionOp.CONSTANT
            self.op2_const = item2.op == TypedExpressionOp.CONSTANT
            item1_t, item2_t = item1.item_t, item2.item_t
            self.op1_t, self.op2_t = item1_t, item2_t
            pri1, pri2 = item1_t.cast_priority(), item2_t.cast_priority()
            result_priority = max(pri1, pri2)
            if result_priority == 1:
                item.item_t = Type.BYTE_T
            elif result_priority == 2:
                item.item_t = Type.INT_T
            elif result_priority == 3:
                item.item_t = Type.CARD_T
            else:
                raise InternalError(f"Invalid cast priority: {result_priority}")
        elif op == TypedExpressionOp.CONSTANT:
            item.item_t = self.constant_type(item.index)
            item.value = self.symbol_table.constants[item.index]
        elif op == TypedExpressionOp.LOAD_VARIABLE:
            scope = item.scope
            if scope == TypedExpressionScope.GLOBAL:
                item.item_t = self.symbol_table.globals[item.index].var_tipe
                item.address = self.symbol_table.globals[item.index].address
            elif scope == TypedExpressionScope.LOCAL:
                item.item_t = self.symbol_table.locals[item.index].var_tipe
                item.address = self.symbol_table.locals[item.index].address
            elif scope == TypedExpressionScope.PARAM:
                item.item_t = self.symbol_table.params[item.index].var_tipe
                item.address = self.symbol_table.params[item.index].address
            elif scope == TypedExpressionScope.ROUTINE_REFERENCE:
                item.item_t = CARD_TIPE
                item.address = self.symbol_table.routines[item.index].address
            else:
                raise InternalError(f"Unknown scope: {scope}")

        #     item.tipe = self.symbol_table.globals[item.value][1]
        # elif op == TypedExpressionOp.GET_LOCAL:
        #     item.tipe = self.symbol_table.locals[item.value][1]
        # elif op == TypedExpressionOp.GET_PARAM:
        #     item.tipe = self.symbol_table.params[item.value][1]
        elif op == TypedExpressionOp.FUNCTION_CALL:
            item.item_t = self.symbol_table.routines[item.index].return_tipe
        else:
            raise InternalError(f"Unknown operation: {op}")
        self.items.append(item)

    def optimize(self):
        """
        Perform optimizations on the expression, such as constant folding.
        TODO:
        - Move constants to second operand for commutative and comparison operations,
            which is faster on many processors, including 6502.
        - Convert multiplication and division by powers of 2 to shifts.
        - Store followed by load of same variable can be removed.
        """
        curr_index = 0
        while curr_index < len(self.items):
            item = self.items[curr_index]
            op, tipe, _ = item.op, item.item_t, item.index

            if op in BINARY_OPS:
                item1 = self.items[curr_index - 2]
                item2 = self.items[curr_index - 1]
                # tipe1, tipe2 = item1.tipe, item2.tipe
                op1, op2, value1, value2 = item1.op, item2.op, item1.index, item2.index
                # Constant folding
                if (
                    op1 == TypedExpressionOp.CONSTANT
                    and op2 == TypedExpressionOp.CONSTANT
                ):
                    result, tipe = self.fold_constants(op, value1, value2)
                    # Create new constant and shift all following items down to fill in the gap.
                    self.items[curr_index - 2] = TypedExpressionItem(
                        TypedExpressionOp.CONSTANT, tipe, result
                    )
                    self.items[curr_index - 1 :] = self.items[curr_index + 1 :]
                    curr_index -= 2
            elif op == TypedExpressionOp.UNARY_MINUS:
                # Apply unary minus to constant. Many compilers do this during tokenization,
                # but the manual specifies it as a separate operation.
                item1 = self.items[curr_index - 1]
                op1, value1 = item1.op, item1.index

                if op1 == TypedExpressionOp.CONSTANT:
                    result = -value1
                    result = self.constant_normalize(result)
                    tipe = self.constant_type(result)
                    # Create new constant and shift all following items down to fill in the gap.
                    self.items[curr_index - 1] = TypedExpressionItem(
                        TypedExpressionOp.CONSTANT, tipe, result
                    )
                    self.items[curr_index:] = self.items[curr_index + 1 :]
                    curr_index -= 1

    def constant_normalize(self, value: int) -> int:
        if value < -32768 or value >= 65536:
            return value % 65536
        return value

    def constant_type(self, value: int) -> Tipe:
        if value >= 0 and value < 256:
            return BYTE_TIPE
        elif value >= -32768 and value < 32768:
            return INT_TIPE
        else:
            return CARD_TIPE

    def fold_constants(
        self, op: TypedExpressionOp, value1: int, value2: int
    ) -> tuple[int, Tipe]:
        if op == TypedExpressionOp.ADD:
            combined_result = value1 + value2
        elif op == TypedExpressionOp.SUBTRACT:
            combined_result = value1 - value2
        elif op == TypedExpressionOp.MULTIPLY:
            combined_result = value1 * value2
        elif op == TypedExpressionOp.DIVIDE:
            combined_result = value1 // value2
        elif op == TypedExpressionOp.MOD:
            combined_result = value1 % value2
        elif op == TypedExpressionOp.LSH:
            combined_result = value1 << value2
        elif op == TypedExpressionOp.RSH:
            combined_result = value1 >> value2
        elif op == TypedExpressionOp.EQ:
            combined_result = 1 if value1 == value2 else 0
        elif op == TypedExpressionOp.NE:
            combined_result = 1 if value1 != value2 else 0
        elif op == TypedExpressionOp.GT:
            combined_result = 1 if value1 > value2 else 0
        elif op == TypedExpressionOp.GE:
            combined_result = 1 if value1 >= value2 else 0
        elif op == TypedExpressionOp.LT:
            combined_result = 1 if value1 < value2 else 0
        elif op == TypedExpressionOp.LE:
            combined_result = 1 if value1 <= value2 else 0
        elif op == TypedExpressionOp.XOR:
            combined_result = int(bool(value1) ^ bool(value2))
        elif op == TypedExpressionOp.BIT_AND:
            combined_result = value1 & value2
        elif op == TypedExpressionOp.BIT_OR:
            combined_result = value1 | value2
        elif op == TypedExpressionOp.BIT_XOR:
            combined_result = value1 ^ value2
        else:
            raise InternalError(f"Unknown operation: {op}")

        # Computed result may be outside of 16-bit range, so normalize it.
        combined_result = self.constant_normalize(combined_result)

        # Select type most appropriate for range of result
        combined_tipe = self.constant_type(combined_result)

        return combined_result, combined_tipe

    def emit(self, code_gen: ByteCodeGen):
        for curr_index, item in enumerate(self.items):
            op, tipe, value = item.op, item.item_t, item.index
            if op == TypedExpressionOp.CONSTANT:
                code_gen.emit_numerical_constant(value, tipe)
            elif op == TypedExpressionOp.GET_GLOBAL:
                code_gen.emit_get_global(value, tipe)
            elif op == TypedExpressionOp.GET_LOCAL:
                code_gen.emit_get_local(value, tipe)
            elif op == TypedExpressionOp.GET_PARAM:
                code_gen.emit_get_param(value, tipe)
            elif op == TypedExpressionOp.FUNCTION_CALL:
                code_gen.emit_function_call(value, tipe)
            elif op in BINARY_OPS:
                op1_tipe, op2_tipe = item.op1_t, item.op2_t
                op1_const, op2_const = item.op1_const, item.op2_const
                code_gen.emit_binary_op(
                    op, tipe, op1_tipe, op2_tipe, op1_const, op2_const
                )
            elif op == TypedExpressionOp.UNARY_MINUS:
                code_gen.emit_unary_minus(tipe)


class Parser:
    def __init__(
        self,
        tokens: list[Token],
        code_gen: ByteCodeGen,
        symbol_table: SymbolTable,
    ):
        self.tokens = tokens
        self.current_token_index = 0
        self.code_gen = code_gen
        self.symbol_table = symbol_table

        # Parsing state
        self.parsing_params = False
        # self.exits_to_patch: list[list[ByteCode]] = []
        self.exits_to_patch: list[list[int]] = []  # Addresses of jumps to patch
        self.curr_routine_index = None

    def current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return None

    def next_token(self):
        if self.current_token_index + 1 < len(self.tokens):
            return self.tokens[self.current_token_index + 1]
        return None

    def advance(self) -> Token:
        token = self.current_token()
        self.current_token_index += 1
        return token

    def consume(self, token_type) -> Token:
        token = self.current_token()
        if token is None or token.tok_type != token_type:
            raise SyntaxError(f"Expected token {token_type}, got {token}")
        return self.advance()

    def parse_dev(self):
        self.parse_expression()

    # <program> ::= <program> MODULE <prog module> | {MODULE} <prog module>
    def parse_program(self):
        # TODO: Not sure the grammar is correct here, but it's from the manual
        try:
            while self.current_token() is not None:
                if self.current_token().tok_type == TokenType.MODULE:
                    self.advance()
                else:
                    break
            return self.parse_prog_module()
        except SyntaxError as e:
            self.error(e.msg)
        except Exception as e:
            self.error(str(e))

    # <prog module> ::= {<system decls>} <routine list>
    def parse_prog_module(self):
        self.parse_system_decls()
        self.parse_routine_list()

    # <system decls> ::= <DEFINE decl> | <TYPE decl> | <var decl>
    # (This grammar rule should probably be a recursive list of system decls, but the manual doesn't specify that)
    def parse_system_decls(self) -> bool:
        result = False
        while self.parse_system_decl():
            result = True
        return result

    def parse_system_decl(self) -> bool:
        if self.parse_define_decl():
            return True
        if self.parse_type_decl():
            return True
        if self.parse_var_decl():
            return True
        return False

    # <DEFINE decl> ::= <DEFINE> <def list>
    # TODO: Remove this when there's a preprocessing step to handle defines
    def parse_define_decl(self) -> bool:
        if self.current_token().tok_type != TokenType.DEFINE:
            return False
        self.advance()
        self.parse_def_list()
        return True

    # <def list> ::= <def list>,<def> | <def>
    # TODO: Remove this when there's a preprocessing step to handle defines
    def parse_def_list(self) -> bool:
        if not self.parse_def():
            return False
        while self.current_token().tok_type == TokenType.COMMA:
            self.advance()
            self.parse_def()
        return True

    # <def> ::= <identifier>=<str const>
    # TODO: Remove this when there's a preprocessing step to handle defines
    def parse_def(self) -> bool:
        raise NotImplementedError()
        # if self.current_token().tok_type != TokenType.IDENTIFIER:
        #     return False
        # if self.next_token().tok_type != TokenType.OP_EQ:
        #     return False
        # identifier = self.current_token().value
        # self.advance()
        # self.advance()
        # str_const = self.current_token().value
        # self.consume(TokenType.STRING_LITERAL)
        # self.directives.define(identifier, str_const)

    # <TYPE decl> ::= TYPE <rec ident list>
    def parse_type_decl(self) -> bool:
        if self.current_token().tok_type != TokenType.TYPE:
            return False
        self.advance()
        self.parse_rec_ident_list()
        return True

    # <rec ident list> ::= <rec ident list> <rec ident> | <rec ident>
    def parse_rec_ident_list(self) -> bool:
        if not self.parse_rec_ident():
            return False
        while self.parse_rec_ident():
            pass
        return True

    # <rec ident> ::= <rec name>=[<field init>]
    def parse_rec_ident(self) -> bool:
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        if self.next_token().tok_type != TokenType.OP_EQ:
            return False
        rec_name = self.current_token().value
        self.advance()
        self.advance()
        self.consume(TokenType.OP_LBRACK)
        self.parse_field_init()
        self.consume(TokenType.OP_RBRACK)

        return True

    # <field init> ::= <fund var decl>
    def parse_field_init(self) -> bool:
        return self.parse_fund_var_decl()

    # <var decl> ::= <var decl> <base var decl> | <base var decl>
    def parse_var_decl(self) -> bool:
        if not self.parse_base_var_decl():
            return False
        while self.parse_base_var_decl():
            pass
        return True

    # <base var decl> ::= <fund decl> | <POINTER decl> | <ARRAY decl> | <record decl>
    def parse_base_var_decl(self):
        if self.parse_fund_decl():
            return True
        if self.parse_pointer_decl():
            return True
        if self.parse_array_decl():
            return True
        if self.parse_record_decl():
            return True
        return False

    # Variable Declaration for Fundamental Data Types
    # -----------------------------------------------
    # <fund decl> ::= <fund decl> <base fund decl> | <base fund decl>
    def parse_fund_decl(self) -> bool:
        if not self.parse_base_fund_decl():
            return False
        while self.parse_base_fund_decl():
            pass
        return True

    # <base fund decl> ::= <fund type> <fund ident list>
    def parse_base_fund_decl(self) -> bool:
        fund_type = self.parse_fund_type()
        if fund_type is None:
            return False
        self.parse_fund_ident_list(fund_type)
        return True

    # <fund type> ::= CARD | CHAR | BYTE | INT
    def parse_fund_type(self) -> TokenType | None:
        if self.current_token().tok_type not in [
            TokenType.CARD,
            TokenType.CHAR,
            TokenType.BYTE,
            TokenType.INT,
        ]:
            return None
        fund_type = self.current_token().tok_type
        self.advance()
        return fund_type

    # <fund ident list> ::= <fund ident list>,<fund ident> | <fund ident>
    def parse_fund_ident_list(self, fund_type: TokenType) -> bool:
        if not self.parse_fund_ident(fund_type):
            return False
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            self.parse_fund_ident(fund_type)
        return True

    # <fund ident> ::= <identifier>{=<init opts>}
    def parse_fund_ident(self, fund_type: TokenType) -> bool:

        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        identifier = self.current_token().value
        self.advance()
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            self.parse_init_opts(fund_type, identifier)
        else:

            # TODO: To simplify this code, maybe use same Tipe enum for tokens and symbol table
            # Would be like a token with type TokenType.TYPE and value BYTE_TIPE
            tipe = None
            if fund_type == TokenType.BYTE:
                tipe = BYTE_TIPE
            elif fund_type == TokenType.CHAR:
                tipe = CHAR_TIPE
            elif fund_type == TokenType.INT:
                tipe = INT_TIPE
            elif fund_type == TokenType.CARD:
                tipe = CARD_TIPE
            # TODO: Deal with locals
            ident_index = self.symbol_table.declare_global(identifier, tipe)
        return True

    # <init opts> ::= <addr> | [<value>]
    # <addr> ::= <comp const>
    # <value> ::= <num const>
    # <num const> ::= <dec num> | <hex num> | <char>
    def parse_init_opts(self, fund_type: TokenType, identifier: str) -> bool:
        if self.current_token().tok_type == TokenType.OP_LBRACK:
            self.advance()
            value = self.current_token().int_value()
            self.advance()
            self.consume(TokenType.OP_RBRACK)
            # A little hacky - set the value of the last global
            self.symbol_table.globals[-1][2] = value
        else:
            raise NotImplementedError()
            # TODO: Special flag for global showing it's tied to an address.
            addr = self.parse_addr()
            self.code_gen.emit_define(identifier, addr)
        return True

    # # <value> ::= <num const>
    # def parse_value_const(self) -> int:
    #     return self.parse_num_const()

    # <num const> ::= <dec num> | <hex num> | <char>
    # def parse_num_const(self) -> int:
    #     if self.current_token().tok_type == TokenType.INT_LITERAL:
    #         return self.parse_dec_num()
    #     if self.current_token().tok_type == TokenType.HEX_LITERAL:
    #         return self.parse_hex_num()
    #     if self.current_token().tok_type == TokenType.CHAR_LITERAL:
    #         return self.parse_char()
    #     raise SyntaxError(f"Unexpected token: {self.current_token()}")

    # # <dec num> ::= <digit>{<digit>}
    # def parse_dec_num(self) -> int:
    #     return int(self.consume(TokenType.INT_LITERAL).value)

    # # <hex num> ::= $<hex digit>{<hex digit>}
    # def parse_hex_num(self) -> int:
    #     return int(self.consume(TokenType.HEX_LITERAL).value, 16)

    # # <char> ::= '<char const>'
    # def parse_char(self) -> str:
    #     return ord(self.consume(TokenType.CHAR_LITERAL).value)

    # <POINTER decl> ::= <ptr type> POINTER <ptr ident list>
    def parse_pointer_decl(self) -> bool:
        if not self.next_token():
            return False
        if self.next_token().tok_type != TokenType.POINTER:
            return False
        ptr_type = self.current_token().value
        self.advance()
        self.advance()
        self.parse_ptr_ident_list(ptr_type)

    # <ptr ident list> ::= <ptr ident list>,<ptr ident> | <ptr ident>
    def parse_ptr_ident_list(self, ptr_type: str) -> bool:
        if not self.parse_ptr_ident(ptr_type):
            return False
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            self.parse_ptr_ident(ptr_type)
        return True

    # <ptr ident> ::= <identifier>{=<value>}
    def parse_ptr_ident(self, ptr_type) -> bool:
        identifier = self.current_token().value
        self.consume(TokenType.IDENTIFIER)
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            value = self.parse_value_const()
            self.code_gen.emit_ptr_ident_value(ptr_type, identifier, value)
        else:
            self.code_gen.emit_ptr_ident(ptr_type, identifier)
        return True

    # Variable Declaration for Arrays
    # -------------------------------
    # <ARRAY decl> ::= <fund type> ARRAY <arr ident list>
    # <arr ident list> ::= <arr ident list>,<arr ident> |
    # <arr ident>
    # <arr ident> ::= <identifier>{(<dim>)}{=<arr init opts>}
    # <dim> ::= <num conat>
    # <arr init opts> ::= <addr> | [<value>] | <str const>
    # <addr> ::= <comp const>
    # <value list> ::= <value list><value> | <value>
    # <value> ::= <comp const>
    def parse_array_decl(self) -> bool:
        # TODO
        # raise NotImplementedError()
        return False

    # Variable Declaration for Records
    # --------------------------------
    # <record decl> ::= <identifier> <rec ident list>
    # <address> ::= <comp const>
    # TODO: Probably need to refer to a symbol/type table to look up the record type to
    # distinguish between record and array or other declarations
    def parse_record_decl(self) -> bool:
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        # Make sure it's a record.
        record_type_index = self.symbol_table.tipes_lookup.get(
            self.current_token().value
        )
        if record_type_index is None:
            return False
        rec_type = self.current_token().value
        self.advance()
        return self.parse_rec_ident_list(rec_type)

    # <rec ident list> ::= <rec ident list>,<rec ident> | <rec ident>
    def parse_rec_ident_list(self, rec_type: str) -> bool:
        if not self.parse_rec_ident(rec_type):
            return False
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            self.parse_rec_ident(rec_type)

    # <rec ident> ::= <identifier>{=<address>}
    def parse_rec_ident(self, rec_type: str) -> bool:
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        identifier = self.current_token().value
        self.advance()
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            addr = self.parse_addr()
            self.code_gen.emit_rec_ident_value(rec_type, identifier, addr)
        else:
            self.code_gen.emit_rec_ident(rec_type, identifier)
        return True

    # <routine list> ::= <routine list> <routine> | <routine>
    def parse_routine_list(self):
        while self.parse_routine():
            pass

    # <routine> ::= <proc routine> | <func routine>
    def parse_routine(self) -> bool:
        if self.parse_proc_routine():
            return True
        if self.parse_func_routine():
            return True
        return False

    # <proc routine> ::= <PROC decl> {<system decls>} {<stmt list>}{RETURN}
    # <proc decl> ::= PROC <identifier>{=<addr>}({<param decl>})
    # The RETURN token is optional because it's desirable to be able to fall through
    # to the next routine on a 6502.
    def parse_proc_routine(self) -> bool:
        if self.current_token().tok_type != TokenType.PROC:
            return False
        self.advance()
        identifier = self.consume(TokenType.IDENTIFIER).value
        if self.current_token().tok_type == TokenType.OP_EQ:
            # TODO: Implement routine address
            # Note: There seem to be limitations in the original implementation in testing
            # i.e. ("BYTE x PROC xFunc = x + 1") should compile by the spec, but it doesn't
            raise NotImplementedError("PROC with routine address")
            self.advance()
            addr = self.parse_addr()
        self.consume(TokenType.OP_LPAREN)

        # TODO: Implement parameters. Current parsing code ends up declaring globals,
        # so that needs to be avoided
        # self.parse_param_decl()
        self.consume(TokenType.OP_RPAREN)
        bytecode_addr = self.code_gen.get_next_addr()
        routine = Routine(identifier, bytecode_addr, [], None)
        try:
            self.curr_routine_index = self.symbol_table.declare_routine(routine)
            self.parse_system_decls()
            self.parse_stmt_list()
        finally:
            self.curr_routine_index = None
        # RETURN is optional, and handled by the stmt list
        # if self.current_token().tok_type == TokenType.RETURN:
        #     self.code_gen.emit_return()
        #     self.advance()

        return True

    # def parse_proc_decl(self) -> bool:
    #     if self.current_token().tok_type != TokenType.PROC:
    #         return False
    #     self.advance()
    #     identifier = self.consume(TokenType.IDENTIFIER).value
    #     if self.current_token().tok_type == TokenType.OP_EQ:
    #         self.advance()
    #         addr = self.parse_addr()
    #     self.consume(TokenType.LPAREN)
    #     self.parse_param_decl()
    #     self.consume(TokenType.RPAREN)
    #     return True

    # <addr> ::= <comp const>
    def parse_addr(self):
        return self.parse_comp_const()

    # <func routine> ::= <FUNC decl> {<system decls>} {<stmt list>}{RETURN (<arith exp>)}
    def parse_func_routine(self) -> bool:
        if not self.parse_func_decl():
            return False
        self.parse_system_decls()
        self.parse_stmt_list()
        # RETURN is optional
        # if self.current_token().tok_type == TokenType.RETURN:
        #     self.advance()
        #     self.consume(TokenType.OP_LPAREN)
        #     self.parse_arith_exp()
        #     self.consume(TokenType.OP_RPAREN)
        return True

        # self.consume(TokenType.FUNC)
        # self.parse_func_decl()
        # self.parse_system_decls()
        # self.parse_stmt_list()
        # if self.current_token().type == TokenType.RETURN:
        #     self.advance()
        #     self.consume(TokenType.LPAREN)
        #     self.parse_arith_exp()
        #     self.consume(TokenType.RPAREN)

    # <FUNC decl> ::= <fund type> FUNC <identifier>{.<addr>} ({<param decl>})
    def parse_func_decl(self) -> bool:
        fund_type = self.parse_fund_type()
        if fund_type is None:
            return False
        self.consume(TokenType.FUNC)
        identifier = self.consume(TokenType.IDENTIFIER).value
        if self.current_token().tok_type == TokenType.OP_DOT:
            self.advance()
            addr = self.parse_addr()
        self.consume(TokenType.OP_LPAREN)
        self.parse_param_decl()
        self.consume(TokenType.OP_RPAREN)
        return True

    # <param decl> ::= <var decl>
    # TODO: Implement limit of 8 parameters
    # NOTE: max. of 8 parameters allowed
    def parse_param_decl(self) -> bool:
        return self.parse_var_decl()

    # A.7 Statements
    # ---------------
    # <stmt list> ::= <stmt list> <stmt> | <stmt>
    def parse_stmt_list(self) -> bool:
        while True:
            if not self.parse_stmt():
                break

    # <stmt> ::= <simp stmt> | <struc stmt> | <code block>
    def parse_stmt(self) -> bool:
        # If in a routine and we see a PROC or FUNC decl, it's not a statement
        # TODO: Also make sure it's a top-level statement? (e.g. not in an IF block)
        if self.curr_routine_index is not None and (
            self.current_token().tok_type == TokenType.PROC
            or (
                self.current_token().is_primitive_type()
                and self.next_token().tok_type == TokenType.FUNC
            )
        ):
            return False

        if self.parse_simp_stmt():
            return True
        if self.parse_struc_stmt():
            return True
        if self.parse_code_block():
            return True
        return False

    # <simp stmt> ::= <assign stmt> | <EXIT stmt> | <routine call>
    def parse_simp_stmt(self) -> bool:
        if self.parse_devprint_stmt():
            return True
        if self.parse_assign_stmt():
            return True
        if self.parse_exit_stmt():
            return True
        if self.parse_routine_call():
            return True
        if self.parse_return_stmt():
            return True
        return False

    def parse_devprint_stmt(self) -> bool:
        if self.current_token().tok_type != TokenType.DEVPRINT:
            return False
        self.advance()
        self.consume(TokenType.OP_LPAREN)
        self.parse_arith_exp()
        self.consume(TokenType.OP_RPAREN)
        self.code_gen.emit_devprint()
        return True

    # <assign stmt> ::= <mem contents>=<arith exp>
    # <mem contents> ::= <fund ref> | <arr ref> | <ptr ref> | <rec ref>
    # <fund ref> ::= <identifier>
    # <arr ref> ::= <identifier>(<arith exp>)
    # <ptr ref> ::= <identifier>^
    # <rec ref> ::= <identifier>.<identifier>
    def parse_assign_stmt(self) -> bool:
        # TODO: Only deals with simple variables. Need to handle arrays, pointers, and records.
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        if self.next_token().tok_type != TokenType.OP_EQ:
            return False
        identifier = self.current_token().value
        self.advance()
        self.advance()
        self.parse_arith_exp()
        # TODO: Handle arrays, pointers, and records
        # For now, just emit for simple global identifier
        global_index = self.symbol_table.globals_lookup.get(identifier)
        if global_index is None:
            raise SyntaxError(f"Undefined variable: {identifier}")
        self.code_gen.emit_set_global(global_index)
        return True

    # <EXIT stmt> ::= EXIT
    def parse_exit_stmt(self) -> bool:
        if self.current_token().tok_type != TokenType.EXIT:
            return False
        self.advance()
        if len(self.exits_to_patch) == 0:
            raise SyntaxError("EXIT statement outside of loop")
        # This gets patched at the end of the loop with the address following the loop
        jump_exit = self.code_gen.emit_jump()
        self.exits_to_patch[-1].append(jump_exit)
        return True

    # <RETURN stmt> ::= RETURN | RETURN (<arith exp>) - depending on PROC or FUNC
    def parse_return_stmt(self) -> bool:
        if self.current_token().tok_type != TokenType.RETURN:
            return False
        self.advance()
        if self.symbol_table.routines[self.curr_routine_index].return_tipe is not None:
            self.consume(TokenType.OP_LPAREN)
            self.advance()
            self.parse_arith_exp()
            self.consume(TokenType.OP_RPAREN)
        self.code_gen.emit_return()

        return True

    # <routine call> ::= <FUNC call> | <PROC call>
    # <FUNC call> ::= <identifier>({<params>})
    # <PROC call> ::= <identifier>({<params>})
    # "Function calls can be used in any arithmetic expression, with one exception:
    # Functions calls may NOT be used in an
    # arithmetic expression when that expression is used
    # as a parameter in a routine call or declaration."
    def parse_routine_call(self) -> bool:
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        if self.next_token().tok_type != TokenType.OP_LPAREN:
            return False
        identifier = self.current_token().value
        routine_index = self.symbol_table.routines_lookup.get(identifier)
        # Might be an array reference if it's not a routine
        if routine_index is None:
            return False
        if self.parsing_params:
            raise SyntaxError(
                "A function call may not be used as a parameter in a routine call or declaration"
            )
        self.advance()  # routine name
        self.advance()  # (
        self.parse_params(routine_index)
        self.consume(TokenType.OP_RPAREN)
        self.code_gen.emit_routine_call(routine_index)
        return True

    # <params> ::= <params>,<arith exp> | <arith exp>
    def parse_params(self, routine_index: int):
        routine = self.symbol_table.routines[routine_index]
        param_tipes = routine.param_tipes
        expected_param_count = len(param_tipes)
        param_count = 0
        try:
            self.parsing_params = True
            for _ in range(expected_param_count):
                self.parse_arith_exp()
                param_count += 1
                self.code_gen.emit_push_param()
                if param_count < expected_param_count:
                    self.consume(TokenType.OP_COMMA)
            if param_count > 8:
                raise SyntaxError("Too many parameters (max 8)")
            if param_count < expected_param_count:
                self.warn(
                    f"Too few parameters, expected {expected_param_count}, got {param_count} at {self.current_token().source_location()}"
                )
            # Fill in any missing parameters with zeros
            while param_count < expected_param_count:
                self.code_gen.emit_zero()
                self.code_gen.emit_push_param()
                param_count += 1

        finally:
            self.parsing_params = False

    # <cond exp> ::= <complex rel>
    # Note: This was not in the manual but it seems like they are synonymous
    #
    # Also worth noting, the grammar rules in the manual show that an expression like
    # "1" is not a valid conditional expression. But in practice, the Action
    # compiler cartridge allows it, e.g. "IF 1 THEN do_something() FI" compiles and
    # runs as expected, treating nonzero values as true and zero as false
    def parse_cond_exp(self) -> bool:
        return self.parse_expression()

    def parse_arith_exp(self) -> bool:
        return self.parse_expression()

    # <struc stmt> ::= <IF stmt> | <DO loop> | <WHILE loop> | <FOR loop>
    def parse_struc_stmt(self) -> bool:
        if self.parse_if_stmt():
            return True
        if self.parse_do_loop():
            return True
        if self.parse_while_loop():
            return True
        if self.parse_for_loop():
            return True
        return False

    # <IF stmt> ::= IF <cond exp> THEN {stmt list} {|:ELSEIF exten:|}{ELSE exten} FI
    def parse_if_stmt(self) -> bool:
        if self.current_token().tok_type != TokenType.IF:
            return False
        jump_ends: list[ByteCode] = []

        # If
        self.advance()
        self.parse_cond_exp()
        self.consume(TokenType.THEN)
        jump_over = self.code_gen.emit_jump_if_false()
        self.parse_stmt_list()
        jump_ends.append(self.code_gen.emit_jump())
        jump_over.value = self.code_gen.get_next_addr()

        # Elseif
        while self.current_token().tok_type == TokenType.ELSEIF:
            self.advance()
            self.parse_cond_exp()
            self.consume(TokenType.THEN)
            jump_over = self.code_gen.emit_jump_if_false()
            self.parse_stmt_list()
            jump_ends.append(self.code_gen.emit_jump())
            jump_over.value = self.code_gen.get_next_addr()

        # Else
        if self.current_token().tok_type == TokenType.ELSE:
            self.advance()
            self.parse_stmt_list()

        # Fi
        self.consume(TokenType.FI)
        end_addr = self.code_gen.get_next_addr()
        for jump_end in jump_ends:
            jump_end.value = end_addr

        return True

    # Helper function to set up exit patching
    def prepare_exits(self):
        self.exits_to_patch.append([])

    # Helper function for patching exits at the end of loops
    def patch_exits(self):
        exits_to_patch = self.exits_to_patch.pop()
        if exits_to_patch:
            next_addr = self.code_gen.get_next_addr()
            for jump_exit in exits_to_patch:
                jump_exit.value = next_addr

    # <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
    # <UNTIL stmt> ::= UNTIL <cond exp>
    def parse_do_loop(self) -> bool:
        if self.current_token().tok_type != TokenType.DO:
            return False
        self.advance()
        self.prepare_exits()
        jump_start = self.code_gen.get_next_addr()
        self.parse_stmt_list()
        if self.current_token().tok_type == TokenType.UNTIL:
            self.advance()
            self.parse_cond_exp()
            self.code_gen.emit_jump_if_false(jump_start)
            self.consume(TokenType.OD)
        else:
            self.consume(TokenType.OD)
            self.code_gen.emit_jump(jump_start)
        self.patch_exits()
        return True

    # <WHILE loop> ::= WHILE <cond exp> <DO loop>
    # <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
    # <UNTIL stmt> ::= UNTIL <cond exp>
    # Note: Yes,  WHILE loop can also have an UNTIL statement
    def parse_while_loop(self) -> bool:
        if self.current_token().tok_type != TokenType.WHILE:
            return False
        self.advance()
        self.prepare_exits()
        jump_start = self.code_gen.get_next_addr()
        self.parse_cond_exp()
        jump_end = self.code_gen.emit_jump_if_false()
        self.consume(TokenType.DO)
        self.parse_stmt_list()
        if self.current_token().tok_type == TokenType.UNTIL:
            self.advance()
            self.parse_cond_exp()
            self.code_gen.emit_jump_if_false(jump_start)
        else:
            self.code_gen.emit_jump(jump_start)
        self.consume(TokenType.OD)
        jump_end.value = self.code_gen.get_next_addr()
        self.patch_exits()

        return True

    # <FOR loop> ::= FOR <identifier>=<start> TO <finish> {STEP <inc>}<DO loop>
    # <start> ::= <arith exp>
    # <finish> ::= <arith exp>
    # <inc> ::= <arith exp>
    def parse_for_loop(self) -> bool:
        if self.current_token().tok_type != TokenType.FOR:
            return False
        raise NotImplementedError()
        self.advance()
        self.prepare_exits()
        identifier = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.EQUAL)
        self.parse_arith_exp()
        self.consume(TokenType.TO)
        self.parse_arith_exp()
        if self.current_token().tok_type == TokenType.STEP:
            self.advance()
            self.parse_arith_exp()
        self.parse_do_loop()
        self.patch_exits()
        return True

    # <code block> ::= [<comp const list>]
    def parse_code_block(self) -> bool:
        if self.current_token().tok_type != TokenType.OP_LBRACK:
            return False
        self.advance()
        self.parse_comp_const_list()
        self.consume(TokenType.OP_RBRACK)
        return True

    # <comp const list> ::= <comp const list> <comp const> | <comp const>
    def parse_comp_const_list(self) -> bool:
        while True:
            comp_const = self.parse_comp_const()
            if not comp_const:
                break
            self.code_gen.emit_comp_const(comp_const)
        return True

    # We implement the precedence climbing algorithm to parse expressions
    def parse_expression(self):
        # Start at lowest precedence
        self.parse_expr_precedence(ExprPrecedence.XOR)

    def parse_expr_precedence(self, precedence: ExprPrecedence):
        if self.current_token().tok_type not in EXPRESSION_RULES:
            return
        prefix = EXPRESSION_RULES[self.current_token().tok_type].prefix
        if prefix == ExprAction.NONE:
            raise SyntaxError(f"Expected prefix expression: {self.current_token()}")
        self.parse_expr_action(prefix)

        if self.current_token().tok_type not in EXPRESSION_RULES:
            return
        while (
            precedence.value
            <= EXPRESSION_RULES[self.current_token().tok_type].precedence.value
        ):
            self.parse_expr_action(
                EXPRESSION_RULES[self.current_token().tok_type].infix
            )
            if self.current_token().tok_type not in EXPRESSION_RULES:
                return

    def parse_expr_action(self, action: ExprAction):
        if action == ExprAction.NUMBER:
            self.parse_number()
        elif action == ExprAction.GROUPING:
            self.parse_grouping()
        elif action == ExprAction.UNARY:
            self.parse_unary()
        elif action == ExprAction.BINARY:
            self.parse_binary()
        elif action == ExprAction.AND:
            self.parse_and()
        elif action == ExprAction.OR:
            self.parse_or()
        elif action == ExprAction.IDENTIFIER:
            self.parse_identifier_expr()

    def parse_number(self):
        value = None
        if self.current_token().tok_type == TokenType.INT_LITERAL:
            value = int(self.current_token().value)
        elif self.current_token().tok_type == TokenType.HEX_LITERAL:
            value = int(self.current_token().value, 16)
        else:
            raise SyntaxError(
                f"Unexpected token in parse_number: {self.current_token()}"
            )
        if value < -65535 or value > 65535:
            raise SyntaxError(f"Numeric literal {value} out of range [-65535, 65535]")
        self.advance()
        const_index = self.symbol_table.declare_constant(value)
        self.code_gen.emit_numerical_constant(const_index)

    def parse_grouping(self):
        self.advance()
        self.parse_expression()
        self.consume(TokenType.OP_RPAREN)

    def parse_unary(self):
        operator_type = self.current_token().tok_type
        self.parse_expr_precedence(ExprPrecedence.UNARY)
        if operator_type == TokenType.OP_MINUS:
            self.code_gen.emit_unary_minus()
        self.advance()

    def parse_binary(self):
        operator_type = self.current_token().tok_type
        self.advance()
        rule = EXPRESSION_RULES[operator_type]
        self.parse_expr_precedence(ExprPrecedence(rule.precedence.value + 1))

        if operator_type == TokenType.OP_PLUS:
            self.code_gen.emit_add()
        elif operator_type == TokenType.OP_MINUS:
            self.code_gen.emit_subtract()
        elif operator_type == TokenType.OP_TIMES:
            self.code_gen.emit_multiply()
        elif operator_type == TokenType.OP_DIVIDE:
            self.code_gen.emit_divide()
        elif operator_type == TokenType.MOD:
            self.code_gen.emit_mod()
        elif operator_type == TokenType.LSH:
            self.code_gen.emit_lsh()
        elif operator_type == TokenType.RSH:
            self.code_gen.emit_rsh()
        elif operator_type == TokenType.OP_EQ:
            self.code_gen.emit_eq()
        elif operator_type == TokenType.OP_NE:
            self.code_gen.emit_ne()
        elif operator_type == TokenType.OP_GT:
            self.code_gen.emit_gt()
        elif operator_type == TokenType.OP_GE:
            self.code_gen.emit_ge()
        elif operator_type == TokenType.OP_LT:
            self.code_gen.emit_lt()
        elif operator_type == TokenType.OP_LE:
            self.code_gen.emit_le()
        elif operator_type == TokenType.XOR:
            self.code_gen.emit_xor()
        elif operator_type == TokenType.OP_BIT_AND:
            self.code_gen.emit_bit_and()
        elif operator_type == TokenType.OP_BIT_OR:
            self.code_gen.emit_bit_or()
        elif operator_type == TokenType.OP_BIT_XOR:
            self.code_gen.emit_bit_xor()

    def parse_and(self):
        # AND is a short-circuiting operator
        jump_end = self.code_gen.emit_jump_if_false()
        self.code_gen.emit_pop()
        self.advance()
        self.parse_expr_precedence(ExprPrecedence.AND)
        jump_end.value = self.code_gen.get_next_addr()

    def parse_or(self):
        # OR is a short-circuiting operator
        jump_else = self.code_gen.emit_jump_if_false()
        jump_end = self.code_gen.emit_jump()
        jump_else.value = self.code_gen.get_next_addr()
        self.code_gen.emit_pop()
        self.advance()
        self.parse_expr_precedence(ExprPrecedence.OR)
        jump_end.value = self.code_gen.get_next_addr()

    def parse_identifier_expr(self):
        # An identifier in an expression might be a variable of some sort
        # or a function call
        if self.current_token().tok_type == TokenType.OP_AT:
            raise NotImplementedError()
        # TODO: Arrays, pointers, and records
        # TODO: Locals
        identifier = self.current_token().value
        if self.symbol_table.globals_lookup.get(identifier) is not None:
            # TODO: Should call parse_mem_reference to deal with arrays.
            self.code_gen.emit_get_global(self.symbol_table.globals_lookup[identifier])
            self.advance()
        else:
            raise NotImplemented("Function calls in expressions not yet implemented")

    # Memory References
    # -----------------
    # <mem reference> ::= <mem contents> | @<identifier>
    # <mem contents> ::= <fund ref> | <arr ref> | <ptr ref> | <rec ref>
    # <fund ref> ::= <identifier>
    # <arr ref> ::= <identifier>(<arith exp>)
    # <ptr ref> ::= <identifier>^
    # <rec ref> ::= <identifier>.<identifier>
    def parse_mem_reference(self):
        if (
            self.current_token().tok_type == TokenType.AT
            and self.next_token().tok_type == TokenType.IDENTIFIER
            and self.next_token().value in self.symbol_table.globals_lookup
        ):
            self.advance()
            identifier = self.consume(TokenType.IDENTIFIER).value
            global_index = self.symbol_table.globals_lookup.get(identifier)
            if global_index is None:
                raise SyntaxError(f"Undefined variable: {identifier}")
            self.code_gen.emit_get_addr_global(global_index)
        elif (
            self.current_token().tok_type == TokenType.IDENTIFIER
            and self.current_token().value in self.symbol_table.globals_lookup
        ):
            if self.next_token().tok_type == TokenType.LPAREN:
                # Handle array reference
                raise NotImplementedError()
            elif self.next_token().tok_type == TokenType.PERIOD:
                # Handle record reference
                raise NotImplementedError()
            elif self.next_token().tok_type == TokenType.CARET:
                # Handle pointer reference
                identifier = self.consume(TokenType.IDENTIFIER).value
                # TODO: Deal with locals and parameters
                global_index = self.symbol_table.globals_lookup.get(identifier)
                if global_index is None:
                    raise SyntaxError(f"Undefined variable: {identifier}")
                global_val = self.symbol_table.globals[global_index]
                if not global_val.var_type.is_pointer():
                    raise SyntaxError(f"Variable {identifier} is not a pointer")
                self.code_gen.emit_get_ptr_global(global_index)
                self.advance()
            else:
                # TODO: Deal with locals. Just do globals for now
                identifier = self.consume(TokenType.IDENTIFIER).value
                global_index = self.symbol_table.globals_lookup.get(identifier)
                if global_index is None:
                    raise SyntaxError(f"Undefined variable: {identifier}")
                self.code_gen.emit_get_global(global_index)

    def warn(self, message: str):
        print(
            f"Warning: {message} at {self.current_token().source_location()}",
            file=sys.stderr,
        )

    def error(self, message: str):
        print(
            f"Error: {message} at {self.current_token().source_location()}",
            file=sys.stderr,
        )
