from binascii import hexlify

from typing import cast
import unittest

from retraction import Parser, TokenType, tokenize
from retraction.bytecode import ByteCodeOp
from retraction.codegen import ByteCodeGen
from retraction.symtab import SymTab
from retraction.types import Type
import retraction.ast as ast


# Dummy source filename for tests
S_F = "<test>"


class ParserTestCase(unittest.TestCase):
    def assertEqualIgnoreWhitespace(self, a, b):
        # Replace tabs, newlines, and spaces with empty strings
        a = a.replace("\t", "").replace("\n", "").replace(" ", "")
        b = b.replace("\t", "").replace("\n", "").replace(" ", "")
        self.assertEqual(a, b)

    def test_arith_expr_numerical_constants(self):
        source_code = "33"
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_expression()
        self.assertIsInstance(tree, ast.NumericConst)
        const_node = cast(ast.NumericConst, tree)
        self.assertEqual(const_node.value, 33)
        self.assertEqual(str(const_node), "Const(33)")
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_arith_expr_simple(self):
        source_code = "23 + $45 * $678"
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_expression()
        self.assertEqual(
            str(tree),
            "BinaryExpr(Op.ADD, Const(23), BinaryExpr(Op.MUL, Const(69), Const(1656)))",
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_arith_expr_parens(self):
        source_code = "(87 + 65) * (43 + $1B)"
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_expression()
        self.assertEqual(
            str(tree),
            "BinaryExpr(Op.MUL, BinaryExpr(Op.ADD, Const(87), Const(65)), BinaryExpr(Op.ADD, Const(43), Const(27)))",
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_arith_expr_nums(self):
        source_code = "98 2 3"
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_expression()
        self.assertEqual(
            str(tree),
            "Const(98)",
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.INT_LITERAL)

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
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_if_stmt()
        self.assertEqual(
            str(tree),
            "If([Conditional(BinaryExpr(Op.LT, Const(1), Const(3)), [DevPrint(Const(1))]), Conditional(BinaryExpr(Op.LT, Const(2), Const(3)), [DevPrint(Const(2))])], [DevPrint(Const(3))])",
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_if_stmt_int_cond(self):
        source_code = """
        IF $23 THEN
            DEVPRINT (1)
        FI
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_if_stmt()
        self.assertEqual(
            str(tree),
            "If([Conditional(Const(35), [DevPrint(Const(1))])], None)",
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_do_loop(self):
        source_code = """
        DO
            DEVPRINT ($23)
        UNTIL 2
        OD
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_do_loop()
        self.assertEqual(
            str(tree),
            "Do([DevPrint(Const(35))], Const(2))",
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_while_loop(self):
        source_code = """
        WHILE 1
        DO
            DEVPRINT (2)
        OD
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_while_loop()
        self.assertEqual(
            str(tree),
            "While(Const(1), Do([DevPrint(Const(2))], None))",
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
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_while_loop()
        self.maxDiff = None
        self.assertEqualIgnoreWhitespace(
            str(tree),
            """
            While(
              Const(1),
              Do([
                If([Conditional(Const(2),[DevPrint(Const(3)),Exit(),DevPrint(Const(4))])],None),
                Do([DevPrint(Const(5)),Do([DevPrint(Const(6)),Exit(),DevPrint(Const(7))],None)],None),
                Exit(),
                DevPrint(Const(8))],
              None))
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_system_decls_basic(self):
        source_code = """
        BYTE somebyte = [$12]
        CARD somecard = [$2345]
        INT someint = [$6789]
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_system_decls()
        self.maxDiff = None
        self.assertEqualIgnoreWhitespace(
            str(tree),
            """
            [VarDecl(somebyte, FundamentalType.BYTE_T, InitOpts(18, False)),
            VarDecl(somecard, FundamentalType.CARD_T, InitOpts(9029, False)),
            VarDecl(someint, FundamentalType.INT_T, InitOpts(26505, False))]
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    # def test_simple_program(self):
    #     source_code = """
    #     BYTE somebyte = [$12]
    #     CARD somecard = [$2345]
    #     INT someint = [$6789]

    #     PROC main()
    #         DEVPRINT (somebyte)
    #     RETURN
    #     """
    #     tokens = tokenize(source_code, S_F)
    #     symbol_table = SymTab()
    #     parser = Parser(tokens, symbol_table)
    #     tree = parser.parse_program()
    #     self.maxDiff = None
    #     self.assertEqualIgnoreWhitespace(
    #         str(tree),
    #         """
    #         Program([Module([VarDecl(somebyte, FundamentalType.BYTE_T, InitOpts(18, False)),
    #         VarDecl(somecard, FundamentalType.CARD_T, InitOpts(9029, False)),
    #         VarDecl(someint, FundamentalType.INT_T, InitOpts(26505, False))],
    #         [Routine(main, [], [DevPrint(Const(1)), Return()])])])
    #         """,
    #     )
    #     self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    # def test_assignment(self):
    #     source_code = """
    #     BYTE somebyte
    #     BYTE otherbyte
    #     """
    #     # This test invokes two parsers to isolate the assignment parsing
    #     tokens = tokenize(source_code, S_F)
    #     symbol_table = SymbolTable()
    #     codegen = ByteCodeGen(symbol_table)
    #     parser = Parser(tokens, codegen, symbol_table)
    #     parser.parse_system_decls()

    #     source_code = """
    #     otherbyte = 1
    #     """
    #     tokens = tokenize(source_code, S_F)
    #     parser = Parser(tokens, codegen, symbol_table)
    #     parser.parse_assign_stmt()
    #     expected_code = [
    #         ByteCode(ByteCodeOp.NUMERICAL_CONSTANT, 0),  # 1
    #         ByteCode(ByteCodeOp.SET_GLOBAL, 1),  # otherbyte
    #     ]
    #     for i, expected_bytecode in enumerate(expected_code):
    #         self.assertEqual(
    #             codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
    #         )
    #     self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    # def test_global_get(self):
    #     source_code = """
    #     BYTE somebyte
    #     BYTE otherbyte
    #     """
    #     # This test invokes two parsers to isolate the assignment parsing
    #     tokens = tokenize(source_code, S_F)
    #     symbol_table = SymbolTable()
    #     codegen = ByteCodeGen(symbol_table)
    #     parser = Parser(tokens, codegen, symbol_table)
    #     parser.parse_system_decls()

    #     source_code = """
    #     DEVPRINT(otherbyte)
    #     """
    #     tokens = tokenize(source_code, S_F)
    #     parser = Parser(tokens, codegen, symbol_table)
    #     parser.parse_simp_stmt()
    #     expected_code = [
    #         ByteCode(ByteCodeOp.GET_GLOBAL, 1),  # otherbyte
    #         ByteCode(ByteCodeOp.DEVPRINT),
    #     ]
    #     for i, expected_bytecode in enumerate(expected_code):
    #         self.assertEqual(
    #             codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
    #         )
    #     self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    # def test_routine_basics(self):
    #     source_code = """
    #     PROC proc1()
    #         DEVPRINT(1)
    #     RETURN

    #     PROC proc2()
    #         proc1()
    #         DEVPRINT(2)

    #     PROC main()
    #         proc2()
    #     RETURN
    #     """
    #     tokens = tokenize(source_code, S_F)
    #     symbol_table = SymbolTable()
    #     codegen = ByteCodeGen(symbol_table)
    #     parser = Parser(tokens, codegen, symbol_table)
    #     parser.parse_program()
    #     expected_code = [
    #         ByteCode(ByteCodeOp.NUMERICAL_CONSTANT, 0),  # 1
    #         ByteCode(ByteCodeOp.DEVPRINT),  # DEVPRINT(1)
    #         ByteCode(ByteCodeOp.RETURN),
    #         ByteCode(ByteCodeOp.ROUTINE_CALL, 0),  # proc1
    #         ByteCode(ByteCodeOp.NUMERICAL_CONSTANT, 1),  # 2
    #         ByteCode(ByteCodeOp.DEVPRINT),  # DEVPRINT(2)
    #         ByteCode(ByteCodeOp.ROUTINE_CALL, 1),  # proc2
    #         ByteCode(ByteCodeOp.RETURN),
    #     ]
    #     # Check that the symbol table has the correct routine indices
    #     for name, index in [("proc1", 0), ("proc2", 1), ("main", 2)]:
    #         self.assertTrue(
    #             symbol_table.symbol_exists(name), f"Symbol {name} not found"
    #         )
    #         routine_index = symbol_table.routines_lookup[name]
    #         self.assertEqual(routine_index, index, f"Routine index mismatch for {name}")
    #     # Check that the codegen output matches the expected code
    #     for i, expected_bytecode in enumerate(expected_code):
    #         self.assertLess(i, len(codegen.code), f"Codegen index {i} out of range")
    #         self.assertEqual(
    #             codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
    #         )
    #     self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    # def test_global_assign_and_read(self):
    #     source_code = """
    #     BYTE somebyte
    #     BYTE otherbyte

    #     PROC main()
    #         somebyte = 10
    #         otherbyte = somebyte + 36
    #         DEVPRINT(otherbyte)
    #     RETURN
    #     """
    #     tokens = tokenize(source_code, S_F)
    #     symbol_table = SymbolTable()
    #     codegen = ByteCodeGen(symbol_table)
    #     parser = Parser(tokens, codegen, symbol_table)
    #     parser.parse_program()
    #     print(codegen.code)
    #     print(symbol_table.constants)
    #     print(symbol_table.globals)
    #     expected_code = [
    #         ByteCode(ByteCodeOp.NUMERICAL_CONSTANT, 0),  # 10
    #         ByteCode(ByteCodeOp.SET_GLOBAL, 0),  # somebyte
    #         ByteCode(ByteCodeOp.GET_GLOBAL, 0),  # somebyte
    #         ByteCode(ByteCodeOp.NUMERICAL_CONSTANT, 1),  # 36
    #         ByteCode(ByteCodeOp.ADD),
    #         ByteCode(ByteCodeOp.SET_GLOBAL, 1),  # otherbyte
    #         ByteCode(ByteCodeOp.GET_GLOBAL, 1),  # otherbyte
    #         ByteCode(ByteCodeOp.DEVPRINT),
    #         ByteCode(ByteCodeOp.RETURN),
    #     ]
    #     # Check that the symbol table has the correct global indices
    #     for name, index in [("somebyte", 0), ("otherbyte", 1)]:
    #         self.assertTrue(
    #             symbol_table.symbol_exists(name), f"Symbol {name} not found"
    #         )
    #         global_index = symbol_table.globals_lookup[name]
    #         self.assertEqual(global_index, index, f"Global index mismatch for {name}")

    #     # Check that the symbol table has the correct constant values
    #     for i, value in enumerate([10, 36]):
    #         self.assertEqual(
    #             symbol_table.constants[i],
    #             value,
    #             f"Constant value mismatch at index {i}",
    #         )

    #     # Check that the codegen output matches the expected code
    #     for i, expected_bytecode in enumerate(expected_code):
    #         self.assertLess(i, len(codegen.code), f"Codegen index {i} out of range")
    #         self.assertEqual(
    #             codegen.code[i], expected_bytecode, f"Bytecode mismatch at index {i}"
    #         )
    #     self.assertEqual(parser.current_token().tok_type, TokenType.EOF)
