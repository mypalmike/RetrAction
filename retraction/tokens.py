from io import StringIO, TextIOBase
import string

from enum import Enum, auto

from retraction.define import DefineStack
from retraction.error import IdentifierError, InternalError, SyntaxError


class TokenType(Enum):
    AND = auto()
    ARRAY = auto()
    BYTE = auto()
    CARD = auto()
    CHAR = auto()
    DO = auto()
    ELSE = auto()
    ELSEIF = auto()
    EXIT = auto()
    FI = auto()
    FOR = auto()
    FUNC = auto()
    IF = auto()
    INT = auto()
    LSH = auto()
    MOD = auto()
    MODULE = auto()
    OD = auto()
    OR = auto()
    POINTER = auto()
    PROC = auto()
    RETURN = auto()
    RSH = auto()
    STEP = auto()
    THEN = auto()
    TO = auto()
    TYPE = auto()
    UNTIL = auto()
    WHILE = auto()
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_TIMES = auto()
    OP_DIVIDE = auto()
    OP_BIT_AND = auto()
    OP_BIT_OR = auto()
    OP_BIT_XOR = auto()
    OP_EQ = auto()
    OP_NE = auto()
    OP_GT = auto()
    OP_GE = auto()
    OP_LT = auto()
    OP_LE = auto()
    OP_CARET = auto()
    OP_AT = auto()
    OP_LPAREN = auto()
    OP_RPAREN = auto()
    OP_DOT = auto()
    OP_LBRACK = auto()
    OP_RBRACK = auto()
    # OP_QUOTE = auto()
    # OP_SQUOTE = auto()
    OP_SELF_ASSIGN = auto()
    OP_COMMA = auto()
    STRING_LITERAL = auto()
    CHAR_LITERAL = auto()
    INT_LITERAL = auto()
    HEX_LITERAL = auto()
    IDENTIFIER = auto()
    EOF = auto()
    # TODO: Remove this after it's not needed
    DEVPRINT = auto()
    # TODO: Move the tokens after this to preprocessor
    DEFINE = auto()
    INCLUDE = auto()
    SET = auto()
    # SEMICOLON = auto()


# Create a reverse mapping from integers to token type strings
INT_TO_TOKEN = {token.value: token.name for token in TokenType}

FUND_TYPES = {
    TokenType.BYTE,
    TokenType.CARD,
    TokenType.CHAR,
    TokenType.INT,
}

PRIMITIVE_TYPES = {
    TokenType.BYTE,
    TokenType.CARD,
    TokenType.CHAR,
    TokenType.INT,
    TokenType.POINTER,
}

TEXT_TO_TOKEN = {
    "AND": TokenType.AND,
    "ARRAY": TokenType.ARRAY,
    "BYTE": TokenType.BYTE,
    "CARD": TokenType.CARD,
    "CHAR": TokenType.CHAR,
    "DO": TokenType.DO,
    "ELSE": TokenType.ELSE,
    "ELSEIF": TokenType.ELSEIF,
    "EXIT": TokenType.EXIT,
    "FI": TokenType.FI,
    "FOR": TokenType.FOR,
    "FUNC": TokenType.FUNC,
    "IF": TokenType.IF,
    "INT": TokenType.INT,
    "LSH": TokenType.LSH,
    "MOD": TokenType.MOD,
    "MODULE": TokenType.MODULE,
    "OD": TokenType.OD,
    "OR": TokenType.OR,
    "POINTER": TokenType.POINTER,
    "PROC": TokenType.PROC,
    "RETURN": TokenType.RETURN,
    "RSH": TokenType.RSH,
    "STEP": TokenType.STEP,
    "THEN": TokenType.THEN,
    "TO": TokenType.TO,
    "TYPE": TokenType.TYPE,
    "UNTIL": TokenType.UNTIL,
    "WHILE": TokenType.WHILE,
    "XOR": TokenType.OP_BIT_XOR,
    "+": TokenType.OP_PLUS,
    "-": TokenType.OP_MINUS,
    "*": TokenType.OP_TIMES,
    "/": TokenType.OP_DIVIDE,
    "&": TokenType.OP_BIT_AND,
    "%": TokenType.OP_BIT_OR,
    "!": TokenType.OP_BIT_XOR,
    "=": TokenType.OP_EQ,
    "<>": TokenType.OP_NE,
    "#": TokenType.OP_NE,
    ">": TokenType.OP_GT,
    ">=": TokenType.OP_GE,
    "<": TokenType.OP_LT,
    "<=": TokenType.OP_LE,
    "^": TokenType.OP_CARET,
    "@": TokenType.OP_AT,
    "(": TokenType.OP_LPAREN,
    ")": TokenType.OP_RPAREN,
    ",": TokenType.OP_COMMA,
    # "'": TokenType.OP_SQUOTE,
    ".": TokenType.OP_DOT,
    "[": TokenType.OP_LBRACK,
    "]": TokenType.OP_RBRACK,
    "==": TokenType.OP_SELF_ASSIGN,
    # TODO: Remove this after it's not needed
    "DEVPRINT": TokenType.DEVPRINT,
    # TODO: Remove the tokens after this to preprocessor
    "DEFINE": TokenType.DEFINE,
    "INCLUDE": TokenType.INCLUDE,
    "SET": TokenType.SET,
    # ";": TokenType.SEMICOLON,
}


SYMBOL_CHARS = set([s for s in TEXT_TO_TOKEN.keys() if not s[0].isalpha()])


# Token class
class Token:
    def __init__(self, tok_type, value, source_filename, line_number):
        self.tok_type = tok_type
        self.value = value
        self.source_filename = source_filename
        self.line_number = line_number

    def __repr__(self) -> str:
        return f"Token({self.tok_type}, {self.value}, {self.source_filename}, {self.line_number})"

    def int_value(self) -> int:
        """
        Helper to convert the value of a numeric token to an integer.
        """
        if self.tok_type == TokenType.INT_LITERAL:
            return int(self.value)
        elif self.tok_type == TokenType.HEX_LITERAL:
            return int(self.value, 16)
        elif self.tok_type == TokenType.CHAR_LITERAL:
            return ord(self.value)
        else:
            raise InternalError(f"Token {self.tok_type} has no integer value")

    def is_fund_type(self) -> bool:
        """
        Helper to determine if the token represents a fundamental type.
        """
        return self.tok_type in FUND_TYPES

    # def is_primitive_type(self) -> bool:
    #     """
    #     Helper to determine if the token represents a primitive type.
    #     """
    #     return self.tok_type in PRIMITIVE_TYPES

    def source_location(self) -> str:
        return f"{self.source_filename}:{self.line_number}"


class BaseTokenStream:
    def next(self) -> Token:
        raise NotImplementedError()

    @property
    def source_identifier(self) -> str:
        raise NotImplementedError()

    @property
    def line_number(self) -> int:
        raise NotImplementedError()


class TextIOTokenStream(BaseTokenStream):
    def __init__(
        self,
        source: TextIOBase,
        source_identifier: str,
        line_number: int = 0,
        adjust_line_number: bool = True,
    ):
        self.source = source
        self._source_identifier = source_identifier
        self._line_number = line_number
        self.adjust_line_number = adjust_line_number
        self.char_buffer: str | None = None

    def _next_char(self) -> str:
        if self.char_buffer is not None:
            c = self.char_buffer
            self.char_buffer = None
            return c
        return self.source.read(1)

    def _put_back(self, c: str):
        self.char_buffer = c

    @property
    def source_identifier(self) -> str:
        return self._source_identifier

    @property
    def line_number(self) -> int:
        return self._line_number

    def next(self) -> Token:
        while True:
            # Read next character
            c = self._next_char()

            # Check for newline
            if c == "\n":
                if self.adjust_line_number:
                    self._line_number += 1
            elif c.isspace():
                pass
            elif c == "":
                return Token(
                    TokenType.EOF, None, self._source_identifier, self._line_number
                )
            elif c == '"':
                string_const = ""
                while True:
                    c = self._next_char()
                    if c == "":
                        raise SyntaxError("Unterminated string constant")
                    if c == '"':
                        break
                    if c not in string.printable:
                        raise SyntaxError(f"Invalid character in string constant: {c}")
                    string_const += c
                return Token(
                    TokenType.STRING_LITERAL,
                    string_const,
                    self._source_identifier,
                    self._line_number,
                )
            elif c == "'":
                c = self._next_char()
                if c == "":
                    raise SyntaxError("Unterminated character constant")
                return Token(
                    TokenType.CHAR_LITERAL,
                    c,
                    self._source_identifier,
                    self._line_number,
                )
            elif c.isdigit():
                dec_num = c
                while True:
                    c = self._next_char()
                    if not c.isdigit():
                        self._put_back(c)
                        break
                    dec_num += c
                return Token(
                    TokenType.INT_LITERAL,
                    dec_num,
                    self._source_identifier,
                    self._line_number,
                )
            elif c == "$":
                hex_num = ""
                while True:
                    c = self._next_char()
                    if not (c.isdigit() or c in "ABCDEF"):
                        self._put_back(c)
                        break
                    hex_num += c
                return Token(
                    TokenType.HEX_LITERAL,
                    hex_num,
                    self._source_identifier,
                    self._line_number,
                )
            elif c.isalpha():
                word = c
                while True:
                    c = self._next_char()
                    if not (c.isalnum() or c == "_"):
                        self._put_back(c)
                        break
                    word += c
                if word in TEXT_TO_TOKEN:
                    return Token(
                        TEXT_TO_TOKEN[word],
                        None,
                        self._source_identifier,
                        self._line_number,
                    )
                else:
                    return Token(
                        TokenType.IDENTIFIER,
                        word,
                        self._source_identifier,
                        self._line_number,
                    )
            elif c in SYMBOL_CHARS:
                symbol = c
                c = self._next_char()
                if symbol + c in TEXT_TO_TOKEN:
                    symbol += c
                else:
                    self._put_back(c)
                return Token(
                    TEXT_TO_TOKEN[symbol],
                    None,
                    self._source_identifier,
                    self._line_number,
                )
            elif c == ";":
                # Skip comments
                while True:
                    c = self._next_char()
                    if c == "\n" or c == "":
                        self._put_back(c)
                        break
            else:
                raise SyntaxError(f"Invalid character: {c}")


class IncludingTokenStream(BaseTokenStream):
    def __init__(self, inner_stream: BaseTokenStream):
        self.stream_stack = [inner_stream]

    @property
    def source_identifier(self) -> str:
        return self.stream_stack[-1].source_identifier

    @property
    def line_number(self) -> int:
        return self.stream_stack[-1].line_number

    def next(self) -> Token:
        token = self.stream_stack[-1].next()
        if token.tok_type == TokenType.INCLUDE:
            # Get the filename
            filename_token = self.stream_stack[-1].next()
            if filename_token.tok_type != TokenType.STRING_LITERAL:
                raise SyntaxError("Expected string literal after INCLUDE")
            filename = filename_token.value
            is_duplicate = False
            # Check to make sure it's not already included
            for stream in self.stream_stack:
                if (
                    isinstance(stream, TextIOTokenStream)
                    and stream.source_identifier == filename
                ):
                    is_duplicate = True
                    break
            if not is_duplicate:
                f = open(filename, "r")
                new_stream = TextIOTokenStream(f, filename)
                self.stream_stack.append(new_stream)
            # Whether or not the include happened, we need to get the next token.
            # Recursion is the easiest way to implement this.
            return self.next()
        elif token.tok_type == TokenType.EOF:
            # End of the file might be the end of an included file or the end of the
            # main file.
            if len(self.stream_stack) == 1:
                return token
            self.stream_stack.pop()
            # Need to get the next token from the outer stream.
            return self.next()
        return token


class ScopedDefineTokenStream(BaseTokenStream):
    def __init__(self, inner_stream: BaseTokenStream, define_stack: DefineStack):
        self.inner_stream = inner_stream
        self.define_stack = define_stack
        self.override_stream: BaseTokenStream | None = None

    def next(self) -> Token:
        if self.override_stream is not None:
            next_override_token = self.override_stream.next()
            if next_override_token.tok_type == TokenType.EOF:
                self.override_stream = None
                return self.next()
            return next_override_token
        token = self.inner_stream.next()
        if token.tok_type == TokenType.DEFINE:
            # Get the identifier
            identifier_token = self.inner_stream.next()
            if identifier_token.tok_type != TokenType.IDENTIFIER:
                raise SyntaxError("Expected identifier after DEFINE")
            identifier = identifier_token.value
            # Next token must be "="
            equals_token = self.inner_stream.next()
            if equals_token.tok_type != TokenType.OP_EQ:
                raise SyntaxError("Expected = after DEFINE")
            # Get the value
            value_token = self.inner_stream.next()
            if value_token.tok_type == TokenType.STRING_LITERAL:
                value = value_token.value
            else:
                raise SyntaxError("Expected string literal or identifier after DEFINE")
            self.define_stack.set(identifier, value)
            return self.next()
        elif token.tok_type == TokenType.IDENTIFIER:
            value = self.define_stack.get(token.value)
            if value is not None:
                self.override_stream = TextIOTokenStream(
                    StringIO(value),
                    self.inner_stream.source_identifier,
                    self.inner_stream.line_number,
                    False,
                )
                return self.override_stream.next()
        return token


# TODO: Replace this so that tokens are streamed directly to the parser.
# This will fix the issue where the parser does not have the DefineStack
# in the right state to handle scope changes.
def tokenize(
    source_code: str | None, source_filename: str, define_stack: DefineStack
) -> list[Token]:
    io: TextIOBase | None = None
    if source_code:
        # Create a StringIO object from the source code
        io = StringIO(source_code)
    else:
        # Open the file
        io = open(source_filename, "r")
    text_io_tokenizer = TextIOTokenStream(io, source_filename)
    including_tokenizer = IncludingTokenStream(text_io_tokenizer)
    define_tokenizer = ScopedDefineTokenStream(including_tokenizer, define_stack)
    tokenizer = define_tokenizer
    tokens = []
    while True:
        token = tokenizer.next()
        tokens.append(token)
        if token.tok_type == TokenType.EOF:
            break
    for token in tokens:
        print(token)
    return tokens
