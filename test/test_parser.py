import unittest

from retraction import Parser, Token, TokenType, tokenize
from retraction.bytecode import ByteCode, ByteCodeOp
from retraction.codegen import ByteCodeGen
from retraction.symtab import SymbolTable
from retraction.tipes import BYTE_TIPE, CARD_TIPE, INT_TIPE


class ParserTestCase(unittest.TestCase):
    def test_arith_expr_simple(self):
        source_code = "1 + 2 * 3"
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_expression()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),
            ByteCode(ByteCodeOp.CONSTANT, 1),
            ByteCode(ByteCodeOp.CONSTANT, 2),
            ByteCode(ByteCodeOp.MULTIPLY),
            ByteCode(ByteCodeOp.ADD),
        ]
        self.assertEqual(codegen.code, expected_code)
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)
        expected_const_indices = [
            b.value for b in expected_code if b.op == ByteCodeOp.CONSTANT
        ]
        expected_const_values = [1, 2, 3]
        for i, index in enumerate(expected_const_indices):
            self.assertEqual(symbol_table.constants[index][1], expected_const_values[i])

    def test_arith_expr_parens(self):
        source_code = "(1 + 2) * (3 + $1B)"
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_expression()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),
            ByteCode(ByteCodeOp.CONSTANT, 1),
            ByteCode(ByteCodeOp.ADD),
            ByteCode(ByteCodeOp.CONSTANT, 2),
            ByteCode(ByteCodeOp.CONSTANT, 3),
            ByteCode(ByteCodeOp.ADD),
            ByteCode(ByteCodeOp.MULTIPLY),
        ]
        self.assertEqual(codegen.code, expected_code)
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)
        expected_const_indices = [
            b.value for b in expected_code if b.op == ByteCodeOp.CONSTANT
        ]
        expected_const_values = [1, 2, 3, 0x1B]
        for i, index in enumerate(expected_const_indices):
            self.assertEqual(symbol_table.constants[index][1], expected_const_values[i])

    def test_system_decls(self):
        source_code = """
        BYTE somebyte
        CARD somecard
        INT someint
        """
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_system_decls()
        for name, type in [
            ("somebyte", BYTE_TIPE),
            ("somecard", CARD_TIPE),
            ("someint", INT_TIPE),
        ]:
            self.assertTrue(symbol_table.symbol_exists(name))
            g_index = symbol_table.globals_lookup[name]
            g_name, g_type = symbol_table.globals[g_index]
            self.assertEqual(g_name, name)
            self.assertEqual(g_type, type)
