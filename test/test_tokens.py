import unittest
from retraction import tokenize, Token, TokenType
from retraction.define import DefineStack


# Dummy source filename for tests
S_F = "<test>"
DEF_STACK = DefineStack()


class TokenizeTestCase(unittest.TestCase):
    def test_keyword_tokens(self):
        source_code = "IF THEN ELSE"
        expected_tokens = [
            Token(TokenType.IF, None, S_F, 0),
            Token(TokenType.THEN, None, S_F, 0),
            Token(TokenType.ELSE, None, S_F, 0),
            Token(TokenType.EOF, None, S_F, 0),
        ]
        tokens = tokenize(source_code, S_F, DEF_STACK)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.tok_type, expected_token.tok_type)
            self.assertEqual(token.value, expected_token.value)

    def test_symbol_tokens(self):
        source_code = "+ - * / & % ! = == <> # > >= < <= ^ @ (<>)"
        expected_tokens = [
            Token(TokenType.OP_PLUS, None, S_F, 0),
            Token(TokenType.OP_MINUS, None, S_F, 0),
            Token(TokenType.OP_TIMES, None, S_F, 0),
            Token(TokenType.OP_DIVIDE, None, S_F, 0),
            Token(TokenType.OP_BIT_AND, None, S_F, 0),
            Token(TokenType.OP_BIT_OR, None, S_F, 0),
            Token(TokenType.OP_BIT_XOR, None, S_F, 0),
            Token(TokenType.OP_EQ, None, S_F, 0),
            Token(TokenType.OP_SELF_ASSIGN, None, S_F, 0),
            Token(TokenType.OP_NE, None, S_F, 0),
            Token(TokenType.OP_NE, None, S_F, 0),
            Token(TokenType.OP_GT, None, S_F, 0),
            Token(TokenType.OP_GE, None, S_F, 0),
            Token(TokenType.OP_LT, None, S_F, 0),
            Token(TokenType.OP_LE, None, S_F, 0),
            Token(TokenType.OP_CARET, None, S_F, 0),
            Token(TokenType.OP_AT, None, S_F, 0),
            Token(TokenType.OP_LPAREN, None, S_F, 0),
            Token(TokenType.OP_NE, None, S_F, 0),
            Token(TokenType.OP_RPAREN, None, S_F, 0),
            Token(TokenType.EOF, None, S_F, 0),
        ]

        tokens = tokenize(source_code, S_F, DEF_STACK)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.tok_type, expected_token.tok_type)
            self.assertEqual(token.value, expected_token.value)

    def test_literal_tokens_and_line_numbers(self):
        source_code = """ "hello world"$1A
        'c 123 """
        expected_tokens = [
            Token(TokenType.STRING_LITERAL, "hello world", S_F, 0),
            Token(TokenType.HEX_LITERAL, "1A", S_F, 0),
            Token(TokenType.CHAR_LITERAL, "c", S_F, 1),
            Token(TokenType.INT_LITERAL, "123", S_F, 1),
            Token(TokenType.EOF, None, S_F, 1),
        ]
        tokens = tokenize(source_code, S_F, DEF_STACK)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.tok_type, expected_token.tok_type)
            self.assertEqual(token.value, expected_token.value)

    def test_identifier_tokens(self):
        source_code = "apples Bananas cu_cumbers d0nutS"
        expected_tokens = [
            Token(TokenType.IDENTIFIER, "apples", S_F, 0),
            Token(TokenType.IDENTIFIER, "Bananas", S_F, 0),
            Token(TokenType.IDENTIFIER, "cu_cumbers", S_F, 0),
            Token(TokenType.IDENTIFIER, "d0nutS", S_F, 0),
            Token(TokenType.EOF, None, S_F, 0),
        ]
        tokens = tokenize(source_code, S_F, DEF_STACK)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.tok_type, expected_token.tok_type)
            self.assertEqual(token.value, expected_token.value)
