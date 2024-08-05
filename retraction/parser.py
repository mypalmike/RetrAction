from enum import Enum, auto

from retraction.tokens import Token, TokenType
from retraction.codegen import ByteCodeGen
from retraction.bytecode import ByteCode
from retraction.symtab import SymbolTable
from retraction.tipes import BYTE_TIPE, CARD_TIPE, CHAR_TIPE, INT_TIPE, BaseTipe, Tipe

# from retraction.expression import ExpressionNode, StubExpressionNode


class SyntaxError(Exception):
    pass


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
    # PARENTHESIS = 8
    # HIGHEST = 9


class ExprAction(Enum):
    NONE = auto()
    NUMBER = auto()
    GROUPING = auto()
    UNARY = auto()
    BINARY = auto()
    AND = auto()
    OR = auto()


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
    TokenType.EOF: ExprRule(ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE),
}


class Parser:
    def __init__(
        self,
        tokens: list[Token],
        directives,
        code_gen: ByteCodeGen,
        symbol_table: SymbolTable,
    ):
        self.tokens = tokens
        self.current_token_index = 0
        self.directives = directives
        self.code_gen = code_gen
        self.symbol_table = symbol_table

        # Parser state variables
        self.parsing_params = False

    def current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return None

    def next_token(self):
        if self.current_token_index + 1 < len(self.tokens):
            return self.tokens[self.current_token_index + 1]
        return None

    def prev_token(self):
        if self.current_token_index > 0:
            return self.tokens[self.current_token_index - 1]
        return None

    def advance(self):
        self.current_token_index += 1

    def consume(self, token_type) -> Token:
        token = self.current_token()
        if token is None or token.tok_type != token_type:
            raise SyntaxError(f"Expected token {token_type}, got {token}")
        self.advance()
        return token

        # if self.current_token() is None or self.current_token().type != token_type:
        #     raise SyntaxError(
        #         f"Expected token {token_type}, got {self.current_token()}"
        #     )
        # self.advance()

    def parse_dev(self):
        self.parse_expression()

    # <program> ::= <program> MODULE <prog module> | {MODULE} <prog module>
    def parse_program(self):
        # TODO: Not sure the grammar is correct here, but it's from the manual
        while self.current_token() is not None:
            if self.current_token().tok_type == TokenType.MODULE:
                self.advance()
            else:
                break
        return self.parse_prog_module()

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
        elif self.parse_type_decl():
            return True
        elif self.parse_var_decl():
            return True
        return False

    # <DEFINE decl> ::= <DEFINE> <def list>
    def parse_define_decl(self) -> bool:
        if self.current_token().tok_type == TokenType.DEFINE:
            self.advance()
            self.parse_def_list()
            return True
        return False

    # <def list> ::= <def list>,<def> | <def>
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
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        if self.next_token().tok_type != TokenType.OP_EQ:
            return False
        identifier = self.current_token().value
        self.advance()
        self.advance()
        str_const = self.current_token().value
        self.consume(TokenType.STRING_LITERAL)
        self.directives.define(identifier, str_const)

    # <TYPE decl> ::= TYPE <rec ident list>
    def parse_type_decl(self) -> bool:
        if self.current_token().tok_type == TokenType.TYPE:
            self.advance()
            self.parse_rec_ident_list()
            return True
        return False

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
        print(f"current_token: {self.current_token()}")
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
        print(f"parse_fund_ident... fund_type: {fund_type}")
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        identifier = self.current_token().value
        self.advance()
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            self.parse_init_opts(fund_type, identifier)
        else:
            print(f"fund_type: {fund_type}, identifier: {identifier}")
            print(f"current_token: {self.current_token()}")
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

        # identifier = self.current_token().value
        # self.expect(TokenType.IDENTIFIER)
        # if self.current_token().type == TokenType.EQUAL:
        #     self.advance()
        #     self.parse_init_opts(fund_type, identifier)
        # else:
        #     self.code_gen.emit_fund_ident(fund_type, identifier)

    # <init opts> ::= <addr> | [<value>]
    def parse_init_opts(self, fund_type: TokenType, identifier: str) -> bool:
        if self.current_token().tok_type == TokenType.OP_LBRACK:
            self.advance()
            value = self.parse_value_const()
            self.consume(TokenType.OP_RBRACK)
            self.code_gen.emit_define_value(identifier, value)
        else:
            addr = self.parse_addr()
            self.code_gen.emit_define(identifier, addr)
        return True

    # <value> ::= <num const>
    def parse_value_const(self) -> int:
        return self.parse_num_const()

    # <num const> ::= <dec num> | <hex num> | <char>
    def parse_num_const(self) -> int:
        if self.current_token().tok_type == TokenType.INT_LITERAL:
            return self.parse_dec_num()
        if self.current_token().tok_type == TokenType.HEX_LITERAL:
            return self.parse_hex_num()
        if self.current_token().tok_type == TokenType.CHAR_LITERAL:
            return self.parse_char()
        raise SyntaxError(f"Unexpected token: {self.current_token()}")

    # <dec num> ::= <digit>{<digit>}
    def parse_dec_num(self) -> int:
        return int(self.consume(TokenType.INT_LITERAL).value)

    # <hex num> ::= $<hex digit>{<hex digit>}
    def parse_hex_num(self) -> int:
        return int(self.consume(TokenType.HEX_LITERAL).value, 16)

    # <char> ::= '<char const>'
    def parse_char(self) -> str:
        return ord(self.consume(TokenType.CHAR_LITERAL).value)

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

    # Memory References
    # TODO: All of these need to be reworked using the table parser
    # without ExpreressionNodes
    # -----------------
    # <mem reference> ::= <mem contents> | @<identifier>
    # def parse_mem_reference(self) -> ExpressionNode | None:
    #     mem_contents = self.parse_mem_contents()
    #     if mem_contents:
    #         return mem_contents
    #     if self.current_token().type == TokenType.AT:
    #         self.advance()
    #         identifier = self.current_token().value
    #         self.consume(TokenType.IDENTIFIER)
    #         return StubExpressionNode(f"mem_ref(@{identifier})")
    #     return None

    # # <mem contents> ::= <fund ref> | <arr ref> | <ptr ref> | <rec ref>
    # def parse_mem_contents(self) -> ExpressionNode | None:
    #     arr_ref = self.parse_arr_ref()
    #     if arr_ref:
    #         return arr_ref
    #     ptr_ref = self.parse_ptr_ref()
    #     if ptr_ref:
    #         return ptr_ref
    #     rec_ref = self.parse_rec_ref()
    #     if rec_ref:
    #         return rec_ref
    #     # Note: This has to be last because it will match any identifier, whereas the others
    #     # match an identifier followed by specific "next" tokens that they look for (e.g. LPAREN, CARET, PERIOD)
    #     fund_ref = self.parse_fund_ref()
    #     if fund_ref:
    #         return fund_ref
    #     return None

    # <arr ref> ::= <identifier>(<arith exp>)
    # def parse_arr_ref(self) -> ExpressionNode | None:
    #     if self.current_token().type != TokenType.IDENTIFIER:
    #         return None
    #     identifier = self.current_token().value
    #     self.advance()
    #     if self.current_token().type != TokenType.LPAREN:
    #         return None
    #     self.advance()
    #     arith_exp = self.parse_arith_exp()
    #     if self.current_token().type != TokenType.RPAREN:
    #         return None
    #     self.advance()
    #     # TODO: Make this return a subclass of Expression
    #     return StubExpressionNode(f"arr_ref({identifier}, {arith_exp})")

    # # <ptr ref> ::= <identifier>^
    # def parse_ptr_ref(self) -> ExpressionNode | None:
    #     if self.current_token().type != TokenType.IDENTIFIER:
    #         return None
    #     identifier = self.current_token().value
    #     self.advance()
    #     if self.current_token().type != TokenType.CARET:
    #         return None
    #     self.advance()
    #     return StubExpressionNode(f"ptr_ref({identifier})")

    # # <rec ref> ::= <identifier>.<identifier>
    # def parse_rec_ref(self) -> ExpressionNode | None:
    #     if self.current_token().type != TokenType.IDENTIFIER:
    #         return None
    #     identifier = self.current_token().value
    #     self.advance()
    #     if self.current_token().type != TokenType.PERIOD:
    #         return None
    #     self.advance()
    #     field = self.current_token().value
    #     self.advance()
    #     return StubExpressionNode(f"rec_ref({identifier}, {field})")

    # # # <fund ref> ::= <identifier>
    # def parse_fund_ref(self) -> ExpressionNode | None:
    #     if self.current_token().type != TokenType.IDENTIFIER:
    #         return None
    #     identifier = self.current_token().value
    #     self.advance()
    #     return StubExpressionNode(f"fund_ref({identifier})")

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
    # The RETURN token is apparently optional because it's not uncommon to fall through to the next routine
    def parse_proc_routine(self) -> bool:
        if not self.parse_proc_decl():
            return False
        self.parse_system_decls()
        self.parse_stmt_list()
        if self.current_token().tok_type == TokenType.RETURN:
            self.code_gen.emit_return()
            self.advance()
        return True

    # <proc decl> ::= PROC <identifier>{=<addr>}({<param decl>})
    def parse_proc_decl(self) -> bool:
        if self.current_token().tok_type != TokenType.PROC:
            return False
        self.advance()
        identifier = self.consume(TokenType.IDENTIFIER).value
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            addr = self.parse_addr()
        self.consume(TokenType.LPAREN)
        self.parse_param_decl()
        self.consume(TokenType.RPAREN)
        return True

    # <addr> ::= <comp const>
    def parse_addr(self):
        return self.parse_comp_const()

    # <func routine> ::= <FUNC decl> {<system decls>} {<stmt list>}{RETURN (<arith exp>)}
    def parse_func_routine(self) -> bool:
        if not self.parse_func_decl():
            return False
        self.parse_system_decls()
        self.parse_stmt_list()
        if self.current_token().tok_type == TokenType.RETURN:
            self.advance()
            self.consume(TokenType.OP_LPAREN)
            self.parse_arith_exp()
            self.consume(TokenType.OP_RPAREN)
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
        return False

    def parse_devprint_stmt(self) -> bool:
        if self.current_token().tok_type == TokenType.DEVPRINT:
            self.advance()
            self.consume(TokenType.OP_LPAREN)
            self.parse_arith_exp()
            self.consume(TokenType.OP_RPAREN)
            self.code_gen.emit_devprint()
            return True
        return False

    # <assign stmt> ::= <mem contents>=<arith exp>
    def parse_assign_stmt(self) -> bool:
        if self.next_token().tok_type == TokenType.OP_EQ:
            mem_contents = self.parse_mem_contents()
            self.consume(TokenType.OP_EQ)
            self.parse_arith_exp()
            self.code_gen.emit_assign_stmt(mem_contents)
            return True
        return False

    # <EXIT stmt> ::= EXIT
    def parse_exit_stmt(self) -> bool:
        if self.current_token().tok_type == TokenType.EXIT:
            self.advance()
            self.code_gen.emit_exit()
            return True
        return False

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
        routine_name = self.current_token().value
        if self.symbol_table.routines_lookup[routine_name] is None:
            return False
        # TODO: Finish the implementation
        return False
        if self.parsing_params:
            raise SyntaxError(
                "A function call may not be used as a parameter in a routine call or declaration"
            )
        identifier = self.current_token().value
        self.consume(TokenType.IDENTIFIER)
        self.consume(TokenType.OP_LPAREN)
        if self.current_token().tok_type != TokenType.OP_RPAREN:
            self.parse_params()
        self.consume(TokenType.OP_RPAREN)
        # TODO: Implement this
        # self.code_gen.emit_routine_call(identifier)

    # <params> ::= <params>,<arith exp> | <arith exp>
    def parse_params(self):
        try:
            self.parsing_params = True
            self.parse_arith_exp()
            param_count = 1
            while self.current_token().tok_type == TokenType.OP_COMMA:
                self.advance()
                self.parse_arith_exp(False)
                param_count += 1
                if param_count > 8:
                    raise SyntaxError("Too many parameters (max 8)")
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

    # <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
    # <UNTIL stmt> ::= UNTIL <cond exp>
    def parse_do_loop(self) -> bool:
        if self.current_token().tok_type != TokenType.DO:
            return False
        self.advance()
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
        return True

    # <WHILE loop> ::= WHILE <cond exp> <DO loop>
    # <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
    # <UNTIL stmt> ::= UNTIL <cond exp>
    # Note: Yes,  WHILE loop can also have an UNTIL statement
    def parse_while_loop(self) -> bool:
        if self.current_token().tok_type != TokenType.WHILE:
            return False
        self.advance()
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
        jump_end.value = self.code_gen.get_next_addr()
        self.consume(TokenType.OD)
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
        identifier = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.EQUAL)
        self.parse_arith_exp()
        self.consume(TokenType.TO)
        self.parse_arith_exp()
        if self.current_token().tok_type == TokenType.STEP:
            self.advance()
            self.parse_arith_exp()
        self.parse_do_loop()
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
        self.advance()
        if self.prev_token().tok_type not in EXPRESSION_RULES:
            return
        prefix = EXPRESSION_RULES[self.prev_token().tok_type].prefix
        if prefix == ExprAction.NONE:
            raise SyntaxError(f"Expected expression: {self.prev_token()}")
        self.parse_expr_action(prefix)

        if self.current_token().tok_type not in EXPRESSION_RULES:
            return
        while (
            precedence.value
            <= EXPRESSION_RULES[self.current_token().tok_type].precedence.value
        ):
            self.advance()
            self.parse_expr_action(EXPRESSION_RULES[self.prev_token().tok_type].infix)
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

    def parse_number(self):
        value = None
        if self.prev_token().tok_type == TokenType.INT_LITERAL:
            value = int(self.prev_token().value)
        elif self.prev_token().tok_type == TokenType.HEX_LITERAL:
            value = int(self.prev_token().value, 16)
        if value < -65535 or value > 65535:
            raise SyntaxError(f"Numeric literal {value} out of range [-65535, 65535]")
        const_index = self.symbol_table.declare_constant(value)
        self.code_gen.emit_constant(const_index)

    def parse_grouping(self):
        self.parse_expression()
        self.consume(TokenType.OP_RPAREN)

    def parse_unary(self):
        operator_type = self.prev_token().tok_type
        self.parse_expr_precedence(ExprPrecedence.UNARY)
        if operator_type == TokenType.OP_MINUS:
            self.code_gen.emit_unary_minus()

    def parse_binary(self):
        operator_type = self.prev_token().tok_type
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
        self.parse_expr_precedence(ExprPrecedence.AND)
        jump_end.value = self.code_gen.get_next_addr()

    def parse_or(self):
        # OR is a short-circuiting operator
        jump_else = self.code_gen.emit_jump_if_false()
        jump_end = self.code_gen.emit_jump()
        jump_else.value = self.code_gen.get_next_addr()
        self.code_gen.emit_pop()
        self.parse_expr_precedence(ExprPrecedence.OR)
        jump_end.value = self.code_gen.get_next_addr()
