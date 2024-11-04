# RetrAction

An interpreter and compiler for the Action programming language. Not yet complete.

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

**What works?**

- Parses virtually all of the Action! language into bytecode.

- VM for a stack-based processor with 64K memory. The VM is mostly designed around being easy to compile to.

- Procedures and function calls.

- Local and global variables.

- Pointers.

- Records.

- Arrays.

- IF/ELSEIF/ELSE/ENDIF

**What doesn't work?**

- DO/WHILE/UNTIL and FOR loops. These were implemented in an earlier version before a major change (adding ast rather than flat/direct compilation) and should be relatively simple to add again.

- Local variable initialization.

- "Preprocessor" - INCLUDE, DEFINE, SET, and comments. Note: the "SET" directive, which was designed to set memory locations on an Atari 8-bit machine at compile time might be emulated at some point for "common" compile-time settings.

- Case-insensitive compilation, which is an option in the original Action! compiler.

## Future work

- 6502 backend

- Tools to deploy to Atari 8-bit machines

## Useful links

https://atariwiki.org/wiki/Wiki.jsp?page=Action

https://craftinginterpreters.com

https://atari800.github.io/

https://github.com/jhallen/atari-tools
