from enum import Enum, auto

from retraction.tokens import TokenType

# Expressions are parsed using the Pratt method. These classes define the rules
# used by the parser.


class ExprPrecedence(Enum):
    """
    Lowest to highest precedence
    """

    NONE = 0
    XOR = 1
    OR = 2
    AND = 3
    COMPARE = 4
    TERM = 5
    FACTOR = 6
    UNARY = 7


class ExprAction(Enum):
    """
    Action to take when parsing an expression
    """

    NONE = auto()
    NUMERIC_LITERAL = auto()
    GROUPING = auto()
    UNARY = auto()
    BINARY = auto()
    AND = auto()
    OR = auto()
    IDENTIFIER = auto()


class ExprRule:
    """
    Rule for parsing an expression. These are used in the EXPRESSION_RULES table to look up
    the appropriate action to take.
    """

    def __init__(
        self,
        prefix: ExprAction,
        infix: ExprAction,
        precedence: ExprPrecedence,
    ):
        self.prefix = prefix
        self.infix = infix
        self.precedence = precedence

    def is_relational(self):
        return self.precedence in [
            ExprPrecedence.COMPARE,
            ExprPrecedence.AND,
            ExprPrecedence.OR,
            ExprPrecedence.XOR,
        ]


EXPRESSION_RULES = {
    TokenType.OP_LPAREN: ExprRule(
        ExprAction.GROUPING, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.OP_RPAREN: ExprRule(
        ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.OP_PLUS: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.TERM
    ),
    TokenType.OP_MINUS: ExprRule(
        ExprAction.UNARY, ExprAction.BINARY, ExprPrecedence.TERM
    ),
    TokenType.OP_TIMES: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
    ),
    TokenType.OP_DIVIDE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
    ),
    # TODO: Does precedence matter for this?
    TokenType.OP_AT: ExprRule(
        ExprAction.IDENTIFIER, ExprAction.NONE, ExprPrecedence.UNARY
    ),
    TokenType.MOD: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.LSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.RSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
    TokenType.OP_EQ: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_NE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_GT: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_GE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_LT: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.OP_LE: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
    ),
    TokenType.AND: ExprRule(ExprAction.NONE, ExprAction.AND, ExprPrecedence.AND),
    TokenType.OR: ExprRule(ExprAction.NONE, ExprAction.OR, ExprPrecedence.OR),
    TokenType.XOR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.XOR),
    TokenType.OP_BIT_AND: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.AND
    ),
    TokenType.OP_BIT_OR: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.OR
    ),
    TokenType.OP_BIT_XOR: ExprRule(
        ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.XOR
    ),
    TokenType.INT_LITERAL: ExprRule(
        ExprAction.NUMERIC_LITERAL, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.HEX_LITERAL: ExprRule(
        ExprAction.NUMERIC_LITERAL, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.CHAR_LITERAL: ExprRule(
        ExprAction.NUMERIC_LITERAL, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.IDENTIFIER: ExprRule(
        ExprAction.IDENTIFIER, ExprAction.NONE, ExprPrecedence.NONE
    ),
    TokenType.EOF: ExprRule(ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE),
}
