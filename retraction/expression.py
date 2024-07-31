# from enum import Enum


# # Highest to lowest precedence:
# # ( )
# # - @
# # * / MOD LSH RSH
# # + -
# # = # <> > >= < <=
# # AND &
# # OR %
# # XOR !
# class ExprPrecedence(Enum):
#     NONE = 0
#     XOR = 1
#     OR = 2
#     AND = 3
#     COMPARE = 4
#     TERM = 5
#     FACTOR = 6
#     UNARY = 7
#     # PARENTHESIS = 8
#     # HIGHEST = 9


# class ExprAction(Enum):
#     NONE = 0
#     NUMBER = 1
#     GROUPING = 2
#     UNARY = 3
#     BINARY = 4


# class ExprRule:
#     def __init__(
#         self,
#         prefix: ExprAction,
#         infix: ExprAction,
#         precedence: ExprPrecedence,
#     ):
#         self.prefix = prefix
#         self.infix = infix
#         self.precedence = precedence

#     def is_relational(self):
#         return self.precedence in [
#             ExprPrecedence.COMPARE,
#             ExprPrecedence.AND,
#             ExprPrecedence.OR,
#             ExprPrecedence.XOR,
#         ]


# EXPRESSION_RULES = {
#     TokenType.LPAREN: ExprRule(
#         ExprAction.GROUPING, ExprAction.NONE, ExprPrecedence.NONE
#     ),
#     TokenType.RPAREN: ExprRule(ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE),
#     TokenType.PLUS: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.TERM),
#     TokenType.MINUS: ExprRule(ExprAction.UNARY, ExprAction.BINARY, ExprPrecedence.TERM),
#     TokenType.TIMES: ExprRule(
#         ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
#     ),
#     TokenType.DIVIDE: ExprRule(
#         ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR
#     ),
#     TokenType.MOD: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
#     TokenType.LSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
#     TokenType.RSH: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.FACTOR),
#     TokenType.EQUAL: ExprRule(
#         ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE
#     ),
#     TokenType.NE: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
#     TokenType.GR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
#     TokenType.GE: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
#     TokenType.LS: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
#     TokenType.LE: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.COMPARE),
#     TokenType.AND: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.AND),
#     TokenType.OR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.OR),
#     TokenType.XOR: ExprRule(ExprAction.NONE, ExprAction.BINARY, ExprPrecedence.XOR),
#     TokenType.INT: ExprRule(ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE),
#     TokenType.HEX: ExprRule(ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE),
#     TokenType.CHAR: ExprRule(ExprAction.NUMBER, ExprAction.NONE, ExprPrecedence.NONE),
#     TokenType.EOF: ExprRule(ExprAction.NONE, ExprAction.NONE, ExprPrecedence.NONE),
# }
