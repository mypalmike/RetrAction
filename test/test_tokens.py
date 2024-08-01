import unittest
from retraction import tokenize, Token, TokenType


class TokenizeTestCase(unittest.TestCase):
    def test_keyword_tokens(self):
        source_code = "IF THEN ELSE"
        expected_tokens = [
            Token(TokenType.IF, None),
            Token(TokenType.THEN, None),
            Token(TokenType.ELSE, None),
            Token(TokenType.EOF, None),
        ]
        tokens = tokenize(source_code)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected_token.type)
            self.assertEqual(token.value, expected_token.value)

    def test_symbol_tokens(self):
        source_code = "+ - * / & % ! = == <> # > >= < <= ^ @ (<>)"
        expected_tokens = [
            Token(TokenType.OP_PLUS, None),
            Token(TokenType.OP_MINUS, None),
            Token(TokenType.OP_TIMES, None),
            Token(TokenType.OP_DIVIDE, None),
            Token(TokenType.OP_BIT_AND, None),
            Token(TokenType.OP_BIT_OR, None),
            Token(TokenType.OP_BIT_XOR, None),
            Token(TokenType.OP_EQ, None),
            Token(TokenType.OP_SELF_ASSIGN, None),
            Token(TokenType.OP_NE, None),
            Token(TokenType.OP_NE, None),
            Token(TokenType.OP_GT, None),
            Token(TokenType.OP_GE, None),
            Token(TokenType.OP_LT, None),
            Token(TokenType.OP_LE, None),
            Token(TokenType.OP_CARET, None),
            Token(TokenType.OP_AT, None),
            Token(TokenType.OP_LPAREN, None),
            Token(TokenType.OP_NE, None),
            Token(TokenType.OP_RPAREN, None),
            Token(TokenType.EOF, None),
        ]

        # Token(TokenType.PLUS, None),
        # Token(TokenType.MINUS, None),
        # Token(TokenType.TIMES, None),
        # Token(TokenType.DIVIDE, None),
        # Token(TokenType.AND, None),
        # Token(TokenType.MOD, None),
        # Token(TokenType.NOT, None),
        # Token(TokenType.EQUAL, None),
        # Token(TokenType.NE, None),
        # Token(TokenType.NE, None),
        # Token(TokenType.GR, None),
        # Token(TokenType.GE, None),
        # Token(TokenType.LS, None),
        # Token(TokenType.LE, None),
        # Token(TokenType.CARET, None),
        # Token(TokenType.AT, None),
        # Token(TokenType.LPAREN, None),
        # Token(TokenType.NE, None),
        # Token(TokenType.RPAREN, None),
        # Token(TokenType.EOF, None),

        tokens = tokenize(source_code)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected_token.type)
            self.assertEqual(token.value, expected_token.value)

    def test_literal_tokens(self):
        source_code = '"hello world" $1A \'c 123'
        expected_tokens = [
            Token(TokenType.STRING_LITERAL, "hello world"),
            Token(TokenType.HEX_LITERAL, "1A"),
            Token(TokenType.CHAR_LITERAL, "c"),
            Token(TokenType.INT_LITERAL, "123"),
            Token(TokenType.EOF, None),
        ]
        tokens = tokenize(source_code)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected_token.type)
            self.assertEqual(token.value, expected_token.value)

    def test_identifier_tokens(self):
        source_code = "apples Bananas cu_cumbers d0nutS"
        expected_tokens = [
            Token(TokenType.IDENTIFIER, "apples"),
            Token(TokenType.IDENTIFIER, "Bananas"),
            Token(TokenType.IDENTIFIER, "cu_cumbers"),
            Token(TokenType.IDENTIFIER, "d0nutS"),
            Token(TokenType.EOF, None),
        ]
        tokens = tokenize(source_code)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected_token.type)
            self.assertEqual(token.value, expected_token.value)
