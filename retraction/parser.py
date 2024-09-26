from enum import Enum, auto
import sys
from typing import cast

from retraction import ast
from retraction.pratt import EXPRESSION_RULES, ExprAction, ExprPrecedence
from retraction.tokens import Token, TokenType
from retraction.error import IdentifierError, InternalError, SyntaxError
from retraction.types import (
    ArrayType,
    FundamentalType,
    PointerType,
    Type,
    RecordType,
)

from retraction.symtab import EntryType, SymTab, Entry


OP_MAP: dict[TokenType, ast.Op] = {
    TokenType.OP_PLUS: ast.Op.ADD,
    TokenType.OP_MINUS: ast.Op.SUB,
    TokenType.OP_TIMES: ast.Op.MUL,
    TokenType.OP_DIVIDE: ast.Op.DIV,
    TokenType.MOD: ast.Op.MOD,
    TokenType.LSH: ast.Op.LSH,
    TokenType.RSH: ast.Op.RSH,
    TokenType.OP_EQ: ast.Op.EQ,
    TokenType.OP_NE: ast.Op.NE,
    TokenType.OP_GT: ast.Op.GT,
    TokenType.OP_GE: ast.Op.GE,
    TokenType.OP_LT: ast.Op.LT,
    TokenType.OP_LE: ast.Op.LE,
    TokenType.AND: ast.Op.AND,
    TokenType.OR: ast.Op.OR,
    TokenType.OP_BIT_AND: ast.Op.BIT_AND,
    TokenType.OP_BIT_OR: ast.Op.BIT_OR,
    TokenType.OP_BIT_XOR: ast.Op.BIT_XOR,
}


def token_type_to_fundamental_type(token_type: TokenType) -> FundamentalType:
    if token_type == TokenType.BYTE:
        return FundamentalType.BYTE_T
    if token_type == TokenType.CHAR:
        return FundamentalType.CHAR_T
    if token_type == TokenType.INT:
        return FundamentalType.INT_T
    if token_type == TokenType.CARD:
        return FundamentalType.CARD_T
    raise InternalError(
        f"Invalid token type {token_type} when parsing fundamental type"
    )


class RoutineCategory(Enum):
    PROC = auto()
    FUNC = auto()


class Parser:
    """
    This is primarily a recursive descent parser, but expressions are parsed using
    the Pratt method for handling operator precedence.
    """

    def __init__(
        self,
        tokens: list[Token],
        symbol_table: SymTab,
    ):
        self.tokens = tokens
        self.current_token_index = 0
        self.symbol_table = symbol_table

        # Parsing state
        self.parsing_param_decl = False
        self.exits_to_patch: list[list[int]] = []  # Addresses of jumps to patch
        self.parsing_routine: RoutineCategory | None = None
        self.routine_return_type: Type = FundamentalType.VOID_T
        self.typed_expression = None
        self.last_t: Type | None = None

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
            raise SyntaxError(f"Expected {token_type}, got {token}")
        return self.advance()

    def parse_dev(self):
        self.parse_expression()

    def parse_program(self) -> ast.Program:
        """
        <program> ::= <program> MODULE <prog module> | {MODULE} <prog module>
        """
        # try:
        modules: list[ast.Module] = []
        # First MODULE is optional
        if self.current_token().tok_type == TokenType.MODULE:
            self.advance()
        modules.append(self.parse_prog_module())

        while self.current_token().tok_type == TokenType.MODULE:
            self.advance()
            self.parsing_routine = None
            modules.append(self.parse_prog_module())

        return ast.Program(modules, self.symbol_table)  # type: ignore
        # except SyntaxError as e:
        #     self.error(e.msg)
        #     raise e
        # except Exception as e:
        #     self.error(str(e))
        #     raise e

    def parse_prog_module(self) -> ast.Module:
        """
        <prog module> ::= {<system decls>} <routine list>
        """
        return ast.Module(self.parse_system_decls(), self.parse_routine_list())

    def parse_system_decls(self) -> list[ast.Decl]:
        """
        The grammar uses lower-level rules for decl repetition, but we handle it at higher
        levels instead, like here.
        <system decls> ::= <DEFINE decl> | <TYPE decl> | <var decl>
        """
        decls: list[ast.Decl] = []
        while True:
            decl = self.parse_system_decl()
            if decl is None:
                break
            if isinstance(decl, list):
                for d in decl:
                    decls.append(d)
            else:
                decls.append(decl)

        return decls

    def parse_system_decl(self) -> ast.StructDecl | list[ast.VarDecl] | None:
        """
        Parse a single system decl
        """
        # We don't parse defines. They will be handled in a preprocessing step.
        # if self.parse_define_decl():
        #     return True
        record_decl = self.parse_type_decl()
        if record_decl is not None:
            self.symbol_table.add_entry(record_decl.name, EntryType.RECORD, record_decl)
            return record_decl
        var_decl = self.parse_var_decl(True)
        if var_decl is not None:
            for v in var_decl:
                self.symbol_table.add_entry(v.name, EntryType.VAR, v)
            return var_decl
        return None

    def parse_type_decl(self) -> ast.StructDecl | None:
        """
        Note: The grammar specifies multiple type declarations, but this is unnecessary
        because higher-level rules already handle repetition. So we just parse a single
        record declaration here.
        <TYPE decl> ::= TYPE <rec ident list>
        <rec ident list> ::= <rec ident list> <rec ident> | <rec ident>
        <rec ident> ::= <rec name>=[<field init>]
        """
        if self.current_token().tok_type != TokenType.TYPE:
            return None
        self.advance()
        rec_name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.OP_EQ)
        self.consume(TokenType.OP_LBRACK)
        field_list = self.parse_field_init()
        self.consume(TokenType.OP_RBRACK)
        return ast.StructDecl(rec_name, field_list)

    def parse_field_init(self) -> list[ast.VarDecl]:
        """
        As with some other rules, we handle repetition differently from the published
        grammar. Here, we iterate over fund decls until we reach the closing bracket.
        <field init> ::= <fund var decl>
        """
        fields: list[ast.VarDecl] = []
        while True:
            curr_fields = self.parse_fund_decl(False)
            if curr_fields is None:
                break
            fields = fields + curr_fields
        # Empty record is an error, matching behavior of the original Action! compiler.
        if len(fields) == 0:
            raise SyntaxError("Empty record declaration")
        return fields

    def parse_var_decl(self, allow_init: bool) -> list[ast.VarDecl] | None:
        """
        Repetition is handled at higher levels, so we just parse a single var decl here.
        But keep in mind, a single var decl can declare multiple variables (e.g. "BYTE x, y, z")
        <var decl> ::= <var decl> <base var decl> | <base var decl>
        """
        return self.parse_base_var_decl(allow_init)

    def parse_base_var_decl(self, allow_init: bool) -> list[ast.VarDecl] | None:
        """
        <base var decl> ::= <fund decl> | <POINTER decl> | <ARRAY decl> | <record decl>
        """
        ptr_decl = self.parse_pointer_decl(allow_init)
        if ptr_decl:
            return ptr_decl
        array_decl = self.parse_array_decl(allow_init)
        if array_decl:
            return array_decl
        # Note: The order of these checks is important. Pointer and array declarations
        # are checked before fund decl because they start with the same token
        # (e.g. BYTE POINTER x vs. BYTE x)
        fund_decl = self.parse_fund_decl(allow_init)
        if fund_decl:
            return fund_decl
        record_decl = self.parse_record_decl()
        if record_decl:
            return record_decl
        return None

    def parse_fund_decl(self, allow_init: bool) -> list[ast.VarDecl] | None:
        """
        # Variable Declaration for Fundamental Data Types
        # <fund decl> ::= <fund decl> <base fund decl> | <base fund decl>
        """
        # This recurrence rule seems unnecessary and potentially problematic. Higher-level rules
        # already handle repetition. So we just parse a single base fund decl here.
        return self.parse_base_fund_decl(allow_init)

    def parse_base_fund_decl(self, allow_init: bool) -> list[ast.VarDecl] | None:
        """
        <base fund decl> ::= <fund type> <fund ident list>
        """
        # Skip if it's a FUNC decl
        if (
            self.current_token().is_fund_type()
            and self.next_token().tok_type == TokenType.FUNC
        ):
            return None
        fund_t = self.parse_fund_type()
        if fund_t is None:
            return None
        return self.parse_fund_ident_list(fund_t, allow_init)

    def parse_fund_type(self) -> FundamentalType | None:
        """
        <fund type> ::= CARD | CHAR | BYTE | INT
        """
        if self.current_token().tok_type not in [
            TokenType.CARD,
            TokenType.CHAR,
            TokenType.BYTE,
            TokenType.INT,
        ]:
            return None
        fund_t = self.current_token().tok_type
        self.advance()
        return token_type_to_fundamental_type(fund_t)

    def parse_fund_ident_list(
        self, fund_t: FundamentalType, allow_init: bool
    ) -> list[ast.VarDecl]:
        """
        This handles stuff like "INT x, y, z = 1, a, b = 2"
        <fund ident list> ::= <fund ident list>,<fund ident> | <fund ident>
        """
        var_decls: list[ast.VarDecl] = []
        var_decls.append(self.parse_fund_ident(fund_t, allow_init))
        while (
            self.current_token().tok_type == TokenType.OP_COMMA
            and self.next_token().tok_type == TokenType.IDENTIFIER
        ):
            self.advance()
            var_decls.append(self.parse_fund_ident(fund_t, allow_init))
        return var_decls

    def parse_fund_ident(
        self,
        fund_t: FundamentalType,
        allow_init: bool,
    ) -> ast.VarDecl:
        """
        <fund ident> ::= <identifier>{=<init opts>}
        """
        identifier = self.consume(TokenType.IDENTIFIER).value
        init_opts = self.parse_init_opts(allow_init)

        return ast.VarDecl(identifier, fund_t, init_opts)

    def parse_init_opts(self, allow_init: bool) -> ast.InitOpts | None:
        """
        <init opts> ::= <addr> | [<value>]
        <addr> ::= <comp const>
        <value> ::= <num const>
        <num const> ::= <dec num> | <hex num> | <char>
        """
        if self.current_token().tok_type == TokenType.OP_EQ:
            if not allow_init:
                raise SyntaxError("Declaration may not have an initial value")
            self.advance()
            if self.current_token().tok_type == TokenType.OP_LBRACK:
                self.advance()
                value = self.current_token().int_value()
                self.advance()
                self.consume(TokenType.OP_RBRACK)
                return ast.InitOpts([value], False)
            else:
                addr = self.parse_addr()
                return ast.InitOpts([addr], True)
        return None

    def parse_fund_or_record_type(self) -> FundamentalType | RecordType | None:
        """
        <fund or record type> ::= <fund type> | <record type>
        """
        fund_t = self.parse_fund_type()
        if fund_t is not None:
            return fund_t
        record_t = self.parse_record_type()
        if record_t:
            return record_t
        return None

    def parse_pointer_decl(
        self,
        allow_init: bool,
    ) -> list[ast.VarDecl] | None:
        """
        <POINTER decl> ::= <ptr type> POINTER <ptr ident list>
        """
        if not self.next_token() or self.next_token().tok_type != TokenType.POINTER:
            return None
        ref_t = self.parse_fund_or_record_type()
        if ref_t is None:
            raise SyntaxError(
                "Expected fundamental or record type in pointer declaration"
            )
        self.advance()
        return self.parse_ptr_ident_list(ref_t, allow_init)

    def parse_ptr_ident_list(
        self,
        ref_t: FundamentalType | RecordType,
        allow_init: bool,
    ) -> list[ast.VarDecl] | None:
        """
        <ptr ident list> ::= <ptr ident list>,<ptr ident> | <ptr ident>
        """
        ptr_var_decls: list[ast.VarDecl] = []
        ptr_var_decls.append(self.parse_ptr_ident(ref_t, allow_init))
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            ptr_var_decls.append(self.parse_ptr_ident(ref_t, allow_init))
        return ptr_var_decls

    def parse_ptr_ident(
        self,
        ref_type: FundamentalType | RecordType,
        allow_init: bool,
    ) -> ast.VarDecl:
        """
        <ptr ident> ::= <identifier>{=<value>}
        """
        identifier = self.current_token().value
        self.consume(TokenType.IDENTIFIER)
        if self.current_token().tok_type == TokenType.OP_EQ:
            if not allow_init:
                raise SyntaxError("Declaration may not have an initial value")
            self.advance()
            value = self.parse_comp_const()
            if value is None:
                raise SyntaxError("Expected constant value in pointer declaration")
            return ast.VarDecl(
                identifier, PointerType(ref_type), ast.InitOpts([value], False)
            )
        return ast.VarDecl(identifier, PointerType(ref_type), None)

    def parse_array_decl(self, allow_init: bool) -> list[ast.VarDecl] | None:
        """
        Variable Declaration for Arrays
        <ARRAY decl> ::= <fund type> ARRAY <arr ident list>
        <arr ident list> ::= <arr ident list>,<arr ident> |
        <arr ident>
        <arr ident> ::= <identifier>{(<dim>)}{=<arr init opts>}
        <dim> ::= <num const>
        <arr init opts> ::= <addr> | [<value>] | <str const>
        <addr> ::= <comp const>
        <value list> ::= <value list><value> | <value>
        <value> ::= <comp const>
        """
        if not self.next_token() or self.next_token().tok_type != TokenType.ARRAY:
            return None
        fund_t = self.parse_fund_type()
        if fund_t is None:
            raise SyntaxError("Expected fundamental type in array declaration")
        self.consume(TokenType.ARRAY)
        return self.parse_arr_ident_list(fund_t, allow_init)

    def parse_arr_ident_list(
        self,
        fund_t: FundamentalType,
        allow_init: bool,
    ) -> list[ast.VarDecl]:
        """
        <arr ident list> ::= <arr ident list>,<arr ident> | <arr ident>
        """
        arr_var_decls: list[ast.VarDecl] = []
        arr_var_decls.append(self.parse_arr_ident(fund_t, allow_init))
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            arr_var_decls.append(self.parse_arr_ident(fund_t, allow_init))
        return arr_var_decls

    def parse_arr_ident(
        self,
        fund_t: FundamentalType,
        allow_init: bool,
    ) -> ast.VarDecl:
        """
        <arr ident> ::= <identifier>{(<dim>)}{=<arr init opts>}
        """
        identifier = self.consume(TokenType.IDENTIFIER).value
        dim = self.parse_dimensions()
        init_opts = self.parse_arr_init_opts(allow_init)
        if dim is None and init_opts is None:
            self.warn("Array declaration has no dimensions or initialization")
        elif (
            dim is not None
            and init_opts is not None
            and dim != len(init_opts.initial_values)
        ):
            self.warn(
                f"Array dimension {dim} does not match initialization length {len(init_opts.initial_values)}, will allocated based on initialization length"
            )
        return ast.VarDecl(identifier, ArrayType(fund_t, dim), init_opts)

    def parse_dimensions(self) -> int | None:
        """
        <dim> ::= <num const>
        """
        if self.current_token().tok_type != TokenType.OP_LPAREN:
            return None
        self.advance()
        dim = self.parse_comp_const()
        if dim is None:
            raise SyntaxError("Expected constant value in array dimension")
        self.consume(TokenType.OP_RPAREN)
        return dim

    def parse_arr_init_opts(self, allow_init: bool) -> ast.InitOpts | None:
        """
        Note: Grammar says <value> but it would seem to be <value list> based on the
        examples in the manual.
        <arr init opts> ::= <addr> | [<value list>] | <str const>
        """
        if self.current_token().tok_type != TokenType.OP_EQ:
            return None
        if not allow_init:
            raise SyntaxError("Declaration may not have an initial value")
        self.advance()
        if self.current_token().tok_type == TokenType.OP_LBRACK:
            self.advance()
            values = self.parse_value_list()
            self.consume(TokenType.OP_RBRACK)
            return ast.InitOpts(values, False)
        elif self.current_token().tok_type == TokenType.STRING_LITERAL:
            str_literal = self.current_token().value
            self.advance()
            values = [len(str_literal)] + [ord(c) for c in str_literal]
            return ast.InitOpts(values, False)
        addr = self.parse_addr()
        return ast.InitOpts([addr], True)

    def parse_value_list(self) -> list[int]:
        """
        <value list> ::= <value list><value> | <value>
        """
        values = []
        while self.current_token().tok_type != TokenType.OP_RBRACK:
            value = self.parse_comp_const()
            if value is None:
                raise SyntaxError("Expected constant value in array initialization")
            values.append(value)
            # Commas may or may not separate values. Note: this allows trailing commas.
            if self.current_token().tok_type == TokenType.OP_COMMA:
                self.advance()
        return values

    def parse_record_type(self) -> RecordType | None:
        """
        <record type> ::= <identifier>
        """
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return None
        identifier = self.current_token().value
        symtab_entry, _ = self.symbol_table.find(identifier)
        if symtab_entry is None or symtab_entry.entry_type != EntryType.RECORD:
            return None
        self.advance()
        return RecordType(identifier)

    def parse_record_decl(self) -> list[ast.VarDecl] | None:
        """
        Variable Declaration for Records
        <record decl> ::= <identifier> <rec ident list>
        <address> ::= <comp const>
        TODO: Probably need to refer to a symbol/type table to look up the record type to
        distinguish between record and array or other declarations
        """
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return None
        # Make sure it's a record.
        identifier = self.current_token().value
        symtab_entry, _ = self.symbol_table.find(identifier)
        if symtab_entry is None or symtab_entry.entry_type != EntryType.RECORD:
            return None
        self.advance()
        return self.parse_rec_ident_list(RecordType(identifier))

    def parse_rec_ident_list(
        self,
        record_t: RecordType,
    ) -> list[ast.VarDecl]:
        """
        <rec ident list> ::= <rec ident list>,<rec ident> | <rec ident>
        """
        rec_idents: list[ast.VarDecl] = []
        rec_idents.append(self.parse_rec_ident(record_t))
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            rec_idents.append(self.parse_rec_ident(record_t))
        return rec_idents

    def parse_rec_ident(
        self,
        record_t: RecordType,
    ) -> ast.VarDecl:
        """
        <rec ident> ::= <identifier>{=<address>}
        """
        identifier = self.consume(TokenType.IDENTIFIER).value
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            addr = self.parse_addr()
            return ast.VarDecl(identifier, record_t, ast.InitOpts([addr], True))
        else:
            return ast.VarDecl(identifier, record_t, None)

    def parse_routine_list(self) -> list[ast.Routine]:
        """
        <routine list> ::= <routine list> <routine> | <routine>
        """
        routines: list[ast.Routine] = []
        while True:
            routine = self.parse_routine()
            if routine is None:
                break
            routines.append(routine)
        return routines

    def parse_routine(self) -> ast.Routine | None:
        """
        <routine> ::= <proc routine> | <func routine>
        <proc routine> ::= <PROC decl> {<system decls>} {<stmt list>}{RETURN}
        <proc decl> ::= PROC <identifier>{=<addr>}({<param decl>})
        <func routine> ::= <FUNC decl> {<system decls>} {<stmt list>}{RETURN (<arith exp>)}
        <FUNC decl> ::= <fund type> FUNC <identifier>{.<addr>} ({<param decl>})
        The RETURN token is optional because it's desirable to be able to fall through
        to the next routine on a 6502.
        The ".<addr>" appears to be a typo in the grammar. It should be "=<addr>".
        """
        return_t: FundamentalType = FundamentalType.VOID_T
        if self.current_token().tok_type == TokenType.PROC:
            self.advance()
        elif (
            self.current_token().is_fund_type()
            and self.next_token().tok_type == TokenType.FUNC
        ):
            parsed_return_t = self.parse_fund_type()
            if parsed_return_t is None:
                raise SyntaxError("Expected return type in function declaration")
            return_t = parsed_return_t
            self.consume(TokenType.FUNC)
        else:
            return None
        identifier = self.consume(TokenType.IDENTIFIER).value
        fixed_addr = None
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            fixed_addr = self.parse_addr()
        try:
            self.parsing_routine = (
                RoutineCategory.PROC
                if return_t == FundamentalType.VOID_T
                else RoutineCategory.FUNC
            )
            # Push symbol table stack
            outer_symbol_table = self.symbol_table
            self.symbol_table = SymTab(outer_symbol_table)
            # self.symbol_table.parent = outer_symbol_table
            self.consume(TokenType.OP_LPAREN)
            param_decls = self.parse_param_decls()
            self.consume(TokenType.OP_RPAREN)
            system_decls = self.parse_system_decls()
            statements = self.parse_stmt_list()
            routine = ast.Routine(
                identifier,
                param_decls,
                system_decls,
                statements,
                fixed_addr,
                return_t,
                self.symbol_table,  # type: ignore
            )
            if self.symbol_table.parent is None:
                raise InternalError(
                    "Symbol table parent should not be None after parsing routine"
                )
            outer_symbol_table.add_entry(identifier, EntryType.ROUTINE, routine)
            return routine
        finally:
            # Restore state
            self.symbol_table = outer_symbol_table
            self.parsing_routine = None

    def parse_addr(self) -> int:
        """
        <addr> ::= <comp const>
        """
        value = self.parse_comp_const()
        if value is None:
            raise SyntaxError("Expected constant value for address")
        return value

    def parse_comp_const(self) -> int | None:
        """
        TODO: Implement this correctly, which includes allowing addition and references to function addresses...
        For now, just parse a number
        """
        value = 0
        if self.current_token().tok_type == TokenType.INT_LITERAL:
            value = int(self.current_token().value)
        elif self.current_token().tok_type == TokenType.HEX_LITERAL:
            value = int(self.current_token().value, 16)
        elif self.current_token().tok_type == TokenType.CHAR_LITERAL:
            value = ord(self.current_token().value)
        else:
            return None
        if value < -65535 or value > 65535:
            raise SyntaxError(f"Numeric literal {value} out of range [-65535, 65535]")
        self.advance()
        return value

    def parse_param_decls(self) -> list[ast.VarDecl]:
        """
        <param decls> ::= <param decls>,<param decl> | <param decl>  (Not in Action! manual)
        <param decl> ::= <var decl>
        TODO: Implement limit of 8 parameters
        """
        if self.parsing_param_decl:
            raise InternalError(
                "Nested parameter declarations, should not happen due to guards in routine decl parsing"
            )
        try:
            self.parsing_param_decl = True
            param_decls: list[ast.VarDecl] = []

            while self.current_token().tok_type != TokenType.OP_RPAREN:
                var_decl = self.parse_var_decl(False)
                if var_decl is None:
                    raise SyntaxError("Expected parameter declaration")
                param_decls += var_decl
                if self.current_token().tok_type == TokenType.OP_COMMA:
                    self.advance()
            for p in param_decls:
                # Put each param in the symbol table.
                self.symbol_table.add_entry(p.name, EntryType.VAR, p)
            return param_decls
        finally:
            self.parsing_param_decl = False

    def parse_stmt_list(self) -> list[ast.Statement]:
        """
        <stmt list> ::= <stmt list> <stmt> | <stmt>
        """
        stmts: list[ast.Statement] = []
        while True:
            stmt = self.parse_stmt()
            if stmt is None:
                break
            stmts.append(stmt)
        return stmts

    def parse_stmt(self) -> ast.Statement | None:
        """
        <stmt> ::= <simp stmt> | <struc stmt> | <code block>
        """
        # If in a routine and we see a PROC or FUNC decl, it's not a statement
        # TODO: Also make sure it's a top-level statement? (e.g. not in an IF block)
        if self.parsing_routine is not None and (
            self.current_token().tok_type == TokenType.PROC
            or (
                self.current_token().is_fund_type()
                and self.next_token().tok_type == TokenType.FUNC
            )
        ):
            return None

        simp_stmt = self.parse_simp_stmt()
        if simp_stmt:
            return simp_stmt
        struc_stmt = self.parse_struc_stmt()
        if struc_stmt:
            return struc_stmt
        code_block = self.parse_code_block()
        if code_block:
            return code_block
        return None

    def parse_simp_stmt(self) -> ast.Statement | None:
        """
        <simp stmt> ::= <assign stmt> | <EXIT stmt> | <routine call>
        """
        devprint_stmt = self.parse_devprint_stmt()
        if devprint_stmt:
            return devprint_stmt
        assign_stmt = self.parse_assign_stmt()
        if assign_stmt:
            return assign_stmt
        exit_stmt = self.parse_exit_stmt()
        if exit_stmt:
            return exit_stmt
        routine_call = self.parse_routine_call()
        if routine_call:
            return ast.CallStmt(routine_call)
        return_stmt = self.parse_return_stmt()
        if return_stmt:
            return return_stmt
        return None

    def parse_devprint_stmt(self) -> ast.DevPrint | None:
        """
        Debugging tool.
        TODO: Remove this when no longer needed
        """
        if self.current_token().tok_type != TokenType.DEVPRINT:
            return None
        self.advance()
        self.consume(TokenType.OP_LPAREN)
        expr = self.parse_arith_exp()
        self.consume(TokenType.OP_RPAREN)
        return ast.DevPrint(expr)

    def parse_assign_stmt(self) -> ast.Assign | None:
        """
        <assign stmt> ::= <mem contents>=<arith exp>
        <mem contents> ::= <fund ref> | <arr ref> | <ptr ref> | <rec ref>
        <fund ref> ::= <identifier>
        <arr ref> ::= <identifier>(<arith exp>)
        <ptr ref> ::= <identifier>^
        <rec ref> ::= <identifier>.<identifier>
        """
        # TODO: Handle aliases for self-assignment (e.g. x = x + 1 written as x ==+ 1)
        # Examples: b2==+1, b2==-b1, b2==& $0F, b2==LSH (5+3)
        var_target: ast.Expr | None = None
        if self.current_token().tok_type == TokenType.IDENTIFIER:
            identifier = self.current_token().value
            symbol_table_entry, _ = self.symbol_table.find(identifier)
            # Check symbol table to see if it's a variable
            if symbol_table_entry is None:
                raise IdentifierError(f"Undefined identifier: {identifier}")
            if symbol_table_entry.entry_type != EntryType.VAR:
                return None
            # Get type of variable from decl
            var_decl = cast(ast.VarDecl, symbol_table_entry.node)
            var_target = ast.Var(identifier, var_decl.var_t)
            if self.next_token().tok_type == TokenType.OP_EQ:
                self.advance()
                self.advance()
                # TODO: Need to check anything in symbol table about the variable here?
            elif self.next_token().tok_type == TokenType.OP_LPAREN:
                # TODO: Check to see if it's an array. Need to expand ast VarDecl to keep this info.
                self.advance()
                self.advance()
                rec_index_expr = self.parse_arith_exp()
                self.consume(TokenType.OP_RPAREN)
                self.consume(TokenType.OP_EQ)
                var_target = ast.ArrayAccess(var_target, rec_index_expr)
            elif self.next_token().tok_type == TokenType.OP_CARET:
                self.advance()
                self.advance()
                self.consume(TokenType.OP_EQ)
                var_target = ast.Dereference(var_target)
            elif self.next_token().tok_type == TokenType.OP_DOT:
                self.advance()
                self.advance()
                field_name = self.consume(TokenType.IDENTIFIER).value
                self.consume(TokenType.OP_EQ)
                var_target = ast.FieldAccess(var_target, field_name)

        if var_target is None:
            return None

        expr = self.parse_arith_exp()
        return ast.Assign(var_target, expr)

    def parse_exit_stmt(self) -> ast.Exit | None:
        """
        Equivalent to break statement in most languages.
        <EXIT stmt> ::= EXIT
        """
        if self.current_token().tok_type != TokenType.EXIT:
            return None
        self.advance()
        return ast.Exit()

    def parse_return_stmt(self) -> ast.Return | None:
        """
        <RETURN stmt> ::= RETURN | RETURN (<arith exp>) - depending on PROC or FUNC
        """
        if self.current_token().tok_type != TokenType.RETURN:
            return None
        self.advance()
        if self.parsing_routine is None:
            raise SyntaxError("RETURN statement outside of a routine")
        if self.parsing_routine == RoutineCategory.PROC:
            return ast.Return(None)
        self.consume(TokenType.OP_LPAREN)
        expr = self.parse_arith_exp()
        self.consume(TokenType.OP_RPAREN)
        return ast.Return(expr)

    def parse_routine_call(self) -> ast.Call | None:
        """
        <routine call> ::= <FUNC call> | <PROC call>
        <FUNC call> ::= <identifier>({<params>})
        <PROC call> ::= <identifier>({<params>})
        Note: Action! manual states: "Function calls can be used in any
        arithmetic expression, with one exception:
        Functions calls may NOT be used in an
        arithmetic expression when that expression is used
        as a parameter in a routine call or declaration."
        """
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return None
        if self.next_token().tok_type != TokenType.OP_LPAREN:
            return None

        identifier = self.current_token().value
        symbol_table_entry, _ = self.symbol_table.find(identifier)
        if symbol_table_entry is None:
            raise IdentifierError(f"Undefined identifier: {identifier}")
        if symbol_table_entry.entry_type != EntryType.ROUTINE:
            return None
        if self.parsing_param_decl:
            raise SyntaxError("A function call may not be used as a parameter.")
        self.advance()  # routine name
        self.advance()  # (
        routine = cast(ast.Routine, symbol_table_entry.node)
        params = self.parse_params(routine)
        self.consume(TokenType.OP_RPAREN)
        return ast.Call(identifier, params, routine.return_t)

    def parse_params(self, routine: ast.Routine) -> list[ast.Expr]:
        """
        <params> ::= <params>,<arith exp> | <arith exp>
        """
        param_exprs: list[ast.Expr] = []
        expected_param_count = len(routine.params)
        param_count = 0
        try:
            self.parsing_param_decl = True
            while self.current_token().tok_type != TokenType.OP_RPAREN:
                param_expr = self.parse_arith_exp()
                param_exprs.append(param_expr)
                param_count += 1
                if self.current_token().tok_type == TokenType.OP_COMMA:
                    self.advance()
                else:
                    break
            if param_count < expected_param_count:
                self.warn(
                    f"Too few parameters, expected {expected_param_count}, got {param_count}, filling in remainder with zeros"
                )
                while param_count < expected_param_count:
                    param_exprs.append(ast.NumericalConst(0))
                    param_count += 1
            elif self.current_token().tok_type == TokenType.OP_COMMA:
                raise SyntaxError(
                    f"Too many parameters, expected {expected_param_count}"
                )
            return param_exprs
        finally:
            self.parsing_param_decl = False

    def parse_cond_exp(self) -> ast.Expr:
        """
        <cond exp> ::= <complex rel>

        Note: This was not in the Action! manual but it seems complex_rel and arith_exp are synonymous.
        Also worth noting, the grammar rules in the manual show that an expression like
        "1" is not a valid conditional expression. But in practice, the Action!
        compiler cartridge allows it, e.g. "IF 1 THEN do_something() FI" compiles and
        runs as might be expected, treating nonzero values as true and zero as false
        """
        expr = self.parse_expression()
        if expr is None:
            raise SyntaxError("Expected conditional expression")
        return expr

    def parse_arith_exp(self) -> ast.Expr:
        """
        Parse an expression and verify it is not conditional
        """
        expr = self.parse_expression()
        if expr is None:
            raise SyntaxError("Expected arithmetic expression")
        # Get the operation of the expression if it's a binary operation
        if isinstance(expr, ast.BinaryExpr):
            binary_expr = cast(ast.BinaryExpr, expr)
            if binary_expr.op.is_conditional():
                raise SyntaxError("Conditional expression not allowed here")
        return expr

    def parse_struc_stmt(self) -> ast.Statement | None:
        """
        <struc stmt> ::= <IF stmt> | <DO loop> | <WHILE loop> | <FOR loop>
        """
        if_stmt = self.parse_if_stmt()
        if if_stmt:
            return if_stmt
        do_loop = self.parse_do_loop()
        if do_loop:
            return do_loop
        while_loop = self.parse_while_loop()
        if while_loop:
            return while_loop
        for_loop = self.parse_for_loop()
        if for_loop:
            return for_loop
        return None

    def parse_if_stmt(self) -> ast.If | None:
        """
        <IF stmt> ::= IF <cond exp> THEN {stmt list} {|:ELSEIF exten:|}{ELSE exten} FI
        """
        if self.current_token().tok_type != TokenType.IF:
            return None

        conditionals: list[ast.Conditional] = []
        self.advance()
        cond_expr = self.parse_cond_exp()
        self.consume(TokenType.THEN)
        statements = self.parse_stmt_list()
        conditional = ast.Conditional(cond_expr, statements)
        conditionals.append(conditional)

        while self.current_token().tok_type == TokenType.ELSEIF:
            self.advance()
            cond_expr = self.parse_cond_exp()
            self.consume(TokenType.THEN)
            statements = self.parse_stmt_list()
            conditional = ast.Conditional(cond_expr, statements)
            conditionals.append(conditional)

        else_statements: list[ast.Statement] | None = None
        if self.current_token().tok_type == TokenType.ELSE:
            self.advance()
            else_statements = self.parse_stmt_list()

        self.consume(TokenType.FI)
        return ast.If(conditionals, else_statements)

    def parse_do_loop(self) -> ast.Do | None:
        """
        <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
        <UNTIL stmt> ::= UNTIL <cond exp>
        """
        if self.current_token().tok_type != TokenType.DO:
            return None
        self.advance()
        statements = self.parse_stmt_list()
        until_expr = None
        if self.current_token().tok_type == TokenType.UNTIL:
            self.advance()
            until_expr = self.parse_cond_exp()
        self.consume(TokenType.OD)
        return ast.Do(statements, until_expr)

    def parse_while_loop(self) -> ast.While | None:
        """
        <WHILE loop> ::= WHILE <cond exp> <DO loop>
        <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
        <UNTIL stmt> ::= UNTIL <cond exp>

        Note: Yes,  WHILE loop can also have an UNTIL statement
        """
        if self.current_token().tok_type != TokenType.WHILE:
            return None
        self.advance()
        cond_expr = self.parse_cond_exp()
        do_loop = self.parse_do_loop()
        if do_loop is None:
            raise SyntaxError("Expected DO loop after WHILE")
        return ast.While(cond_expr, do_loop)

    def parse_for_loop(self) -> ast.For | None:
        """
        <FOR loop> ::= FOR <identifier>=<start> TO <finish> {STEP <inc>}<DO loop>
        <start> ::= <arith exp>
        <finish> ::= <arith exp>
        <inc> ::= <arith exp>
        """
        if self.current_token().tok_type != TokenType.FOR:
            return None
        self.advance()
        identifier = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.OP_EQ)
        start_expr = self.parse_arith_exp()
        self.consume(TokenType.TO)
        finish_expr = self.parse_arith_exp()
        inc_expr = None
        if self.current_token().tok_type == TokenType.STEP:
            self.advance()
            inc_expr = self.parse_arith_exp()
        else:
            inc_expr = ast.NumericalConst(1)
        do_loop = self.parse_do_loop()
        if do_loop is None:
            raise SyntaxError("Expected DO loop after FOR")
        # Need the type of the identifier.
        symbol_table_entry, _ = self.symbol_table.find(identifier)
        if symbol_table_entry is None:
            raise IdentifierError(f"Undefined identifier: {identifier}")
        if symbol_table_entry.entry_type != EntryType.VAR:
            raise IdentifierError(f"Expected variable identifier: {identifier}")
        var_decl = cast(ast.VarDecl, symbol_table_entry.node)
        var_target = ast.Var(identifier, var_decl.var_t)
        return ast.For(var_target, start_expr, finish_expr, inc_expr, do_loop)

    def parse_code_block(self) -> ast.CodeBlock | None:
        """
        <code block> ::= [<comp const list>]
        """
        if self.current_token().tok_type != TokenType.OP_LBRACK:
            return None
        self.advance()
        comp_consts = self.parse_comp_const_list()
        self.consume(TokenType.OP_RBRACK)
        return ast.CodeBlock(comp_consts)

    def parse_comp_const_list(self) -> list[int]:
        """
        <comp const list> ::= <comp const list> <comp const> | <comp const>
        """
        comp_consts: list[int] = []
        while True:
            comp_const = self.parse_comp_const()
            if comp_const is None:
                break
            comp_consts.append(comp_const)
        return comp_consts

    def parse_expression(self) -> ast.Expr | None:  # , is_inner_expression=False):
        """
        Expression parsing uses the Pratt method.
        """
        return self.parse_expr_precedence(ExprPrecedence.XOR)

    def parse_expr_precedence(self, precedence: ExprPrecedence) -> ast.Expr | None:
        if self.current_token().tok_type not in EXPRESSION_RULES:
            return None
        prefix = EXPRESSION_RULES[self.current_token().tok_type].prefix
        if prefix == ExprAction.NONE:
            raise SyntaxError(f"Expected prefix expression: {self.current_token()}")
        curr_expr = self.parse_expr_action(prefix)

        if self.current_token().tok_type in EXPRESSION_RULES:
            while (
                precedence.value
                <= EXPRESSION_RULES[self.current_token().tok_type].precedence.value
            ):
                curr_expr = self.parse_expr_action(
                    EXPRESSION_RULES[self.current_token().tok_type].infix,
                    curr_expr,
                )
                if self.current_token().tok_type not in EXPRESSION_RULES:
                    break

        return curr_expr

    def parse_expr_action(
        self, action: ExprAction, left_operand: ast.Expr | None = None
    ) -> ast.Expr:
        """
        Dispatch to the appropriate expression parsing method based on the action
        """
        if action == ExprAction.NUMERIC_LITERAL:
            return self.parse_numeric_literal()
        elif action == ExprAction.GROUPING:
            return self.parse_grouping()
        elif action == ExprAction.UNARY:
            return self.parse_unary()
        elif action == ExprAction.BINARY:
            if left_operand is None:
                raise InternalError("Expected left operand for binary expression")
            return self.parse_binary(left_operand)
        elif action == ExprAction.IDENTIFIER:
            return self.parse_identifier_expr()
        else:
            raise InternalError(f"Unknown expression action: {action}")

    def parse_numeric_literal(self) -> ast.Expr:
        """
        Action method for parsing a numeric literal
        """
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
        return ast.NumericalConst(value)

    def parse_grouping(self) -> ast.Expr:
        """
        Action method for parsing a grouping
        """
        self.advance()
        expr = self.parse_expression()
        if expr is None:
            raise SyntaxError("Expected expression inside parentheses")
        self.consume(TokenType.OP_RPAREN)
        return expr

    def parse_unary(self) -> ast.Expr:
        """
        Action method for parsing a unary operator
        """
        operator_type = self.current_token().tok_type
        self.advance()
        operand = self.parse_expr_precedence(ExprPrecedence.UNARY)
        if operand is None:
            raise SyntaxError("Expected operand for unary operator {operator_type}")
        if operator_type == TokenType.OP_MINUS:
            expr = ast.UnaryExpr(ast.Op.SUB, operand)
            # self.code_gen.emit_unary_minus()
        else:
            raise SyntaxError(f"Unknown unary operator: {operator_type}")
        return expr

    def parse_binary(self, left_operand: ast.Expr) -> ast.Expr:
        """
        Action method for parsing a binary operator
        """
        operator_type = self.current_token().tok_type
        self.advance()
        rule = EXPRESSION_RULES[operator_type]
        right_operand = self.parse_expr_precedence(
            ExprPrecedence(rule.precedence.value + 1)
        )
        if right_operand is None:
            raise SyntaxError(f"Expected right operand for {operator_type}")
        op = OP_MAP.get(operator_type)
        if op is None:
            raise SyntaxError(f"Unknown binary operator: {operator_type}")
        return ast.BinaryExpr(op, left_operand, right_operand)

    def parse_identifier_expr(self) -> ast.Expr:
        """
        Action method for parsing an identifier in an expression

        An identifier in an expression might be a variable or a function call
        """
        is_reference = False
        is_pointer = False
        if self.current_token().tok_type == TokenType.OP_AT:
            is_reference = True
            self.advance()
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            raise SyntaxError(
                f"Expected identifier in expression: {self.current_token()}"
            )
        identifier = self.current_token().value
        symbol_table_entry, _ = self.symbol_table.find(identifier)
        if symbol_table_entry is None:
            raise IdentifierError(f"Undefined identifier: {identifier}")
        elif symbol_table_entry.entry_type == EntryType.VAR:
            self.advance()
            if self.current_token().tok_type == TokenType.OP_CARET:
                is_pointer = True
                self.advance()
            var_decl = cast(ast.VarDecl, symbol_table_entry.node)
            var_node = ast.Var(identifier, var_decl.var_t)
            if is_pointer:
                if not isinstance(var_decl.var_t, PointerType):
                    raise SyntaxError(f"Variable {identifier} is not a pointer")
                return ast.Dereference(var_node)
            if is_reference:
                return ast.Reference(var_node)
            if isinstance(var_decl.var_t, ArrayType):
                if self.current_token().tok_type == TokenType.OP_LPAREN:
                    self.advance()
                    index_expr = self.parse_arith_exp()
                    self.consume(TokenType.OP_RPAREN)
                    return ast.ArrayAccess(var_node, index_expr)
                else:
                    return ast.Reference(var_node)
            return var_node
        elif symbol_table_entry.entry_type == EntryType.ROUTINE:
            routine_call = self.parse_routine_call()
            if routine_call is None:
                raise InternalError(f"Failed to parse routine call for {identifier}")
            return routine_call
        else:
            raise IdentifierError(f"Invalid identifier in expression: {identifier}")

    def parse_mem_reference(self):
        """
        Memory References

        <mem reference> ::= <mem contents> | @<identifier>
        <mem contents> ::= <fund ref> | <arr ref> | <ptr ref> | <rec ref>
        <fund ref> ::= <identifier>
        <arr ref> ::= <identifier>(<arith exp>)
        <ptr ref> ::= <identifier>^
        <rec ref> ::= <identifier>.<identifier>
        """
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
