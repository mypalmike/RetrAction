from binascii import hexlify
import unittest

from retraction.define import DefineStack
from retraction.symtab import SymTab
from retraction.bcwalk import BCWalk
from retraction.codegen import ByteCodeGen
from retraction.parser import Parser
from retraction.tokens import tokenize


# Dummy source filename for tests
S_F = "<test>"
DEF_STACK = DefineStack()


class test_BCWalk(unittest.TestCase):
    def test_global_decl(self):
        source_code = """
        BYTE x
        CHAR y = ['a]
        INT z = [$1234]
        CARD a
        """
        tokens = tokenize(source_code, S_F, DEF_STACK)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_program()
        codegen = ByteCodeGen(symbol_table, 0)
        bc_walk = BCWalk(codegen)
        # tree.accept(visitor)
        bc_walk.walk(tree)
        expected_code_hex = hexlify(
            bytearray(
                [
                    0x00,  # BYTE
                    0x61,  # BYTE 'a
                    0x34,  # INT $1234
                    0x12,
                    0x00,  # CARD
                    0x00,
                ]
            ),
            "-",
            -2,
        )
        actual_code_hex = hexlify(codegen.code, "-", -2)
        self.assertEqual(expected_code_hex, actual_code_hex)

    def test_global_array_decl(self):
        source_code = """
        BYTE ARRAY ba(3)
        CHAR ARRAY cha = ['a, 'b]
        CHAR ARRAY st = "Hello"
        CARD ARRAY ca = [$1234, $5678]
        CARD ARRAY ca2 = $1234
        BYTE ARRAY ba2(4) = [1, 2, 3, 4, 5]
        """
        tokens = tokenize(source_code, S_F, DEF_STACK)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_program()
        codegen = ByteCodeGen(symbol_table, 0)
        bc_walk = BCWalk(codegen)
        # tree.accept(visitor)
        bc_walk.walk(tree)
        expected_code_hex = hexlify(
            bytearray(
                [
                    0x00,  # BYTE
                    0x00,
                    0x00,
                    0x61,  # CHAR 'a
                    0x62,  # CHAR 'b
                    0x05,  # CHAR "Hello" including length byte
                    0x48,
                    0x65,
                    0x6C,
                    0x6C,
                    0x6F,
                    0x34,  # CARD $1234
                    0x12,
                    0x78,  # CARD $5678
                    0x56,  # Note: No allocation for ca2 which has a memory address
                    0x01,  # BYTE
                    0x02,
                    0x03,
                    0x04,
                    0x05,
                ]
            ),
            "-",
            -2,
        )
        actual_code_hex = hexlify(codegen.code, "-", -2)
        self.assertEqual(expected_code_hex, actual_code_hex)

    def test_proc(self):
        source_code = """
        PROC proc1()
            DEVPRINT(1)
        RETURN

        PROC main()
          proc1()
        RETURN
        """
        tokens = tokenize(source_code, S_F, DEF_STACK)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_program()
        codegen = ByteCodeGen(symbol_table, 0)
        bc_walk = BCWalk(codegen)
        bc_walk.walk(tree)
        expected_code_hex = hexlify(
            bytearray(
                [
                    0x16,  # CONST
                    0x00,  # Type BYTE
                    0x01,  # Value 1
                    0xC8,  # DEVPRINT
                    0x00,  # Type BYTE
                    0x1B,  # RETURN
                    0x04,  # Type VOID
                    0x1A,  # ROUTINE_CALL
                    0x04,  # Type VOID
                    0x00,  # Params size
                    0x00,
                    0x00,  # Locals size
                    0x00,
                    0x00,  # Routine address
                    0x00,
                    0x1B,  # RETURN
                    0x04,  # Type VOID
                ]
            ),
            "-",
            -2,
        )
        actual_code_hex = hexlify(codegen.code, "-", -2)
        self.assertEqual(expected_code_hex, actual_code_hex)
