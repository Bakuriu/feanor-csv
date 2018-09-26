# Copyright 2018 Giacomo Alzetta <giacomo.alzetta+feanor@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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