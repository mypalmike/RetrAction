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
        source_code = "+ - * / & % ! = <> # > >= < <= ^ @ (<>)"
        expected_tokens = [
            Token(TokenType.PLUS, None),
            Token(TokenType.MINUS, None),
            Token(TokenType.TIMES, None),
            Token(TokenType.DIVIDE, None),
            Token(TokenType.AND, None),
            Token(TokenType.MOD, None),
            Token(TokenType.NOT, None),
            Token(TokenType.EQUAL, None),
            Token(TokenType.NE, None),
            Token(TokenType.NE, None),
            Token(TokenType.GR, None),
            Token(TokenType.GE, None),
            Token(TokenType.LS, None),
            Token(TokenType.LE, None),
            Token(TokenType.CARET, None),
            Token(TokenType.AT, None),
            Token(TokenType.LPAREN, None),
            Token(TokenType.NE, None),
            Token(TokenType.RPAREN, None),
            Token(TokenType.EOF, None),
        ]
        tokens = tokenize(source_code)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected_token.type)
            self.assertEqual(token.value, expected_token.value)

    def test_literal_tokens(self):
        source_code = '"hello world" $1A \'c 123'
        expected_tokens = [
            Token(TokenType.STRING, "hello world"),
            Token(TokenType.HEX, "1A"),
            Token(TokenType.CHAR, "c"),
            Token(TokenType.INT, "123"),
            Token(TokenType.EOF, None),
        ]
        tokens = tokenize(source_code)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected_token.type)
            self.assertEqual(token.value, expected_token.value)

    def test_identifier_tokens(self):
        source_code = "apples Bananas cu_cumbers d0nutS"
        expected_tokens = [
            Token(TokenType.VAR_T, "apples"),
            Token(TokenType.VAR_T, "Bananas"),
            Token(TokenType.VAR_T, "cu_cumbers"),
            Token(TokenType.VAR_T, "d0nutS"),
            Token(TokenType.EOF, None),
        ]
        tokens = tokenize(source_code)
        for token, expected_token in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected_token.type)
            self.assertEqual(token.value, expected_token.value)
