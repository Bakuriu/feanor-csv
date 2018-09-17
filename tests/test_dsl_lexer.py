import unittest

from feanor.dsl import get_lexer
from feanor.dsl.ast import ParsingError


def to_token_dicts(tokens):
    new_tokens = []
    for token in tokens:
        new_tokens.append({name: value for value, name in zip(token, TestLexer.TOKEN_ATTRS_ORDER)})
    return new_tokens


def tokenize(text):
    lexer = get_lexer()
    lexer.input(text)
    return list(iter(lexer.token, None))


class TestLexer(unittest.TestCase):
    TOKEN_ATTRS_ORDER = ('type', 'value', 'lineno', 'lexpos')

    def assertEqualToken(self, expected, got):
        for attr_name, expected_value in expected.items():
            self.assertEqual(expected_value, getattr(got, attr_name))

    def assertEqualTokens(self, expected, got):
        expected = to_token_dicts(expected)
        self.assertEqual(len(expected), len(got))
        for expected_token, got_token in zip(expected, got):
            self.assertEqualToken(expected_token, got_token)

    # Start of tests

    def test_simple_type(self):
        tokens = tokenize('%int')
        expected_tokens = [('%', '%', 1, 0), ('IDENTIFIER', 'int', 1, 1)]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_type_with_generator(self):
        tokens = tokenize('%int:fixed')
        expected_tokens = [('%', '%', 1, 0), ('IDENTIFIER', 'int', 1, 1), (':', ':', 1, 4), ('IDENTIFIER', 'fixed', 1, 5)]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_reference(self):
        tokens = tokenize('@int')
        expected_tokens = [('@', '@', 1, 0), ('IDENTIFIER', 'int', 1, 1)]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_integer(self):
        tokens = tokenize('5')
        expected_tokens = [('INTEGER', 5, 1, 0)]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_float(self):
        tokens = tokenize('5.3')
        expected_tokens = [('FLOAT', 5.3, 1, 0)]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_operators(self):
        operators = '+.·|'
        types = '+..|'
        for op, ty in zip(operators, types):
            tokens = tokenize(op)
            expected_tokens = [(ty, ty, 1, 0)]
            self.assertEqualTokens(expected_tokens, tokens)

    def test_parenthesis(self):
        parenthesis = '(){}<>'
        types = '(){}<>'
        for paren, ty in zip(parenthesis, types):
            tokens = tokenize(paren)
            expected_tokens = [(ty, paren, 1, 0)]
            self.assertEqualTokens(expected_tokens, tokens)

    def test_other_symbols(self):
        symbols = ':=_,'
        types = ':=_,'
        for sym, ty in zip(symbols, types):
            tokens = tokenize(sym)
            expected_tokens = [(ty, sym, 1, 0)]
            self.assertEqualTokens(expected_tokens, tokens)

    def test_empty_call(self):
        tokens = tokenize('func()')
        expected_tokens = [('IDENTIFIER', 'func', 1, 0), ('(', '(', 1, 4), (')', ')', 1, 5)]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_let_expression(self):
        tokens = tokenize('let a := %int in @a')
        expected_tokens = [
            ('LET', 'let'), ('IDENTIFIER', 'a'), ('DEFINE', ':='), ('%', '%'), ('IDENTIFIER', 'int'),
            ('IN', 'in'), ('@', '@'), ('IDENTIFIER', 'a')
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_parenthesized_type(self):
        tokens = tokenize('(%int)')
        expected_tokens = [
            ('(', '(', 1, 0), ('%', '%', 1, 1), ('IDENTIFIER', 'int', 1, 2), (')', ')', 1, 5)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_parenthesized_reference(self):
        tokens = tokenize('(@int)')
        expected_tokens = [
            ('(', '(', 1, 0), ('@', '@', 1, 1), ('IDENTIFIER', 'int', 1, 2), (')', ')', 1, 5)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_type_assignment(self):
        tokens = tokenize('(%int)=name')
        expected_tokens = [
            ('(', '(', 1, 0), ('%', '%', 1, 1), ('IDENTIFIER', 'int', 1, 2),
            (')', ')', 1, 5), ('=', '=', 1, 6), ('IDENTIFIER', 'name', 1, 7)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_type_projection(self):
        tokens = tokenize('(%int)_5')
        expected_tokens = [
            ('(', '(', 1, 0), ('%', '%', 1, 1), ('IDENTIFIER', 'int', 1, 2),
            (')', ')', 1, 5), ('_', '_', 1, 6), ('INTEGER', 5, 1, 7)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_projection_at_end_of_name_is_separate_token(self):
        tokens = tokenize('@ciao_5')
        expected_tokens = [
            ('@', '@', 1, 0), ('IDENTIFIER', 'ciao', 1, 1), ('_', '_', 1, 5), ('INTEGER', 5, 1, 6)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_reference_assignment(self):
        tokens = tokenize('(@int)=name')
        expected_tokens = [
            ('(', '(', 1, 0), ('@', '@', 1, 1), ('IDENTIFIER', 'int', 1, 2),
            (')', ')', 1, 5), ('=', '=', 1, 6), ('IDENTIFIER', 'name', 1, 7)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_simple_binary_or(self):
        tokens = tokenize('%int<|>%int')
        expected_tokens = [
            ('%', '%',), ('IDENTIFIER', 'int'), ('<', '<'), ('|', '|'), ('>', '>'), ('%', '%'), ('IDENTIFIER', 'int')
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_simple_binary_or_left_config(self):
        tokens = tokenize('%int<5|>%int')
        expected_tokens = [
            ('%', '%',), ('IDENTIFIER', 'int'), ('<', '<'), ('INTEGER', 5),
            ('|', '|'), ('>', '>'), ('%', '%'), ('IDENTIFIER', 'int')
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_simple_binary_or_right_config(self):
        tokens = tokenize('%int<|"string">%int')
        expected_tokens = [
            ('%', '%',), ('IDENTIFIER', 'int'), ('<', '<'), ('|', '|'),
            ('STRING', "string"), ('>', '>'), ('%', '%'), ('IDENTIFIER', 'int')
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_simple_binary_or_left_right_config(self):
        tokens = tokenize('%int<"string"|10>%int')
        expected_tokens = [
            ('%', '%',), ('IDENTIFIER', 'int'), ('<', '<'), ('STRING', "string"), ('|', '|'),
            ('INTEGER', 10), ('>', '>'), ('%', '%'), ('IDENTIFIER', 'int')
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_assign_binary_op(self):
        tokens = tokenize('(%int<"string"|10>%int)=name')
        expected_tokens = [('(', '('),
                           ('%', '%',), ('IDENTIFIER', 'int'), ('<', '<'),
                           ('STRING', "string"), ('|', '|'), ('INTEGER', 10),
                           ('>', '>'),
                           ('%', '%'), ('IDENTIFIER', 'int'), (')', ')'), ('=', '='),
                           ('IDENTIFIER', 'name')
                           ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_raise_error_if_name_contains_symbols(self):
        with self.assertRaises(ParsingError) as ctx:
            tokenize('%ci-ao')
        self.assertEqual("Invalid Syntax: \'-ao\'", str(ctx.exception))

    def test_keeps_track_of_lineno(self):
        tokens = tokenize('(\n\n%int\n+\n%int\n\n\n)')
        expected_tokens = [
            ('(', '(', 1), ('%', '%', 3), ('IDENTIFIER', 'int', 3),
            ('+', '+', 4), ('%', '%', 5), ('IDENTIFIER', 'int', 5),
            (')', ')', 8)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_keeps_track_of_lineno_and_lexpos_correctly(self):
        tokens = tokenize('(\n\n%int\n+\n%int\n\n\n)')
        expected_tokens = [
            ('(', '(', 1, 0), ('%', '%', 3, 3), ('IDENTIFIER', 'int', 3, 4),
            ('+', '+', 4, 8), ('%', '%', 5, 10), ('IDENTIFIER', 'int', 5, 11),
            (')', ')', 8, 17)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_tokenize_numeric_literal(self):
        tokens = tokenize('5')
        expected_tokens = [
            ('INTEGER', 5, 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_tokenize_simple_string_single_quote(self):
        tokens = tokenize("'ciao'")
        expected_tokens = [
            ('STRING', 'ciao', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_tokenize_simple_string_double_quote(self):
        tokens = tokenize('"ciao"')
        expected_tokens = [
            ('STRING', 'ciao', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_raise_error_if_mix_single_quotes(self):
        with self.assertRaises(ParsingError):
            tokenize('"ciao\'')
        with self.assertRaises(ParsingError):
            tokenize("'ciao\"")

    def test_can_parse_multi_line_string_single_quote(self):
        tokens = tokenize("'''ciao\nlol'''")
        expected_tokens = [
            ('STRING', 'ciao\nlol', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_parse_multi_line_string_double_quote(self):
        tokens = tokenize('"""ciao\nlol"""')
        expected_tokens = [
            ('STRING', 'ciao\nlol', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_raise_error_if_mix_multi_quotes(self):
        with self.assertRaises(ParsingError):
            tokenize('"""ciao\'\'\'')
        with self.assertRaises(ParsingError):
            tokenize("'''ciao\"\"\"")

    def test_can_escape_single_quote(self):
        tokens = tokenize(r"'ciao\''")
        expected_tokens = [
            ('STRING', 'ciao\'', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_escape_double_quote(self):
        tokens = tokenize(r'"ciao\""')
        expected_tokens = [
            ('STRING', 'ciao\"', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_escape_multi_single_quote(self):
        tokens = tokenize(r"""'''ciao\'\'\''''""")
        expected_tokens = [
            ('STRING', 'ciao\'\'\'', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_escape_multi_double_quote(self):
        tokens = tokenize(r'''"""ciao\"\"\""""''')
        expected_tokens = [
            ('STRING', 'ciao"""', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_escape_complex(self):
        tokens = tokenize(r'''"""ciao\"\"\"\'\'\'ciao\\"""''')
        expected_tokens = [
            ('STRING', 'ciao"""\'\'\'ciao\\', 1, 0)
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_use_different_quotes_from_delimiter_without_escape_in_string(self):
        tokens = tokenize("""'''a"b'c\"\"\"'''""")
        expected_tokens = [
            ('STRING', '''a"b'c"""''', 1, 0),
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_can_lex_a_string_with_newlines_outside_string_literal(self):
        tokens = tokenize("%int\n + \n%int\n\n\n.\n%float")
        expected_tokens = [
            ('%', '%', 1), ('IDENTIFIER', 'int', 1), ('+', '+', 2), ('%', '%', 3),
            ('IDENTIFIER', 'int', 3), ('.', '.', 6), ('%', '%', 7), ('IDENTIFIER', 'float', 7),
        ]
        self.assertEqualTokens(expected_tokens, tokens)

    def test_single_quote_string_cannot_contain_newline(self):
        with self.assertRaises(ParsingError):
            tokenize('"ciao\n"')


    def test_multi_quotes_string_can_contain_newline(self):
        tokens = tokenize('"""ciao\n\n""" .')
        expected_tokens = [('STRING', 'ciao\n\n'), ('.', '.', 3)]
        self.assertEqualTokens(expected_tokens, tokens)


    def test_can_detect_error_inside_string_literal(self):
        with self.assertRaises(ParsingError):
            tokenize('"\\a"')