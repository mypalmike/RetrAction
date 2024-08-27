from enum import Enum, auto
import sys

from retraction.pratt import EXPRESSION_RULES, ExprAction, ExprPrecedence
from retraction.tokens import Token, TokenType
from retraction.codegen import ByteCodeGen
from retraction.bytecode import (
    ByteCodeOp,
    ByteCodeVariableAddressMode,
    ByteCodeVariableScope,
)
from retraction.error import InternalError, SyntaxError
from retraction.symtab import SymbolTable
from retraction.typedexpr import (
    TypedExpressionItem,
    TypedExpressionOp,
    TypedPostfixExpression,
)
from retraction.types import Type, Routine, RecordType, binary_expression_type


class Parser:
    """
    This is primarily a recursive descent parser, but expressions are parsed using
    the Pratt method for handling operator precedence.
    """

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
            raise SyntaxError(f"Expected token {token_type}, got {token}")
        return self.advance()

    def parse_dev(self):
        self.parse_expression()

    #
    def parse_program(self):
        """
        <program> ::= <program> MODULE <prog module> | {MODULE} <prog module>
        """
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

    def parse_prog_module(self):
        """
        <prog module> ::= {<system decls>} <routine list>
        """
        self.parse_system_decls()
        self.parse_routine_list()

    def parse_system_decls(self) -> bool:
        """
        <system decls> ::= <DEFINE decl> | <TYPE decl> | <var decl>

        This grammar rule should probably be a list of system decls, but the Action!
        manual seems to be wrong here.
        """
        result = False
        while self.parse_system_decl():
            result = True
        return result

    def parse_system_decl(self) -> bool:
        """
        Parse a single system decl
        """
        if self.parse_define_decl():
            return True
        if self.parse_type_decl():
            return True
        if self.parse_var_decl():
            return True
        return False

    def parse_define_decl(self) -> bool:
        """
        <DEFINE decl> ::= <DEFINE> <def list>
        TODO: Remove this when there's a preprocessing step to handle defines
        """
        if self.current_token().tok_type != TokenType.DEFINE:
            return False
        self.advance()
        self.parse_def_list()
        return True

    def parse_def_list(self) -> bool:
        """
        <def list> ::= <def list>,<def> | <def>
        TODO: Remove this when there's a preprocessing step to handle defines
        """
        if not self.parse_def():
            return False
        while self.current_token().tok_type == TokenType.COMMA:
            self.advance()
            self.parse_def()
        return True

    def parse_def(self) -> bool:
        """
        <def> ::= <identifier>=<str const>
        TODO: Remove this when there's a preprocessing step to handle defines
        """
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

    def parse_type_decl(self) -> bool:
        """
        <TYPE decl> ::= TYPE <rec ident list>
        """
        if self.current_token().tok_type != TokenType.TYPE:
            return False
        self.advance()
        self.parse_rec_ident_list()
        return True

    def parse_rec_ident_list(self) -> bool:
        """
        <rec ident list> ::= <rec ident list> <rec ident> | <rec ident>
        """
        if not self.parse_rec_ident():
            return False
        while self.parse_rec_ident():
            pass
        return True

    def parse_rec_ident(self) -> bool:
        """
        <rec ident> ::= <rec name>=[<field init>]
        """
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

    def parse_field_init(self) -> bool:
        """
        <field init> ::= <fund var decl>
        """
        return self.parse_fund_var_decl()

    def parse_var_decl(self) -> bool:
        """
        <var decl> ::= <var decl> <base var decl> | <base var decl>
        """
        if not self.parse_base_var_decl():
            return False
        while self.parse_base_var_decl():
            pass
        return True

    def parse_base_var_decl(self):
        """
        <base var decl> ::= <fund decl> | <POINTER decl> | <ARRAY decl> | <record decl>
        """
        if self.parse_fund_decl():
            return True
        if self.parse_pointer_decl():
            return True
        if self.parse_array_decl():
            return True
        if self.parse_record_decl():
            return True
        return False

    def parse_fund_decl(self) -> bool:
        """
        # Variable Declaration for Fundamental Data Types
        # <fund decl> ::= <fund decl> <base fund decl> | <base fund decl>
        """
        if not self.parse_base_fund_decl():
            return False
        while self.parse_base_fund_decl():
            pass
        return True

    def parse_base_fund_decl(self) -> bool:
        """
        <base fund decl> ::= <fund type> <fund ident list>
        """
        fund_type = self.parse_fund_type()
        if fund_type is None:
            return False
        self.parse_fund_ident_list(fund_type)
        return True

    def parse_fund_type(self) -> TokenType | None:
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
        fund_type = self.current_token().tok_type
        self.advance()
        return fund_type

    def parse_fund_ident_list(self, fund_type: TokenType) -> bool:
        """
        <fund ident list> ::= <fund ident list>,<fund ident> | <fund ident>
        """
        if not self.parse_fund_ident(fund_type):
            return False
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            self.parse_fund_ident(fund_type)
        return True

    def parse_fund_ident(self, fund_type: TokenType) -> bool:
        """
        <fund ident> ::= <identifier>{=<init opts>}
        """
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

    def parse_init_opts(self, fund_type: TokenType, identifier: str) -> bool:
        """
        <init opts> ::= <addr> | [<value>]
        <addr> ::= <comp const>
        <value> ::= <num const>
        <num const> ::= <dec num> | <hex num> | <char>
        """
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

    def parse_pointer_decl(self) -> bool:
        """
        <POINTER decl> ::= <ptr type> POINTER <ptr ident list>
        """
        if not self.next_token():
            return False
        if self.next_token().tok_type != TokenType.POINTER:
            return False
        ptr_type = self.current_token().value
        self.advance()
        self.advance()
        self.parse_ptr_ident_list(ptr_type)

    def parse_ptr_ident_list(self, ptr_type: str) -> bool:
        """
        <ptr ident list> ::= <ptr ident list>,<ptr ident> | <ptr ident>
        """
        if not self.parse_ptr_ident(ptr_type):
            return False
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            self.parse_ptr_ident(ptr_type)
        return True

    def parse_ptr_ident(self, ptr_type) -> bool:
        """
        <ptr ident> ::= <identifier>{=<value>}
        """
        identifier = self.current_token().value
        self.consume(TokenType.IDENTIFIER)
        if self.current_token().tok_type == TokenType.OP_EQ:
            self.advance()
            value = self.parse_value_const()
            self.code_gen.emit_ptr_ident_value(ptr_type, identifier, value)
        else:
            self.code_gen.emit_ptr_ident(ptr_type, identifier)
        return True

    def parse_array_decl(self) -> bool:
        """
        # Variable Declaration for Arrays
        # TODO: Implement arrays

        # <ARRAY decl> ::= <fund type> ARRAY <arr ident list>
        # <arr ident list> ::= <arr ident list>,<arr ident> |
        # <arr ident>
        # <arr ident> ::= <identifier>{(<dim>)}{=<arr init opts>}
        # <dim> ::= <num conat>
        # <arr init opts> ::= <addr> | [<value>] | <str const>
        # <addr> ::= <comp const>
        # <value list> ::= <value list><value> | <value>
        # <value> ::= <comp const>
        """
        return False

    def parse_record_decl(self) -> bool:
        """
        Variable Declaration for Records
        --------------------------------
        <record decl> ::= <identifier> <rec ident list>
        <address> ::= <comp const>
        TODO: Probably need to refer to a symbol/type table to look up the record type to
        distinguish between record and array or other declarations
        """
        if self.current_token().tok_type != TokenType.IDENTIFIER:
            return False
        # Make sure it's a record.
        record_type_index = self.symbol_table.record_types_lookup.get(
            self.current_token().value
        )
        if record_type_index is None:
            return False
        rec_type = self.current_token().value
        self.advance()
        return self.parse_rec_ident_list(rec_type)

    def parse_rec_ident_list(self, rec_type: str) -> bool:
        """
        <rec ident list> ::= <rec ident list>,<rec ident> | <rec ident>
        """
        if not self.parse_rec_ident(rec_type):
            return False
        while self.current_token().tok_type == TokenType.OP_COMMA:
            self.advance()
            self.parse_rec_ident(rec_type)

    def parse_rec_ident(self, rec_type: str) -> bool:
        """
        <rec ident> ::= <identifier>{=<address>}
        """
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

    def parse_routine_list(self):
        """
        <routine list> ::= <routine list> <routine> | <routine>
        """
        while self.parse_routine():
            pass

    def parse_routine(self) -> bool:
        """
        <routine> ::= <proc routine> | <func routine>
        """
        if self.parse_proc_routine():
            return True
        if self.parse_func_routine():
            return True
        return False

    def parse_proc_routine(self) -> bool:
        """
        <proc routine> ::= <PROC decl> {<system decls>} {<stmt list>}{RETURN}
        <proc decl> ::= PROC <identifier>{=<addr>}({<param decl>})

        The RETURN token is optional because it's desirable to be able to fall through
        to the next routine on a 6502.
        """
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
        return True

    def parse_addr(self):
        """
        <addr> ::= <comp const>
        """
        return self.parse_comp_const()

    def parse_func_routine(self) -> bool:
        """
        <func routine> ::= <FUNC decl> {<system decls>} {<stmt list>}{RETURN (<arith exp>)}
        """
        if not self.parse_func_decl():
            return False
        self.parse_system_decls()
        self.parse_stmt_list()
        return True

    def parse_func_decl(self) -> bool:
        """
        <FUNC decl> ::= <fund type> FUNC <identifier>{.<addr>} ({<param decl>})
        """
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

    def parse_param_decl(self) -> bool:
        """
        <param decl> ::= <var decl>
        TODO: Implement limit of 8 parameters
        """
        return self.parse_var_decl()

    def parse_stmt_list(self) -> bool:
        """
        <stmt list> ::= <stmt list> <stmt> | <stmt>
        """
        while True:
            if not self.parse_stmt():
                break

    def parse_stmt(self) -> bool:
        """
        <stmt> ::= <simp stmt> | <struc stmt> | <code block>
        """
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

    def parse_simp_stmt(self) -> bool:
        """
        <simp stmt> ::= <assign stmt> | <EXIT stmt> | <routine call>
        """
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
        """
        Debugging tool.
        TODO: Remove this when no longer needed
        """
        if self.current_token().tok_type != TokenType.DEVPRINT:
            return False
        self.advance()
        self.consume(TokenType.OP_LPAREN)
        self.parse_arith_exp()
        self.consume(TokenType.OP_RPAREN)
        self.code_gen.emit_devprint(self.last_t)
        return True

    def parse_assign_stmt(self) -> bool:
        """
        <assign stmt> ::= <mem contents>=<arith exp>
        <mem contents> ::= <fund ref> | <arr ref> | <ptr ref> | <rec ref>
        <fund ref> ::= <identifier>
        <arr ref> ::= <identifier>(<arith exp>)
        <ptr ref> ::= <identifier>^
        <rec ref> ::= <identifier>.<identifier>
        """
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

    def parse_exit_stmt(self) -> bool:
        """
        Equivalent to break statement in most languages.
        <EXIT stmt> ::= EXIT
        """
        if self.current_token().tok_type != TokenType.EXIT:
            return False
        self.advance()
        if len(self.exits_to_patch) == 0:
            raise SyntaxError("EXIT statement outside of loop")
        # This gets patched at the end of the loop with the address following the loop
        jump_exit = self.code_gen.emit_jump()
        self.exits_to_patch[-1].append(jump_exit)
        return True

    def parse_return_stmt(self) -> bool:
        """
        <RETURN stmt> ::= RETURN | RETURN (<arith exp>) - depending on PROC or FUNC
        """
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

    def parse_routine_call(self) -> bool:
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

    def parse_params(self, routine_index: int):
        """
        <params> ::= <params>,<arith exp> | <arith exp>
        """
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

    def parse_cond_exp(self) -> bool:
        """
        <cond exp> ::= <complex rel>

        Note: This was not in the Action! manual but it seems complex_rel and arith_exp are synonymous.
        Also worth noting, the grammar rules in the manual show that an expression like
        "1" is not a valid conditional expression. But in practice, the Action!
        compiler cartridge allows it, e.g. "IF 1 THEN do_something() FI" compiles and
        runs as expected, treating nonzero values as true and zero as false
        """
        return self.parse_expression()

    def parse_arith_exp(self) -> bool:
        """
        TODO: Get rid of this indirection?
        """
        return self.parse_expression()

    def parse_struc_stmt(self) -> bool:
        """
        <struc stmt> ::= <IF stmt> | <DO loop> | <WHILE loop> | <FOR loop>
        """
        if self.parse_if_stmt():
            return True
        if self.parse_do_loop():
            return True
        if self.parse_while_loop():
            return True
        if self.parse_for_loop():
            return True
        return False

    def parse_if_stmt(self) -> bool:
        """
        <IF stmt> ::= IF <cond exp> THEN {stmt list} {|:ELSEIF exten:|}{ELSE exten} FI
        """
        if self.current_token().tok_type != TokenType.IF:
            return False
        jump_end_addrs: list[int] = []

        # If
        self.advance()
        self.parse_cond_exp()
        self.consume(TokenType.THEN)
        jump_over_addr = self.code_gen.emit_jump_if_false(self.last_t)
        self.parse_stmt_list()
        jump_end_addrs.append(self.code_gen.emit_jump())
        self.code_gen.fixup_jump(jump_over_addr, self.code_gen.get_next_addr())

        # Elseif
        while self.current_token().tok_type == TokenType.ELSEIF:
            self.advance()
            self.parse_cond_exp()
            self.consume(TokenType.THEN)
            jump_over_addr = self.code_gen.emit_jump_if_false(self.last_t)
            self.parse_stmt_list()
            jump_end_addrs.append(self.code_gen.emit_jump())
            self.code_gen.fixup_jump(jump_over_addr, self.code_gen.get_next_addr())

        # Else
        if self.current_token().tok_type == TokenType.ELSE:
            self.advance()
            self.parse_stmt_list()

        # Fi
        self.consume(TokenType.FI)
        end_addr = self.code_gen.get_next_addr()
        for jump_end_addr in jump_end_addrs:
            self.code_gen.fixup_jump(jump_end_addr, end_addr)

        return True

    def prepare_exits(self):
        """
        Helper method to set up exit patching
        """
        self.exits_to_patch.append([])

    def patch_exits(self):
        """
        Helper method for patching exits at the end of loops
        """
        exits_to_patch = self.exits_to_patch.pop()
        if exits_to_patch:
            next_addr = self.code_gen.get_next_addr()
            for jump_exit in exits_to_patch:
                jump_exit.value = next_addr

    def parse_do_loop(self) -> bool:
        """
        <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
        <UNTIL stmt> ::= UNTIL <cond exp>
        """
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

    def parse_while_loop(self) -> bool:
        """
        <WHILE loop> ::= WHILE <cond exp> <DO loop>
        <DO loop> ::= DO {<stmt list>} {<UNTIL stmt>} OD
        <UNTIL stmt> ::= UNTIL <cond exp>

        Note: Yes,  WHILE loop can also have an UNTIL statement
        """
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

    def parse_for_loop(self) -> bool:
        """
        <FOR loop> ::= FOR <identifier>=<start> TO <finish> {STEP <inc>}<DO loop>
        <start> ::= <arith exp>
        <finish> ::= <arith exp>
        <inc> ::= <arith exp>
        """
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

    def parse_code_block(self) -> bool:
        """
        <code block> ::= [<comp const list>]
        """
        if self.current_token().tok_type != TokenType.OP_LBRACK:
            return False
        self.advance()
        self.parse_comp_const_list()
        self.consume(TokenType.OP_RBRACK)
        return True

    def parse_comp_const_list(self) -> bool:
        """
        <comp const list> ::= <comp const list> <comp const> | <comp const>
        """
        while True:
            comp_const = self.parse_comp_const()
            if not comp_const:
                break
            self.code_gen.emit_comp_const(comp_const)
        return True

    def parse_expression(self, is_inner_expression=False):
        """
        Expression parsing uses the Pratt method.
        """
        if not is_inner_expression:
            self.typed_expression = TypedPostfixExpression(self.symbol_table)

        self.parse_expr_precedence(ExprPrecedence.XOR)
        # TODO: Run the optimization code here. Probably add a parser flag to enable this.
        # self.typed_expression.optimize()
        print("Typed expression:")
        for item in self.typed_expression.items:
            print(item)

        if not is_inner_expression:
            self.typed_expression.emit_bytecode(self.code_gen)
            self.last_t = self.typed_expression.items[-1].item_t

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
        """
        Dispatch to the appropriate expression parsing method based on the action
        """
        if action == ExprAction.NUMERIC_LITERAL:
            self.parse_numeric_literal()
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

    def parse_numeric_literal(self):
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
        const_index = self.symbol_table.declare_constant(value)
        typed_expression = TypedExpressionItem(TypedExpressionOp.CONSTANT, const_index)
        self.typed_expression.append(typed_expression)
        # self.code_gen.emit_numerical_constant(const_index)

    def parse_grouping(self):
        """
        Action method for parsing a grouping
        """
        self.advance()
        self.parse_expression(True)
        self.consume(TokenType.OP_RPAREN)

    def parse_unary(self):
        """
        Action method for parsing a unary operator
        """
        operator_type = self.current_token().tok_type
        self.parse_expr_precedence(ExprPrecedence.UNARY)
        if operator_type == TokenType.OP_MINUS:
            self.code_gen.emit_unary_minus()
        self.advance()

    def parse_binary(self):
        """
        Action method for parsing a binary operator
        """
        operator_type = self.current_token().tok_type
        self.advance()
        rule = EXPRESSION_RULES[operator_type]
        self.parse_expr_precedence(ExprPrecedence(rule.precedence.value + 1))

        if operator_type == TokenType.OP_PLUS:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.ADD))
        elif operator_type == TokenType.OP_MINUS:
            self.typed_expression.append(
                TypedExpressionItem(TypedExpressionOp.SUBTRACT)
            )
        elif operator_type == TokenType.OP_TIMES:
            self.typed_expression.append(
                TypedExpressionItem(TypedExpressionOp.MULTIPLY)
            )
        elif operator_type == TokenType.OP_DIVIDE:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.DIVIDE))
        elif operator_type == TokenType.MOD:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.MOD))
        elif operator_type == TokenType.LSH:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.LSH))
        elif operator_type == TokenType.RSH:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.RSH))
        elif operator_type == TokenType.OP_EQ:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.EQ))
        elif operator_type == TokenType.OP_NE:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.NE))
        elif operator_type == TokenType.OP_GT:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.GT))
        elif operator_type == TokenType.OP_GE:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.GE))
        elif operator_type == TokenType.OP_LT:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.LT))
        elif operator_type == TokenType.OP_LE:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.LE))
        elif operator_type == TokenType.XOR:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.XOR))
        elif operator_type == TokenType.OP_BIT_AND:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.BIT_AND))
        elif operator_type == TokenType.OP_BIT_OR:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.BIT_OR))
        elif operator_type == TokenType.OP_BIT_XOR:
            self.typed_expression.append(TypedExpressionItem(TypedExpressionOp.BIT_XOR))

    def parse_and(self):
        """
        Action method for parsing an AND operator

        AND is short-circuiting, so we don't treat it as a simple binary operator
        """
        jump_end = self.code_gen.emit_jump_if_false()
        self.code_gen.emit_pop()
        self.advance()
        self.parse_expr_precedence(ExprPrecedence.AND)
        jump_end.value = self.code_gen.get_next_addr()

    def parse_or(self):
        """
        Action method for parsing an OR operator

        OR is short-circuiting, so we don't treat it as a simple binary operator
        """
        jump_else = self.code_gen.emit_jump_if_false()
        jump_end = self.code_gen.emit_jump()
        jump_else.value = self.code_gen.get_next_addr()
        self.code_gen.emit_pop()
        self.advance()
        self.parse_expr_precedence(ExprPrecedence.OR)
        jump_end.value = self.code_gen.get_next_addr()

    def parse_identifier_expr(self):
        """
        Action method for parsing an identifier in an expression

        An identifier in an expression might be a variable or a function call
        """
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
