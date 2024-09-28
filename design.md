# Commentary on the design

Writing a compiler involves making many decisions and analyzing both pulished specifications and analyzing existing implementations. This document is intended to describe some of the decisions and the analysis behind them. Please note that when I refer to the Action! implementation, I am testing with a cartidge image titled "ACTION-36-ROM-OSS.rom" using the "Atari800" emulator under Linux.

## Generating and interpreting bytecode

My initial goal with this project was to generate 6502 assembly directly from the compiler with no bytecode intermediary. However, as I was developing the compiler, I found a few reasons to generate bytecode.

First, it seemed useful for testing the compiler. Having to run an Atari 800 emulator to test the compiler output would slow development progress.

Second, it seems like a cool feature. Being able to run Action! code directly on any platform where you can run Python would potentially be useful for other people. Quickly prototyping code, finding uses for the language on modern platforms, etc.

And third, it simplified code generation. In particular, I started to wonder how to directly generate correctly-typed arithmetic code without maintaining an intermediate language. In other words, it was not clear to me how one would keep track of the types of operands (e.g. INT and BYTE) and how to correctly cast them and perform operations on them while generating raw 6502 assembly. Given that the original Action! compiler seems to (?) directly generate machine code, there's almost surely a way to avoid this intermediate language. However, the benefits of bytecode generation seem to outweight any drawbacks.

## Comparison to the Lox compiler in "Crafting Interpreters"

The interpreter and compiler design were influenced by the Crafting Compilers book, so if you are familiar with the second half of that book (the implementation of Lox, with its byte code, etc), the design of this codebase should not be entirely foreign.

However, there are some differences. The differences are driven by a few things, including the compiler language implementation (python vs. c), the goal of ultimately compiling to 6402 assembly including following the existing Action! conventions, and personal preferences.

### Bytecode encapsulation

In Lox, the bytecode is literally a stream of bytes, organized into chunks. This was at least partly due to the implementation language being C, where it makes sense to pack things carefully for performance and simplicity. Here in Python land, the benefits of that approach disappear. There is no "chunk" concept in this compiler, and the bytecode in this project is a stream of objects of a type called ByteCode. The bytecodes are still very simple though, each optionally containing one integer value, which parallels the Lox bytecode where operations have zero or one direct operands in the stream. This is somewhat similar to a processor having fixed width instructions.

### Local Variables

For Lox, the compiler generated low-level stack instructions for managing local variables. For the Action! compiler, this would have made it easy to implement the bytecode vm interpreter, but more difficult to generate Action! style assembly. Specifically, Action! actually allocates local variables in the global memory space for performance reasons. One effect of this is to make recursion impossible. As of this writing, I'm considering making different 6502 calling/memory conventions configurable in the backend, so that it should be possible to generate code that can be recursive.

The point here is that this Action! bytecode compiler needs to generate higher-level bytecode than the Lox bytecode compiler for local variables, maintaining more semantic infomation about the context, such as variable names, etc. This may harm performance of the VM somewhat, but the VM's performance is not of the highest importance compared to backend native code generation and flexibility.

### Expression parsing token look-ahead vs. look-behind

The Lox bytecode compiler has look-behind functionality, where it holds the current and previous tokens. I find this harder to reason about than a look-ahead parser, with current and next tokens. In particular, it seems that the Action! compiler could end up needing to "rewind" in some cases if it were to use a look-behind approach. The code for expression parsing in this Action! compiler is very similar to that used in Lox (a Pratt parser driven by a precedence table), but has been changed to look ahead rather than behind.

## The published Action! grammar

The Action! manual is undoubtedly one of the best documents that ever shipped with a programming language product. Back in the days before the internet, you would often buy a compiler or assembler and find nothing in the manual about how to actually program in the language\*, leaving you to have to find other books on how to write code, or even just get started, in the language. The Action! manual came with a thorough explanation of the language, including numerous examples to help the user understand how to actually create software.

Furthermore, the Action! manual contains an appendix that includes a BNF grammar for the language. This was hugely beneficial to the development of this compiler, as you might imagine. Much of the parser code is annotated with BNF rules taken directly from the manual.

However, there are some errors and oversights in the published grammar, and I am documenting the ones I am aware of here. Perhaps I should publish a corrected BNF grammar, but for now there are just the following notes.

> \* A couple of anecdotes:
>
> In high school, my cousin and I both had Atari 800 computers. We would get together to play games and try our hands at writing games in BASIC. We heard about assembly language because it was how you made fast code for games, so of course we wanted to try it out. So he got his hands on the Atari Macro Assembler cartridge. Great, we are on our way to writing the next Miner 2049er! Except the thin manual that came with it said nothing about assembly language. I don't think there was even any sort of "Hello World" example to work through. The cartridge goes in, you turn on the machine, and you get an empty screen with a blinking cursor. We tried what we knew. "LIST", etc. from our experience with BASIC. Since we were by far the most knowledgeable people about computers of anyone we knew, there was nobody to turn to for learning this language. OK, yes if we had been more motivated and/or enterprising, we might have found the resources we needed, but it was not terribly easy to discover tech info at the time. Years later, I happened to come across the official MOS 6502 CPU manual randomly at a library in college, which would have been helpful back in high school. Though of course, I would have also needed some guidance towards gaining a better understanding of computer architecture than I did as a kid.
>
> Another story about manuals lacking in useful information... In college, I took a course in computer architecture. A lot of the homework involved 8086 assembly language, and the preferred tooling was Borland Turbo assembler. My college bookstore had this for sale, and also had Borland Turbo C++ for sale at only a slightly higher price, and this included the assembler. So I decided to splurge because I was pretty sure I wanted to learn C and C++ soon. So I bought this rather huge, heavy Turbo C++ box containing all sorts of disks and manuals. There may have been a dozen books in there, comprising 6-8 inches stacked of paper, literally thousands of pages. Great, I thought. I can learn C and C++ from this! And once again, I was wrong. These books covered how to operate the tools, references for the Borland C++ frameworks, etc. But nothing was in there about how to code in C or C++ (or 8086 assembly for that matter, though now I had coursework which taught me that).

### Statement lists

The published grammar would suggest that a statement list requires at least one statement. The original compiler allows empty statement lists, seemingly in all contexts.

### RETURN statements

A couple things here.

The published grammar shows routine declarations ending in a RETURN, and for no other places where RETURN can happen. But the language actually allows any number of RETURN statements within a routine. This includes having no RETURNs at all, which leads to falling through to the next proc an old trick on 6502 processors).

It seems that adding RETURN as a rule for `<simp stmt>` makes the most sense. But there's some context-awareness needed for parsing RETURN as a simple statement: a function must include a value with its return statement (i.e. `RETURN (x + 3)`). While a routine can be called without all parameters, a return will not compile for a function without the

### Equivalence of `<cond exp>` and `<complex rel>`

I believe the intent was that these are synonymous, but there is a disconnect in the published grammar where `<cond exp>` is on the right-hand side of some rules but never defined.

### Fundamental types as conditions

The grammar rules for `<complex rel>` do not allow for evaluating numerical values as relational expressions. In other words, the code `if 1 then do ...` would be syntactically incorrect by the published grammar rules. However, there are examples in the manual of this, and the original implementation allows it. The rules of the original compiler appear to be non-zero = false, zero = true, as is common in other languages.

### Param decl vs. var decl, multiple issues.

The grammar rules for function and proc declarations say that they optionally take a `param decl` in parentheses, e.g. `PROC foo(BYTE x, BYTE y)`. The grammar states `<param decl> ::= <var decl>`. This is certainly mistaken, as a `var decl` is a single variable declaration, and a proc or function takes a comma-delimited list of variable declarations.

Furthermore, even if we were to treat parameter declarations as a comma-separated list of `var decl`, there are ways in which parameter declarations differ from local and global variable declarations.

Parameter declarations do not take initial values. In some languages, this would look like setting default values, e.g. in python you can have `def foo(x=0)`. This is not allowed in Action!.

Also, record types must be pointers. Action! does not support something like:

```
TYPE myrec = [BYTE b1 INT b2]
PROC foo(myrec val)
; etc.
```

But it does allow `PROC foo(myrec POINTER val)`, though see below about limitations in the Action! compiler.

### Mixing record pointer types in parameter lists with other types

The Action! compiler seems to have problems with parameter lists when record pointer types follow fundamental types.

This compiles:

```
TYPE myrec = [BYTE x INT y]
PROC foo(myrec POINTER x)
```

But this does not:

```
TYPE myrec = [BYTE b1 INT i1]
PROC foo(BYTE b2, myrec POINTER mrp)
```

It's unclear why this is a problem for the Action! compiler, but RetrAction should accept the problematic code.

### Proc and func pointers

The grammar does not seem to support treatment of routines as pointers to those routines, e.g.

```
PROC foo()
  PrintE("In foo")
RETURN

PROC bar()
  CARD fooAddr
  fooAddr = foo  ; fooPtr is now the memory location of the foo procedure
RETURN

```

The original Action! language compiler allows it.

### Register parameter notation

The manual mentions the syntax `=*` as a way to tell the compiler that a routine does not use memory in parameter passing. The first 3 bytes of parameters are passed in the A, X, and Y registers, and apparently there's a benefit to using notation to indicate this to the compiler. So, for example, it appears using `PROC Foo=*(CARD x, BYTE y)` can help the compiler generate better code. This doesn't appear to be mentioned in the grammar.

### Routines as raw bytes

There are examples in the manual of using something similar to array notation to define routines. Here's an example from the book (note it also has the above-mentioned `=*` notation):

```
PROC Position=*(CARD c,BYTE r)
[$5B85$5C86$5A84]
```

The raw data is treated as machine code. This syntax does not appear to be specified in the grammar, but testing it with the Action! compiler, it does compile. The various examples in the book make it difficult to determine exactly how to parse the data. Here's an example from the book where the parsing rules seem hard to deduce:

```
PROC DrawTo=*(CARD c,BYTE r)
[$20GrIO$11A0$4CXIO]
```

Here, FrIO and XIO are the names of other PROCs. It seems that the "G" in GrIO and "X" in XIO simply happen to not be hexadecimal and are thus treated as identifiers.

### Apparent bug in TYPE field names and variable names

The following does not compile in the original implementation:

```
TYPE foo = [BYTE x]
INT x
```

It seems to consider this a name collision, showing error 6, "Declaration error". This would appear to be a bug(?) when considering how most languages treat record types. RetrAction allows this code to compile.

### POINTER initialization

The manual, addendum, and implementation seem to disagree somewhat on this topic. The manual and addendum claim that the language allows only this format:

```
BYTE POINTER foo = $1234
```

But the compiler supports the above in addition to:

```
BYTE POINTER foo = [$1234]
```

It's not obvious what each should do. Let's see what the Action! implementation does.

```
CARD POINTER cp1 = 100
CARD POINTER cp2 = [100]

PROC main()
  PrintCE(cp1)
  PrintCE(cp1^)
  PrintCE(@cp1)
  PrintCE(cp2)
  PrintCE(cp2^)
  PrintCE(@cp2)
RETURN

Output:
100
40082
9499
9501
100
9503
```

The cp1 declaration, without the brackets, appears to do what might be expected in other languages, which is to allocate space for a pointer and set that pointer to point to address 100 (which happens to contain the value 40082). The cp2 declaration appears to allocate a location for a CARD object and then create another space for a pointer to the first location, hence the @cp1, cp2, and @cp2 are addresses near each other, presumably allocated by the Action! compiler.

For now, RetrAction only supports the former initialization.

### The AND and OR operations

The original Action! implementation treats AND and OR as aliases for their bitwise versions, & and % respectively. This approach is sound, but means that the second operand is always evaluated, even when it does not need to be. An important optimization of logical AND and OR in most languages is that they can shortcut if the first operand is sufficient to determine the value of the full expression. For instance, the evaluation of `a < b AND c < d` can avoid evaluating `c < d` in cases where `a < b` is false, because there's no way to make the whole expression true, regarless of the values of c and d. Similarly `a < b OR c < d` is always true if `a < b` is true, so there's no need to evaluate `c < d` in that case. Thus, these operands are typically implemented with jumps to skip over the evaluation of an unnecessary expression. This approach is used in RetrAction.

Note: It's common in some languages for programmers to depend on this shortcircuiting behavior. In C, `if (px != NULL && *px == 3)` avoids a potentially bad pointer dereference that could cause a CPU exception on some platforms when the pointer is NULL because C guarantees that the second operand is never evaluated if the first operand is false.

Note: In RetrAction, when numerical values are used as operands, the result of AND is either 0 or the second operand. The result of OR is either 0 or the first non-zero operand. This is significantly different from the original implementation.
