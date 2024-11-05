# RetrAction

An interpreter and compiler for the Action! programming language. Action! is a language developed in the 1980s for the Atari 8-bit computer line. It is similar to C in terms of overall functionality, including pointer, array, and record types. But it is a bit more limited than C. For instance, it does not support nested records, pointers-to-pointers, or multidimensional arrays. The syntax is simpler than C, requiring neither semicolons nor meaningful whitespace.

The main goal of this project is to have a usable cross-compiler to generate 6502 machine code, hosted on any platform that supports Python.

## Up and running

Download:

```bash
git clone https://github.com/mypalmike/RetrAction.git
```

Run examples:

```bash
./main.py samplecode/arrays.act
```

See samplecode directory for other examples. The interpreter currently outputs extra debug information.

## Status

This is a work in progress. The first major milestone will be completing all functionality of the Action! language, generating the stack VM bytecode.

**What works?**

- Parses virtually all of the Action! language into bytecode.

- VM for a stack-based processor with 64K memory. The VM is mostly designed around being easy to compile to.

- Procedures and function calls.

- Local and global variables.

- Pointers.

- Records.

- Arrays.

- Binary operations.

- IF/ELSEIF/ELSE/ENDIF

- DO/WHILE/UNTIL/EXIT

**What's left?**

- Unary negation.

- FOR loops. These were implemented in an earlier version before a major change (adding ast rather than flat/direct compilation) and should be relatively simple to add again.

- Local variable initialization.

- "Preprocessor" - INCLUDE, DEFINE, SET, and comments. Note: the "SET" directive, which was designed to set memory locations on an Atari 8-bit machine at compile time might be emulated at some point for "common" compile-time settings.

- Case-insensitive compilation, which is an option in the original Action! compiler.

## Future work

- 6502 backend

- Tools to deploy to Atari 8-bit machines

## Pie in the sky future features

- Target other 6502 architectures (Apple 2, C64, NES).

- Target other 8- and 16-bit processors (Z80, 8080, ?)

- Target modern 32- and 64- bit processors via LLVM.

- Language improvements. Simple ones like adding unary "NOT". BCD types (they have native 6502 support). Float types. Floating point, 32 bit, 64 bit integers for modern processors.

## Useful links

https://atariwiki.org/wiki/Wiki.jsp?page=Action

https://craftinginterpreters.com

https://atari800.github.io/

https://github.com/jhallen/atari-tools
