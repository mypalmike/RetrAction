from binascii import hexlify

from typing import cast
import unittest

from retraction import Parser, TokenType, tokenize
from retraction.bytecode import ByteCodeOp
from retraction.codegen import ByteCodeGen
from retraction.symtab import EntryType, SymTab
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
            [VarDecl(somebyte,FundamentalType.BYTE_T,InitOpts([18],False)),
            VarDecl(somecard,FundamentalType.CARD_T,InitOpts([9029],False)),
            VarDecl(someint,FundamentalType.INT_T,InitOpts([26505],False))]
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_system_decls_all_internal_types(self):
        source_code = """
        BYTE somebyte = [$12]
        CHAR somechar = ['a]
        CARD somecard = [$2345]
        INT someint = [$6789]
        BYTE POINTER someptr
        CHAR POINTER somecharptr
        CARD POINTER somecardptr
        INT POINTER someintptr
        BYTE POINTER someptrinit = $1000
        BYTE ARRAY somebytearr
        CHAR ARRAY somechararr
        CARD ARRAY somecardarr
        INT ARRAY someintarr
        BYTE ARRAY somebytearrinit(3) = [$12 $34 $56]
        CHAR ARRAY somechararrinit = ['a 'b 'c]
        CHAR ARRAY somechararrinit2 = "abc"
        """
        tokens = tokenize(source_code, S_F)
        print(tokens)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_system_decls()
        self.maxDiff = None
        self.assertEqualIgnoreWhitespace(
            str(tree),
            """
            [VarDecl(somebyte,FundamentalType.BYTE_T,InitOpts([18],False)),
            VarDecl(somechar,FundamentalType.CHAR_T,InitOpts([97],False)),
            VarDecl(somecard,FundamentalType.CARD_T,InitOpts([9029],False)),
            VarDecl(someint,FundamentalType.INT_T,InitOpts([26505],False)),
            VarDecl(someptr,PointerType(FundamentalType.BYTE_T),None),
            VarDecl(somecharptr,PointerType(FundamentalType.CHAR_T),None),
            VarDecl(somecardptr,PointerType(FundamentalType.CARD_T),None),
            VarDecl(someintptr,PointerType(FundamentalType.INT_T),None),
            VarDecl(someptrinit,PointerType(FundamentalType.BYTE_T),InitOpts([4096],False)),
            VarDecl(somebytearr,ArrayType(FundamentalType.BYTE_T,None),None),
            VarDecl(somechararr,ArrayType(FundamentalType.CHAR_T,None),None),
            VarDecl(somecardarr,ArrayType(FundamentalType.CARD_T,None),None),
            VarDecl(someintarr,ArrayType(FundamentalType.INT_T,None),None),
            VarDecl(somebytearrinit,ArrayType(FundamentalType.BYTE_T,3),InitOpts([18,52,86],False)),
            VarDecl(somechararrinit,ArrayType(FundamentalType.CHAR_T,None),InitOpts([97,98,99],False)),
            VarDecl(somechararrinit2,ArrayType(FundamentalType.CHAR_T,None),InitOpts([97,98,99],False))]
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_type_decl(self):
        source_code = """
        TYPE rectype = [
            BYTE field1, field2
            CARD field3
            INT field4
        ]
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_type_decl()
        self.maxDiff = None
        self.assertEqualIgnoreWhitespace(
            str(tree),
            """
            StructDecl(rectype,
            [VarDecl(field1,FundamentalType.BYTE_T,None),
            VarDecl(field2,FundamentalType.BYTE_T,None),
            VarDecl(field3,FundamentalType.CARD_T,None),
            VarDecl(field4,FundamentalType.INT_T,None)])
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_simple_program(self):
        source_code = """
        BYTE somebyte = [$12]

        PROC main()
            DEVPRINT (somebyte)
        RETURN
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_program()
        self.maxDiff = None
        symbol_table_entry = symbol_table.find("main")
        self.assertEqual(symbol_table_entry.name, "main")
        self.assertEqual(symbol_table_entry.entry_type, EntryType.ROUTINE)
        self.assertEqualIgnoreWhitespace(
            str(tree),
            """
            Program([Module(
            [VarDecl(somebyte,FundamentalType.BYTE_T,InitOpts([18],False))],
            [Routine(main,[],[],
            [DevPrint(Var(somebyte,FundamentalType.BYTE_T)),Return(None)],None,None)])])
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_assignment(self):
        source_code = """
        BYTE globalbyte
        PROC main()
            BYTE localbyte
            globalbyte = 1
            localbyte = 2
        RETURN
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_program()
        self.maxDiff = None
        self.assertEqualIgnoreWhitespace(
            str(tree),
            """
            Program([Module(
            [VarDecl(globalbyte,FundamentalType.BYTE_T,None)],
            [Routine(main,[],
              [VarDecl(localbyte,FundamentalType.BYTE_T,None)],
              [Assign(Var(globalbyte,FundamentalType.BYTE_T),Const(1)),
              Assign(Var(localbyte,FundamentalType.BYTE_T),Const(2)),
              Return(None)],None,None)])])
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)

    def test_routine_calls(self):
        source_code = """
        PROC proc1()
            DEVPRINT(1)
        RETURN

        PROC proc2(BYTE p2arg1, p2arg2, INT p2arg3)
            CARD p2local
            proc1()
            DEVPRINT(p2arg1)

        PROC main()
            proc2(6)
        RETURN
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_program()
        self.maxDiff = None
        self.assertEqualIgnoreWhitespace(
            str(tree),
            """
            Program([Module([],
            [Routine(proc1,[],[],[DevPrint(Const(1)),Return(None)],None,None),
            Routine(proc2,
              [VarDecl(p2arg1,FundamentalType.BYTE_T,None),
              VarDecl(p2arg2,FundamentalType.BYTE_T,None),
              VarDecl(p2arg3,FundamentalType.INT_T,None)],
              [VarDecl(p2local,FundamentalType.CARD_T,None)],
              [CallStmt(Call(proc1,[],None)),
              DevPrint(Var(p2arg1,FundamentalType.BYTE_T))],None,None),
            Routine(main,[],[],
              [CallStmt(Call(proc2,[Const(6),Const(0),Const(0)],None)),Return(None)],None,None)])])
            """,
        )
        self.assertEqual(parser.current_token().tok_type, TokenType.EOF)
