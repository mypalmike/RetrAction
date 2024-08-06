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
            self.assertEqual(symbol_table.constants[index], expected_const_values[i])

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
            self.assertEqual(symbol_table.constants[index], expected_const_values[i])

    def test_arith_expr_nums(self):
        source_code = "1 2 3"
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_expression()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),
        ]
        self.assertEqual(codegen.code, expected_code, "Should only parse first number")

    def test_if_stmt(self):
        source_code = """
        IF 1 < 3 THEN
            DEVPRINT (1)
        ELSEIF 2 < 3 THEN
            DEVPRINT (2)
        ELSE
            DEVPRINT (3)
        FI
        """
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_if_stmt()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),  # 1
            ByteCode(ByteCodeOp.CONSTANT, 1),  # 3
            ByteCode(ByteCodeOp.OP_LT),  # 1 < 3
            ByteCode(ByteCodeOp.JUMP_IF_FALSE, 7),  # Jump to ELSEIF
            ByteCode(ByteCodeOp.CONSTANT, 2),  # 1
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(1)
            ByteCode(ByteCodeOp.JUMP, 16),  # Jump to FI
            ByteCode(ByteCodeOp.CONSTANT, 3),  # 2
            ByteCode(ByteCodeOp.CONSTANT, 4),  # 3
            ByteCode(ByteCodeOp.OP_LT),  # 2 < 3
            ByteCode(ByteCodeOp.JUMP_IF_FALSE, 14),  # Jump to ELSE
            ByteCode(ByteCodeOp.CONSTANT, 5),  # 2
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(2)
            ByteCode(ByteCodeOp.JUMP, 16),  # Jump to FI
            ByteCode(ByteCodeOp.CONSTANT, 6),  # 3
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(3)
        ]
        for i, expected_bytecode in enumerate(expected_code):
            self.assertEqual(
                codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
            )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_if_stmt_int_cond(self):
        source_code = """
        IF 1 THEN
            DEVPRINT (1)
        FI
        """
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_if_stmt()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),  # 1
            ByteCode(ByteCodeOp.JUMP_IF_FALSE, 5),  # Jump to ELSE
            ByteCode(ByteCodeOp.CONSTANT, 1),  # 1
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(1)
            ByteCode(ByteCodeOp.JUMP, 5),  # Jump to FI
        ]
        for i, expected_bytecode in enumerate(expected_code):
            self.assertEqual(
                codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
            )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_do_loop(self):
        source_code = """
        DO
            DEVPRINT (1)
        UNTIL 2
        OD
        """
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_do_loop()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),  # 1
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(1)
            ByteCode(ByteCodeOp.CONSTANT, 1),  # 2
            ByteCode(ByteCodeOp.JUMP_IF_FALSE, 0),  # Jump to DO
        ]
        for i, expected_bytecode in enumerate(expected_code):
            self.assertEqual(
                codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
            )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_while_loop(self):
        source_code = """
        WHILE 1
        DO
            DEVPRINT (2)
        OD
        """
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_while_loop()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),  # 1
            ByteCode(ByteCodeOp.JUMP_IF_FALSE, 5),  # Jump to OD
            ByteCode(ByteCodeOp.CONSTANT, 1),  # 2
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(2)
            ByteCode(ByteCodeOp.JUMP, 0),  # Jump to WHILE
        ]
        for i, expected_bytecode in enumerate(expected_code):
            self.assertEqual(
                codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
            )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_exit_stmt(self):
        source_code = """
        WHILE 1
        DO
          IF 2 THEN
            DEVPRINT (3)
            EXIT
            DEVPRINT (4)
          FI
          DO
            DEVPRINT (5)
            DO
              DEVPRINT (6)
              EXIT
              DEVPRINT (7)
            OD
          OD
          EXIT
          DEVPRINT (8)
        OD
        """
        tokens = tokenize(source_code)
        directives = {}
        symbol_table = SymbolTable()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, directives, codegen, symbol_table)
        parser.parse_while_loop()
        expected_code = [
            ByteCode(ByteCodeOp.CONSTANT, 0),  # 1 [0]
            ByteCode(ByteCodeOp.JUMP_IF_FALSE, 23),  # Jump to OD [1]
            ByteCode(ByteCodeOp.CONSTANT, 1),  # 2 [2]
            ByteCode(ByteCodeOp.JUMP_IF_FALSE, 10),  # Jump to DO [3]
            ByteCode(ByteCodeOp.CONSTANT, 2),  # 3 [4]
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(3) [5]
            ByteCode(ByteCodeOp.JUMP, 23),  # Jump to OD [6]
            ByteCode(ByteCodeOp.CONSTANT, 3),  # 4 [7]
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(4) [8]
            ByteCode(ByteCodeOp.JUMP, 10),  # Jump to OD [9]
            ByteCode(ByteCodeOp.CONSTANT, 4),  # 5 [10]
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(5) [11]
            ByteCode(ByteCodeOp.CONSTANT, 5),  # 6 [12]
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(6) [13]
            ByteCode(ByteCodeOp.JUMP, 18),  # Jump to OD [14]
            ByteCode(ByteCodeOp.CONSTANT, 6),  # 7 [15]
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(7) [16]
            ByteCode(ByteCodeOp.JUMP, 12),  # Jump to OD [17]
            ByteCode(ByteCodeOp.JUMP, 10),  # Jump to OD [18]
            ByteCode(ByteCodeOp.JUMP, 23),  # 8 [19]
            ByteCode(ByteCodeOp.CONSTANT, 7),  # 9 [20]
            ByteCode(ByteCodeOp.OP_DEVPRINT),  # DEVPRINT(8) [21]
            ByteCode(ByteCodeOp.JUMP, 0),  # Jump to WHILE [22]
        ]
        for i, expected_bytecode in enumerate(expected_code):
            self.assertEqual(
                codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
            )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

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
        for name, type, value in [
            ("somebyte", BYTE_TIPE, 0),
            ("somecard", CARD_TIPE, 0),
            ("someint", INT_TIPE, 0),
        ]:
            self.assertTrue(symbol_table.symbol_exists(name))
            g_index = symbol_table.globals_lookup[name]
            g_name, g_type, g_value = symbol_table.globals[g_index]
            self.assertEqual(g_name, name)
            self.assertEqual(g_type, type)
            self.assertEqual(g_value, value)
