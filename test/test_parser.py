from retraction import Parser, Token, TokenType, tokenize
from retraction.codegen import CodeGenForTest
from retraction.symtab import SymTab
import unittest


class ParserTestCase(unittest.TestCase):
    def test_arith_expr_simple(self):
        source_code = "1 + 2 * 3"
        tokens = tokenize(source_code)
        directives = {}
        codegen = CodeGenForTest()
        symbol_table = SymTab()
        parser = Parser(tokens, directives, codegen, symbol_table)
        # parser.advance()
        parser.parse_expression()
        expected_code = [
            "NUMBER 1",
            "NUMBER 2",
            "NUMBER 3",
            "MULTIPLY",
            "ADD",
        ]
        self.assertEqual(codegen.code, expected_code)
        self.assertEqual(parser.current_token().type, TokenType.EOF)

    def test_arith_expr_parens(self):
        source_code = "(1 + 2) * (3 + $1A)"
        tokens = tokenize(source_code)
        directives = {}
        codegen = CodeGenForTest()
        symbol_table = SymTab()
        parser = Parser(tokens, directives, codegen, symbol_table)
        # parser.advance()
        parser.parse_expression()
        expected_code = [
            "NUMBER 1",
            "NUMBER 2",
            "ADD",
            "NUMBER 3",
            "NUMBER 26",
            "ADD",
            "MULTIPLY",
        ]
        self.assertEqual(codegen.code, expected_code)
        self.assertEqual(parser.current_token().type, TokenType.EOF)
