from .ast import ParsingError

tokens = (
    'IDENTIFIER',
    'STRING',
    'INTEGER',
    'FLOAT',
    'LET',
    'IN',
    'DEFINE',
)

states = (
    ('string', 'exclusive'),
)

literals = ['%', '@', '{', '}', '(', ')', '=', '<', '>', '_', ':', ',', '+', '.', '|', '[', ']']

def _word_regex(word):
    return word + r'\b' + ('(?<=%s)'%word)*10

t_LET = _word_regex('let')
t_IN = _word_regex('in')

t_IDENTIFIER = r'[a-zA-Z][a-zA-Z0-9]*'



t_DEFINE = r':='


def t_CONCAT(t):
    r"""\.|·"""
    t.type = t.value = '.'
    return t


def t_FLOAT(t):
    r"""\d+\.\d+"""
    t.value = float(t.value)
    return t


def t_INTEGER(t):
    r"""\d+"""
    t.value = int(t.value)
    return t


def t_BEGIN_STRING(t):
    """('''|\"""|'|")"""
    t.lexer.string_start_position = t.lexpos
    t.lexer.string_start_quote = t.value
    t.lexer.string_num_newlines = 0
    t.lexer.begin('string')


def t_newline(t):
    r"""\n+"""
    t.lexer.lineno += len(t.value)


t_ANY_ignore = ' \t'


def t_error(t):
    raise ParsingError('Invalid Syntax: {!r}'.format(t.value))


def t_string_SLASH_QUOTE(t):
    r"""(\\'|\\"|\\\\)"""


def t_string_QUOTE(t):
    """('''|\"""|'|")"""
    if t.value != t.lexer.string_start_quote:
        # we consider this just a piece of the string literal.
        return
    t.type = 'STRING'
    t.value = t.lexer.lexdata[t.lexer.string_start_position + len(t.lexer.string_start_quote):t.lexpos]
    t.value = t.value.encode('utf-8').decode('unicode_escape')
    t.lexpos = t.lexer.string_start_position
    t.lexer.lineno += t.lexer.string_num_newlines
    t.lexer.string_start_quote = t.lexer.string_start_position = t.lexer.string_num_newlines = None
    t.lexer.begin('INITIAL')
    return t


def t_string_any(t):
    r"""[^'"\\]+"""
    t.lexer.string_num_newlines += t.value.count('\n')
    if '\n' in t.value and len(t.lexer.string_start_quote) < 3:
        raise ParsingError('Newline in single-quote string literal.')


def t_string_error(t):
    raise ParsingError('Invalid Syntax inside string-literal: {!r}'.format(t.value))


def t_string_eof(t):
    raise ParsingError('Unexpected EOF in string literal')
