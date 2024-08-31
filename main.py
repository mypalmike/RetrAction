#!/usr/bin/env python3

import argparse

from retraction.tokens import tokenize
from retraction.parser import Parser
from retraction.symtab import SymbolTable
from retraction.codegen import ByteCodeGen
from retraction.vm import VirtualMachine


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_file")
    return parser.parse_args()


def main():
    args = parse_args()
    source_file = args.source_file
    with open(source_file) as f:
        source_code = f.read()
    tokens = tokenize(source_code, source_file)
    symbol_table = SymbolTable()
    codegen = ByteCodeGen(symbol_table)
    parser = Parser(tokens, codegen, symbol_table)
    # parser.parse_dev()
    parser.parse_program()
    print(codegen.code)
    vm = VirtualMachine(codegen.code, symbol_table)
    entry_point = symbol_table.routines[-1].entry_point
    vm.run(entry_point)


if __name__ == "__main__":
    main()
