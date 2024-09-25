#!/usr/bin/env python3

import argparse
from typing import cast

from retraction.ast import Routine
from retraction.bcwalk import BCWalk
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
        tokens = tokenize(source_code, source_file)
        symbol_table = SymTab()
        codegen = ByteCodeGen(symbol_table)
        parser = Parser(tokens, symbol_table)
        # parser.parse_dev()
        tree = parser.parse_program()
        bc_walk = BCWalk(codegen)
        bc_walk.walk(tree)
        print(codegen.code)
        vm = VirtualMachine(codegen.code, symbol_table)
        last_routine_entry = symbol_table.get_last_routine()
        routine_node = cast(Routine, last_routine_entry.node)
        entry_point = routine_node.addr
        vm.run(entry_point)
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    main()
