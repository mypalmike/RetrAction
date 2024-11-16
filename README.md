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

- Local and global variable initialization.

- Pointers.

- Records.

- Arrays.

- All operators.

- IF/ELSEIF/ELSE/ENDIF

- All loop structures: WHILE/FOR/DO/UNTIL/EXIT/OD

- Comments.

- Compiler directives INCLUDE, DEFINE.

**What's left?**

- Fix scoped DEFINE. Requires tokenizer to be streamed rather than all tokens gathered into an array in one go. The machinery for this is largely set up (TokenStreams) but the calling code still just calls the tokenize wrapper.

- Compiler SET directive. Note: the "SET" directive, which was designed to set memory locations on an Atari 8-bit machine at compile time might be emulated for common compile-time settings in order to enhance compatibility with the original Action! compiler.

- Local variable initialization to addresses (e.g. "BYTE x = $1234" declaration in a routine). These refer to absolute memory but are scoped locally. Implementation of access seems like it will be somewhat invasive, having to modify variable reads and writes to check for this case.

- == shortcut for self-assignment

- Basic optimizations e.g. math on constants.

- Augment and modify ast to make some things cleaner. e.g. create cast node rather than sprinkle cast operations around. Similar approach for sprinkling of is_relative checks for vars?

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
