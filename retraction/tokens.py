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
    # TODO: Move the tokens after this to preprocessor
    DEFINE = auto()
    INCLUDE = auto()
    SET = auto()
    OP_SEMICOLON = auto()

    # PLUS = 1
    # MINUS = 2
    # TIMES = 3
    # DIVIDE = 4
    # OR = 5
    # AND = 6
    # EQUAL = 7
    # NE = 8
    # GR = 9
    # GE = 10
    # LS = 11
    # LE = 12
    # REM = 13
    # XOR = 14
    # LSH = 15
    # RSH = 16
    # UMINUS = 17
    # AT = 18
    # SCOLON = 21
    # SQUOTE = 22
    # PERIOD = 23
    # RPAREN = 24
    # LPAREN = 25
    # COMMA = 26
    # DEF = 27
    # DIGIT = 28 + 0x80
    # HEX = 29
    # QUOTE = 30
    # CHAR = 32
    # BYTE = 33
    # INT = 34
    # CARD = 35
    # STRING = 36
    # REAL = 37
    # DEFINE = 38
    # RECORD = 39
    # ARRAY = 64
    # FUNC = 65
    # PROC = 66
    # GET = 67
    # SET = 68
    # POINTER = 69
    # TYPE = 70
    # IF = 80
    # WHILE = 81
    # RETURN = 82
    # EXIT = 83
    # FOR = 84
    # CASE = 85
    # CODE = 86
    # MOD = 87
    # UNTIL = 88
    # LBRACK = 91
    # RBRACK = 93
    # UPARROW = 94
    # THEN = 96
    # ELSE = 97
    # DO = 98
    # FI = 99
    # OD = 100
    # TO = 101
    # STEP = 102
    # OF = 103
    # ESAC = 104
    # EDOC = 105
    # ELSEIF = 106
    # DOWNTO = 107

    # NOT = 108  # mypalmike - added NOT
    # CARET = 109  # mypalmike - added CARET

    # TYPET = 0x70  # 112
    # EOF = 127
    # CONST_T = 0x80
    # VAR_T = 0x88
    # ARRAY_T = 0x90
    # TEMP_T = 0xA8
    # FUNC_T = 0xC0
    # COND_T = 0x48


# Create a reverse mapping from integers to token type strings
INT_TO_TOKEN = {token.value: token.name for token in TokenType}

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
    # TODO: Remove the tokens after this to preprocessor
    "DEFINE": TokenType.DEFINE,
    "INCLUDE": TokenType.INCLUDE,
    "SET": TokenType.SET,
    ";": TokenType.OP_SEMICOLON,
}

# # Define keywords and symbols
# KEYWORDS = [
#     "AND",
#     "ARRAY",
#     "BYTE",
#     "CARD",
#     "CHAR",
#     "DEFINE",
#     "DO",
#     "ELSE",
#     "ELSEIF",
#     "EXIT",
#     "FI",
#     "FOR",
#     "FUNC",
#     "IF",
#     "INCLUDE",
#     "INT",
#     "LSH",
#     "MOD",
#     "MODULE",
#     "OD",
#     "OR",
#     "POINTER",
#     "PROC",
#     "RETURN",
#     "RSH",
#     "SET",
#     "STEP",
#     "THEN",
#     "TO",
#     "TYPE",
#     "UNTIL",
#     "WHILE",
#     "XOR",
# ]

SYMBOL_CHARS = set([s for s in TEXT_TO_TOKEN.keys() if not s[0].isalpha()])

# SYMBOL_CHARS = set(
#     [
#         "+",
#         "-",
#         "*",
#         "/",
#         "&",
#         "%",
#         "!",
#         "=",
#         "<",
#         "#",
#         ">",
#         "$",
#         "^",
#         "@",
#         "(",
#         ")",
#         ",",
#         ";",
#         "'",
#         ".",
#         "[",
#         "]",
#         "==",
#     ]
# )


# Token class
class Token:
    def __init__(self, tok_type, value):
        self.tok_type = tok_type
        self.value = value

    def __repr__(self):
        return f"Token({self.tok_type}, {self.value})"


# Tokenizer function
def tokenize(source_code):
    tokens = []
    i = 0
    length = len(source_code)

    while i < length:
        # Skip whitespace
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
            tokens.append(Token(TokenType.STRING_LITERAL, string_const[1:-1]))
            continue

        # Match character literals. Unlike most languages, there's no
        # closing quote.
        if source_code[i] == "'":
            if i + 1 < length:
                char_const = source_code[i + 1]
                tokens.append(Token(TokenType.CHAR_LITERAL, char_const))
                i += 2
            else:
                raise ValueError("Invalid character constant")
            continue

        # if source_code[i] == "'":
        #     if i + 2 < length and source_code[i + 2] == "'":
        #         char_const = source_code[i : i + 3][1:-1]
        #         tokens.append(Token(TokenType.CHAR, char_const))
        #         i += 3
        #     else:
        #         raise ValueError("Invalid character constant")
        #     continue

        # Match decimal numbers
        if source_code[i].isdigit():
            start = i
            while i < length and source_code[i].isdigit():
                i += 1
            dec_num = source_code[start:i]
            tokens.append(Token(TokenType.INT_LITERAL, dec_num))
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
            tokens.append(Token(TokenType.HEX_LITERAL, hex_num))
            continue

        # Match keywords and identifiers
        if source_code[i].isalpha():
            start = i
            while i < length and (source_code[i].isalnum() or source_code[i] == "_"):
                i += 1
            word = source_code[start:i]
            if word in TEXT_TO_TOKEN:
                tokens.append(Token(TEXT_TO_TOKEN[word], None))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, word))
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
                tokens.append(Token(TEXT_TO_TOKEN[symbol], None))
            else:
                raise ValueError(f"Invalid symbol: {symbol}")
            continue

        # No match
        raise ValueError(f"Invalid character: {source_code[i]}")

    # EOF token
    tokens.append(Token(TokenType.EOF, None))

    return tokens
