#!/usr/bin/env python3

import argparse
from binascii import hexlify
from typing import cast

from retraction.ast import Routine
from retraction.bcwalk import BCWalk
from retraction.define import DefineStack
from retraction.tokens import tokenize
from retraction.parser import Parser
from retraction.symtab import SymTab
from retraction.codegen import ByteCodeGen
from retraction.vm import VirtualMachine


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_file")
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        source_file = args.source_file
        with open(source_file) as f:
            source_code = f.read()
        define_stack = DefineStack()
        tokens = tokenize(source_code, source_file, define_stack)
        symbol_table = SymTab()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, symbol_table, define_stack)
        tree = parser.parse_program()
        bc_walk = BCWalk(codegen)
        bc_walk.walk(tree)
        print(hexlify(codegen.code, "-", -2))
        vm = VirtualMachine(codegen.code, symbol_table)
        entry_point = 0
        vm.run(entry_point)
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    main()
