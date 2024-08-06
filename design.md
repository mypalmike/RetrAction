# Commentary on the design

Writing a compiler involves making many decisions. This document is intended to describe some of these decisions and the reasoning behind them.

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
> In high school, my cousin and I both had Atari 800 computers. We played games and tried our hands at writing games too, in BASIC. We heard about assembly language because it was how you made fast code for games, so of course we wanted to try it out. So he got his hands on the Atari Macro Assembler cartridge. Great, we are on our way to writing the next Miner 2049er! Except the thin manual that came with it said nothing about assembly language. I don't think there was even any sort of "Hello World" example to work through. The cartridge goes in, you turn on the machine, and you get an empty screen with a blinking cursor. We tried what we knew. "LIST", etc. from our experience with BASIC. Since we were by far the most knowledgeable people about computers of anyone we knew, there was nobody to turn to for learning this language. OK, yes if we had been more motivated and/or enterprising, we might have found the resources we needed, but it was not terribly easy to discover tech info at the time. Years later, I happened to come across the official MOS 6502 CPU manual randomly at a library in college, which would have been helpful back in high school. Though of course, I would have also needed some guidance towards gaining a better understanding of computer architecture than I did as a kid.
>
> Another story about manuals lacking in useful information... In college, I took a course in computer architecture. A lot of the homework involved 8086 assembly language, and the preferred tooling was Borland Turbo assembler. My college bookstore had this for sale, and also had Borland Turbo C++ for sale at only a slightly higher price, and this included the assembler. So I decided to splurge because I was pretty sure I wanted to learn C and C++ soon. So I bought this rather huge, heavy Turbo C++ box containing all sorts of disks and manuals. There may have been a dozen books in there, comprising 6-8 inches stacked of paper, literally thousands of pages. Great, I thought. I can learn C and C++ from this! And once again, I was wrong. These books covered how to operate the tools, references for the Borland C++ frameworks, etc. But nothing was in there about how to code in C or C++ (or 8086 assembly for that matter, though now I had coursework which taught me that).

### RETURN statement in a function

A function can have a RETURN statement that returns a value (i.e. `<RETURN expr>`). The grammar only shows "RETURN" by itself as a statement.

### `<cond exp>` vs. `<complex rel>`

I believe the intent was that these are synonymous, but there is a disconnect in the published grammar where `<cond exp>` is on the right-hand side of some rules but never defined.
