from enum import Enum

from retraction.tokens import Token, TokenType
from retraction.codegen import CodeGenForTest
from retraction.symtab import SymTab

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
    NONE = 0
    NUMBER = 1
    GROUPING = 2
    UNARY = 3
    BINARY = 4


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
    TokenType.LPAREN: ExprRule(
        ExprAction.GROUPING, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.RPAREN: ExprRule(ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE),
    TokenType.PLUS: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.TERM),
    TokenType.MINUS: ExprRule(ExprAction.UNARY, ExprAction.BINARY, ExprPrecedence.TERM),
    TokenType.TIMES: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
    ),
    TokenType.DIVIDE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
    ),
    TokenType.MOD: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.LSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.RSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.EQUAL: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.NE: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
    TokenType.GR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
    TokenType.GE: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
    TokenType.LS: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
    TokenType.LE: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
    TokenType.AND: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.AND),
    TokenType.OR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.OR),
    TokenType.XOR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.XOR),
    TokenType.INT: ExprRule(ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE),
    TokenType.HEX: ExprRule(ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE),
    TokenType.CHAR: ExprRule(ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE),
    TokenType.EOF: ExprRule(ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE),
}


class Parser:
    def __init__(
        self,
        tokens: list[Token],
        directives,
        code_gen: CodeGenForTest,
        symbol_table: SymTab,
    ):
        self.tokens = tokens
        self.current_token_index = 0
        self.directives = directives
        self.code_gen = code_gen
        self.symbol_table = symbol_table

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
        if token is None or token.type != token_type:
            raise SyntaxError(f"Expected token {token_type}, got {token}")
        self.advance()
        return token

        # if self.current_token() is None or self.current_token().type != token_type:
        #     raise SyntaxError(
        #         f"Expected token {token_type}, got {self.current_token()}"
        #     )
        # self.advance()

    # <program> ::= <program> MODULE <prog module> | {MODULE} <prog module>
    def parse_program(self):
        # TODO: Not sure the grammar is correct here, but it's from the manual
        while self.current_token() is not None:
            if self.current_token().type == TokenType.MODULE:
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
        if self.current_token().type == TokenType.DEFINE:
            self.advance()
            self.parse_def_list()
            return True
        return False

    # <def list> ::= <def list>,<def> | <def>
    def parse_def_list(self) -> bool:
        if not self.parse_def():
            return False
        while self.current_token().type == TokenType.COMMA:
            self.advance()
            self.parse_def()
        return True

    # <def> ::= <identifier>=<str const>
    # TODO: Remove this when there's a preprocessing step to handle defines
    def parse_def(self) -> bool:
        if self.current_token().type != TokenType.VAR_T:
            return False
        if self.next_token().type != TokenType.EQUAL:
            return False
        identifier = self.current_token().value
        self.advance()
        self.advance()
        str_const = self.current_token().value
        self.consume(TokenType.STRING)
        self.directives.define(identifier, str_const)

    # <TYPE decl> ::= TYPE <rec ident list>
    def parse_type_decl(self) -> bool:
        if self.current_token().type == TokenType.TYPE:
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
        if self.current_token().type != TokenType.VAR_T:
            return False
        if self.next_token().type != TokenType.EQUAL:
            return False
        rec_name = self.current_token().value
        self.advance()
        self.advance()
        self.consume(TokenType.LBRACKET)
        self.parse_field_init()
        self.consume(TokenType.RBRACKET)

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
        if self.current_token().type not in [
            TokenType.CARD,
            TokenType.CHAR,
            TokenType.BYTE,
            TokenType.INT,
        ]:
            return None
        fund_type = self.current_token().type
        self.advance()
        return fund_type

    # <fund ident list> ::= <fund ident list>,<fund ident> | <fund ident>
    def parse_fund_ident_list(self, fund_type: TokenType) -> bool:
        if not self.parse_fund_ident(fund_type):
            return False
        while self.current_token().type == TokenType.COMMA:
            self.advance()
            self.parse_fund_ident(fund_type)
        return True

    # <fund ident> ::= <identifier>{=<init opts>}
    def parse_fund_ident(self, fund_type: TokenType) -> bool:
        if self.current_token().type != TokenType.VAR_T:
            return False
        identifier = self.current_token().value
        self.advance()
        if self.current_token().type == TokenType.EQUAL:
            self.advance()
            self.parse_init_opts(fund_type, identifier)
        else:
            self.code_gen.emit_fund_ident(fund_type, identifier)
        return True

        # identifier = self.current_token().value
        # self.expect(TokenType.VAR_T)
        # if self.current_token().type == TokenType.EQUAL:
        #     self.advance()
        #     self.parse_init_opts(fund_type, identifier)
        # else:
        #     self.code_gen.emit_fund_ident(fund_type, identifier)

    # <init opts> ::= <addr> | [<value>]
    def parse_init_opts(self, fund_type: TokenType, identifier: str) -> bool:
        if self.current_token().type == TokenType.LBRACKET:
            self.advance()
            value = self.parse_value_const()
            self.consume(TokenType.RBRACKET)
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
        if self.current_token().type == TokenType.INT:
            return self.parse_dec_num()
        if self.current_token().type == TokenType.HEX:
            return self.parse_hex_num()
        if self.current_token().type == TokenType.CHAR:
            return self.parse_char()
        raise SyntaxError(f"Unexpected token: {self.current_token()}")

    # <dec num> ::= <digit>{<digit>}
    def parse_dec_num(self) -> int:
        return int(self.consume(TokenType.INT).value)

    # <hex num> ::= $<hex digit>{<hex digit>}
    def parse_hex_num(self) -> int:
        return int(self.consume(TokenType.HEX).value, 16)

    # <char> ::= '<char const>'
    def parse_char(self) -> str:
        return ord(self.consume(TokenType.CHAR).value)

    # <POINTER decl> ::= <ptr type> POINTER <ptr ident list>
    def parse_pointer_decl(self) -> bool:
        if self.next_token().type != TokenType.POINTER:
            return False
        ptr_type = self.current_token().value
        self.advance()
        self.advance()
        self.parse_ptr_ident_list(ptr_type)

    # <ptr ident list> ::= <ptr ident list>,<ptr ident> | <ptr ident>
    def parse_ptr_ident_list(self, ptr_type: str) -> bool:
        if not self.parse_ptr_ident(ptr_type):
            return False
        while self.current_token().type == TokenType.COMMA:
            self.advance()
            self.parse_ptr_ident(ptr_type)
        return True

    # <ptr ident> ::= <identifier>{=<value>}
    def parse_ptr_ident(self, ptr_type) -> bool:
        identifier = self.current_token().value
        self.consume(TokenType.VAR_T)
        if self.current_token().type == TokenType.EQUAL:
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
    def parse_array_decl(self):
        # TODO
        raise NotImplementedError()

    # Variable Declaration for Records
    # --------------------------------
    # <record decl> ::= <identifier> <rec ident list>
    # <address> ::= <comp const>
    # TODO: Probably need to refer to a symbol/type table to look up the record type to
    # distinguish between record and array or other declarations
    def parse_record_decl(self) -> bool:
        if self.current_token().type != TokenType.VAR_T:
            return False
        rec_type = self.current_token().value
        self.advance()
        return self.parse_rec_ident_list(rec_type)

    # <rec ident list> ::= <rec ident list>,<rec ident> | <rec ident>
    def parse_rec_ident_list(self, rec_type: str) -> bool:
        if not self.parse_rec_ident(rec_type):
            return False
        while self.current_token().type == TokenType.COMMA:
            self.advance()
            self.parse_rec_ident(rec_type)

    # <rec ident> ::= <identifier>{=<address>}
    def parse_rec_ident(self, rec_type: str) -> bool:
        if self.current_token().type != TokenType.VAR_T:
            return False
        identifier = self.current_token().value
        self.advance()
        if self.current_token().type == TokenType.EQUAL:
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
    #         self.consume(TokenType.VAR_T)
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
    #     if self.current_token().type != TokenType.VAR_T:
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
    #     if self.current_token().type != TokenType.VAR_T:
    #         return None
    #     identifier = self.current_token().value
    #     self.advance()
    #     if self.current_token().type != TokenType.CARET:
    #         return None
    #     self.advance()
    #     return StubExpressionNode(f"ptr_ref({identifier})")

    # # <rec ref> ::= <identifier>.<identifier>
    # def parse_rec_ref(self) -> ExpressionNode | None:
    #     if self.current_token().type != TokenType.VAR_T:
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
    #     if self.current_token().type != TokenType.VAR_T:
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
        if self.current_token().type == TokenType.RETURN:
            self.code_gen.emit_return()
            self.advance()
        return True

    # <proc decl> ::= PROC <identifier>{=<addr>}({<param decl>})
    def parse_proc_decl(self) -> bool:
        if self.current_token().type != TokenType.PROC:
            return False
        self.advance()
        identifier = self.consume(TokenType.VAR_T).value
        if self.current_token().type == TokenType.EQUAL:
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
        if self.current_token().type == TokenType.RETURN:
            self.advance()
            self.consume(TokenType.LPAREN)
            self.parse_arith_exp()
            self.consume(TokenType.RPAREN)
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
        identifier = self.consume(TokenType.VAR_T).value
        if self.current_token().type == TokenType.PERIOD:
            self.advance()
            addr = self.parse_addr()
        self.consume(TokenType.LPAREN)
        self.parse_param_decl()
        self.consume(TokenType.RPAREN)
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

        # while (
        #     (
        #         self.current_token()
        #         in [
        #             TokenType.IF,
        #             TokenType.DO,
        #             TokenType.WHILE,
        #             TokenType.FOR,
        #         ]
        #     )
        #     or (
        #         self.current_token().type == TokenType.VAR_T
        #         and self.next_token().type == TokenType.EQUAL
        #     )
        #     or (self.current_token().type == TokenType.LBRACK)
        # ):
        #     self.parse_stmt()

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
        if self.parse_assign_stmt():
            return True
        if self.parse_exit_stmt():
            return True
        if self.parse_routine_call():
            return True
        return False

    # <assign stmt> ::= <mem contents>=<arith exp>
    def parse_assign_stmt(self) -> bool:
        if self.next_token().type == TokenType.EQUAL:
            mem_contents = self.parse_mem_contents()
            self.consume(TokenType.EQUAL)
            self.parse_arith_exp()
            self.code_gen.emit_assign_stmt(mem_contents)
            return True
        return False

    # <EXIT stmt> ::= EXIT
    def parse_exit_stmt(self) -> bool:
        if self.current_token().type == TokenType.EXIT:
            self.advance()
            self.code_gen.emit_exit_stmt()
            return True
        return False

    # <routine call> ::= <FUNC call> | <PROC call>
    # <FUNC call> ::= <identifier>({<params>})
    # <PROC call> ::= <identifier>({<params>})
    # "Function calls can be used in any arithmetic expression, with one exception:
    # Functions calls may NOT be used in an
    # arithmetic expression when that expression is used
    # as a parameter in a routine call or declaration."
    def parse_routine_call(self):
        if self.parsing_params:
            raise SyntaxError(
                "A function call may not be used as a parameter in a routine call or declaration"
            )
        identifier = self.current_token().value
        self.consume(TokenType.VAR_T)
        self.consume(TokenType.LPAREN)
        if self.current_token().type != TokenType.RPAREN:
            self.parse_params()
        self.consume(TokenType.RPAREN)
        self.code_gen.emit_routine_call(identifier)

    # <params> ::= <params>,<arith exp> | <arith exp>
    def parse_params(self):
        try:
            self.parsing_params = True
            self.parse_arith_exp()
            param_count = 1
            while self.current_token().type == TokenType.COMMA:
                self.advance()
                self.parse_arith_exp(False)
                param_count += 1
                if param_count > 8:
                    raise SyntaxError("Too many parameters (max 8)")
        finally:
            self.parsing_params = False

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
        if self.current_token().type != TokenType.IF:
            return False
        self.advance()
        cond_exp = self.parse_cond_exp()
        self.consume(TokenType.THEN)
        self.parse_stmt_list()
        while self.parse_elseif_exten():
            pass
        self.parse_else_exten()
        self.consume(TokenType.FI)
        return True

    # <cond exp> ::= <complex rel>
    # Note: This was not in the manual but it seems like they are synonymous
    def parse_cond_exp(self) -> bool:
        return self.parse_expression()

    def parse_arith_exp(self) -> bool:
        return self.parse_expression()

    # <ELSEIF exten> ::= ELSEIF <cond exp> THEN {stmt list}
    def parse_elseif_exten(self) -> bool:
        if self.current_token().type != TokenType.ELSEIF:
            return False
        self.advance()
        self.parse_cond_exp()
        self.consume(TokenType.THEN)
        self.parse_stmt_list()
        return True

    # <ELSE exten> ::= ELSE {stmt list}
    def parse_else_exten(self) -> bool:
        if self.current_token().type != TokenType.ELSE:
            return False
        self.advance()
        self.parse_stmt_list()
        return True

    # <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
    def parse_do_loop(self) -> bool:
        if self.current_token().type != TokenType.DO:
            return False
        self.advance()
        self.parse_stmt_list()
        self.parse_until_stmt()
        self.consume(TokenType.OD)
        return True

    # <UNTIL stmt> ::= UNTIL <cond exp>
    def parse_until_stmt(self) -> bool:
        if self.current_token().type != TokenType.UNTIL:
            return False
        self.advance()
        self.parse_cond_exp()
        return True

    # <WHILE loop> ::= WHILE <cond exp> <DO loop>
    def parse_while_loop(self) -> bool:
        if self.current_token().type != TokenType.WHILE:
            return False
        self.advance()
        self.parse_cond_exp()
        self.parse_do_loop()
        return True

    # <FOR loop> ::= FOR <identifier>=<start> TO <finish> {STEP <inc>}<DO loop>
    # <start> ::= <arith exp>
    # <finish> ::= <arith exp>
    # <inc> ::= <arith exp>
    def parse_for_loop(self) -> bool:
        if self.current_token().type != TokenType.FOR:
            return False
        self.advance()
        identifier = self.consume(TokenType.VAR_T).value
        self.consume(TokenType.EQUAL)
        self.parse_arith_exp()
        self.consume(TokenType.TO)
        self.parse_arith_exp()
        if self.current_token().type == TokenType.STEP:
            self.advance()
            self.parse_arith_exp()
        self.parse_do_loop()
        return True

    # <code block> ::= [<comp const list>]
    def parse_code_block(self) -> bool:
        if self.current_token().type != TokenType.LBRACK:
            return False
        self.advance()
        self.parse_comp_const_list()
        self.consume(TokenType.RBRACK)
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
        prefix = EXPRESSION_RULES[self.prev_token().type].prefix
        if prefix == ExprAction.NONE:
            raise SyntaxError(f"Expected expression: {self.prev_token()}")
        self.parse_expr_action(prefix)

        while (
            precedence.value
            <= EXPRESSION_RULES[self.current_token().type].precedence.value
        ):
            self.advance()
            self.parse_expr_action(EXPRESSION_RULES[self.prev_token().type].infix)

    def parse_expr_action(self, action: ExprAction):
        if action == ExprAction.NUMBER:
            self.parse_number()
        elif action == ExprAction.GROUPING:
            self.parse_grouping()
        elif action == ExprAction.UNARY:
            self.parse_unary()
        elif action == ExprAction.BINARY:
            self.parse_binary()

    def parse_number(self):
        if self.prev_token().type == TokenType.INT:
            self.code_gen.emit_number(int(self.prev_token().value))
        elif self.prev_token().type == TokenType.HEX:
            self.code_gen.emit_number(int(self.prev_token().value, 16))

    def parse_grouping(self):
        self.parse_expression()
        self.consume(TokenType.RPAREN)

    def parse_unary(self):
        operator_type = self.prev_token().type
        self.parse_expr_precedence(ExprPrecedence.UNARY)
        if operator_type == TokenType.MINUS:
            self.code_gen.emit_unary_minus()

    def parse_binary(self):
        operator_type = self.prev_token().type
        rule = EXPRESSION_RULES[operator_type]
        self.parse_expr_precedence(ExprPrecedence(rule.precedence.value + 1))

        if operator_type == TokenType.PLUS:
            self.code_gen.emit_add()
        elif operator_type == TokenType.MINUS:
            self.code_gen.emit_subtract()
        elif operator_type == TokenType.TIMES:
            self.code_gen.emit_multiply()
        elif operator_type == TokenType.DIVIDE:
            self.code_gen.emit_divide()

    def parse_comp_const(self):
        components = [self.parse_base_comp_const()]
        while (
            self.current_token() is not None
            and self.current_token().type == TokenType.PLUS
        ):
            self.advance()  # Consume the '+' token
            components.append(self.parse_base_comp_const())
        return {"type": "comp_const", "components": components}

    def parse_base_comp_const(self):
        token = self.current_token()
        if token.type == TokenType.IDENTIFIER:
            self.advance()  # Consume the identifier
            return {"type": "identifier", "value": token.value}
        elif token.type == TokenType.NUM_CONST:
            self.advance()  # Consume the numeric constant
            return {"type": "num_const", "value": token.value}
        elif token.type == TokenType.PTR_REF:
            self.advance()  # Consume the pointer reference
            return {"type": "ptr_ref", "value": token.value}
        elif token.type == TokenType.STAR:
            self.advance()  # Consume the '*' token
            return {"type": "star"}
        else:
            raise SyntaxError(f"Unexpected token in base comp const: {token}")

    def parse_param_decl(self):
        # Implement the parsing logic for <param decl>
        # For now, just return a placeholder
        return {"type": "param_decl"}

    def parse_system_decls(self):
        # Implement the parsing logic for <system decls>
        # For now, just return a placeholder
        return {"type": "system_decls"}

    def parse_stmt_list(self):
        # Implement the parsing logic for <stmt list>
        # For now, just return a placeholder
        return {"type": "stmt_list"}