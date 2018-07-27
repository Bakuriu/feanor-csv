from . import ast


def get_lexer():
    """Return a new lexer for Feanor's DSL."""
    from ply import lex
    from . import _lex_rules
    return lex.lex(module=_lex_rules)


def get_parser():
    """Return a new parser for Feanor's DSL."""
    from ply import yacc
    from . import _parser_rules
    _ = get_lexer()
    return yacc.yacc(module=_parser_rules, start='expr')