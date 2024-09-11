from binascii import hexlify
import unittest

from retraction.symtab import SymTab
from retraction.bcvisitor import BCVisitor
from retraction.codegen import ByteCodeGen
from retraction.parser import Parser
from retraction.tokens import tokenize


# Dummy source filename for tests
S_F = "<test>"


class test_BCVisitor(unittest.TestCase):
    def test_global_decl(self):
        source_code = """
        BYTE x
        CHAR y = ['a]
        INT z = [$1234]
        CARD a
        """
        tokens = tokenize(source_code, S_F)
        symbol_table = SymTab()
        parser = Parser(tokens, symbol_table)
        tree = parser.parse_program()
        codegen = ByteCodeGen(symbol_table, 0)
        visitor = BCVisitor(codegen)
        tree.accept(visitor)
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
