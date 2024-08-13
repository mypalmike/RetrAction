import string

from enum import Enum, auto


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
    XOR = auto()
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
    OP_SEMICOLON = auto()


# Create a reverse mapping from integers to token type strings
INT_TO_TOKEN = {token.value: token.name for token in TokenType}

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
    "XOR": TokenType.XOR,
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
    ";": TokenType.OP_SEMICOLON,
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
            raise ValueError(f"Token {self.tok_type} has no integer value")

    def is_primitive_type(self) -> bool:
        """
        Helper to determine if the token represents a primitive type.
        """
        return self.tok_type in PRIMITIVE_TYPES

    def source_location(self) -> str:
        return f"{self.source_filename}:{self.line_number}"


# Tokenizer function
def tokenize(source_code, source_filename):
    line_number = 0
    tokens = []
    i = 0
    length = len(source_code)

    while i < length:
        # Skip whitespace
        # Check for newline
        if source_code[i] == "\n":
            line_number += 1
            i += 1
            continue

        if source_code[i].isspace():
            i += 1
            continue

        # Match string constants
        if source_code[i] == '"':
            start = i
            i += 1
            while i < length and source_code[i] != '"':
                if source_code[i] not in string.printable or source_code[i] == '"':
                    raise ValueError(
                        f"Invalid character in string constant: {source_code[i]}"
                    )
                i += 1
            if i >= length or source_code[i] != '"':
                raise ValueError("Unterminated string constant")
            i += 1
            string_const = source_code[start:i]
            tokens.append(
                Token(
                    TokenType.STRING_LITERAL,
                    string_const[1:-1],
                    source_filename,
                    line_number,
                )
            )
            continue

        # Match character literals. Unlike most languages, there's no
        # closing quote.
        if source_code[i] == "'":
            if i + 1 < length:
                char_const = source_code[i + 1]
                tokens.append(
                    Token(
                        TokenType.CHAR_LITERAL, char_const, source_filename, line_number
                    )
                )
                i += 2
            else:
                raise ValueError("Invalid character constant")
            continue

        # Match decimal numbers
        if source_code[i].isdigit():
            start = i
            while i < length and source_code[i].isdigit():
                i += 1
            dec_num = source_code[start:i]
            tokens.append(
                Token(TokenType.INT_LITERAL, dec_num, source_filename, line_number)
            )
            continue

        # Match hexadecimal numbers
        if source_code[i] == "$":
            start = i
            i += 1
            while i < length and (
                source_code[i].isdigit() or source_code[i] in "ABCDEF"
            ):
                i += 1
            hex_num = source_code[start + 1 : i]
            tokens.append(
                Token(TokenType.HEX_LITERAL, hex_num, source_filename, line_number)
            )
            continue

        # Match keywords and identifiers
        if source_code[i].isalpha():
            start = i
            while i < length and (source_code[i].isalnum() or source_code[i] == "_"):
                i += 1
            word = source_code[start:i]
            if word in TEXT_TO_TOKEN:
                tokens.append(
                    Token(TEXT_TO_TOKEN[word], None, source_filename, line_number)
                )
            else:
                tokens.append(
                    Token(TokenType.IDENTIFIER, word, source_filename, line_number)
                )
            continue

        # Match symbols
        if source_code[i] in SYMBOL_CHARS:
            symbol = source_code[i]
            i += 1
            # Look ahead to see if we match a two-character symbol.
            if i < length and symbol + source_code[i] in TEXT_TO_TOKEN:
                symbol += source_code[i]
                i += 1

            if symbol in TEXT_TO_TOKEN:
                tokens.append(
                    Token(TEXT_TO_TOKEN[symbol], None, source_filename, line_number)
                )
            else:
                raise ValueError(f"Invalid symbol: {symbol}")
            continue

        # No match
        raise ValueError(f"Invalid character: {source_code[i]}")

    # EOF token
    tokens.append(Token(TokenType.EOF, None, source_filename, line_number))

    return tokens
