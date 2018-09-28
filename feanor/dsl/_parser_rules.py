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

from . import _lex_rules
from .ast import *

tokens = _lex_rules.tokens
literals = _lex_rules.literals

precedence = (
    ('left', '|'),
    ('left', '+'),
    ('left', '.'),
)


def p_expr(p):
    """expr : expr '|' choice
            | expr '<' opt_literal expr_dispatcher
            | choice
            | call
            | let_expr
    """
    if len(p) == 4:
        p[0] = BinaryOpNode.of(p[2], p[1], p[3])
    elif len(p) == 5:
        operator, right_config, right = p[4]
        left_config = p[3]
        p[0] = BinaryOpNode(operator, p[1], left_config, right, right_config)
    else:
        p[0] = p[1]


def p_expr_dispatcher(p):
    """expr_dispatcher :  '|' opt_literal '>' choice
    """
    p[0] = (Identifier(p[1]), p[2], p[4])


def p_choice(p):
    """choice : choice '+' term
              | term
    """
    if len(p) == 4:
        p[0] = BinaryOpNode.of(p[2], p[1], p[3])
    else:
        p[0] = p[1]


def p_term(p):
    """term : term '.' concatenandum
            | concatenandum
    """
    if len(p) == 4:
        p[0] = BinaryOpNode.of(p[2], p[1], p[3])
    else:
        p[0] = p[1]


def p_concatenandum(p):
    """concatenandum : concatenandum '_' index_or_indices
                     | factor
    """
    if len(p) > 2:
        p[0] = ProjectionNode(p[1], *p[3])
    else:
        p[0] = p[1]


def p_index_or_indices(p):
    """index_or_indices : INTEGER
                        | '(' numeric_list ')'
    """
    if len(p) == 2:
        p[0] = [LiteralNode(p[1])]
    else:
        p[0] = p[2]
        p[0].reverse()


def p_numeric_list(p):
    """numeric_list : INTEGER
                    | numeric_list ','
                    | INTEGER ',' numeric_list
    """
    if len(p) < 4:
        p[0] = [LiteralNode(p[1])] if len(p) == 2 else p[1]
    else:
        p[0] = p[3]
        p[0].append(LiteralNode(p[1]))


def p_factor(p):
    """factor : type
              | reference
              | simple_expr
              | '(' expr ')' opt_assignment
    """
    if len(p) > 2:
        p[0] = p[2] if p[4] is None else AssignNode(p[2], p[4])
    else:
        p[0] = p[1]


def p_type(p):
    """type : '%' IDENTIFIER opt_producer config"""
    p[0] = TypeNameNode.of(p[2], p[3], p[4])


def p_opt_producer(p):
    """opt_producer : ':' IDENTIFIER
                    | empty
    """
    p[0] = p[2] if len(p) == 3 else 'default'


def p_reference(p):
    """reference : '@' IDENTIFIER"""
    p[0] = ReferenceNode.of(p[2])


def p_call(p):
    """call : IDENTIFIER '(' exprlist ')'"""
    p[3].reverse()
    p[0] = CallNode.of(p[1], p[3])


def p_let_expr(p):
    """let_expr : LET defines_list IN expr"""
    p[2].reverse()
    p[0] = LetNode.of(p[2], p[4])


def p_defines_list(p):
    """defines_list : IDENTIFIER DEFINE expr
                    | IDENTIFIER DEFINE expr defines_list
    """
    if len(p) == 4:
        p[0] = [(p[1], p[3])]
    else:
        p[0] = p[4]
        p[0].append((p[1], p[3]))


def p_config(p):
    """config : dict_literal
              | empty"""
    p[0] = Config.of(p[1])


def p_opt_literal(p):
    """opt_literal : literal
                   | empty"""
    p[0] = p[1]


def p_literal(p):
    """literal : dict_literal
               | list_literal
               | INTEGER
               | FLOAT
               | STRING
    """
    p[0] = LiteralNode(p[1])


def p_dict_literal(p):
    """dict_literal : '{' keypair_list '}'"""
    p[2].reverse()
    p[0] = LiteralNode(dict(p[2])).to_plain_object()


def p_list_literal(p):
    """list_literal : '[' literal_list ']'"""
    p[2].reverse()
    p[0] = LiteralNode(p[2]).to_plain_object()


def p_literal_list(p):
    """literal_list : empty
                    | literal
                    | literal ',' literal_list
    """
    if len(p) > 2:
        p[0] = p[3]
        p[0].append(p[1])
    else:
        p[0] = [p[1]] if p[1] else []


def p_keypair_list(p):
    """keypair_list : empty
                    | keypair
                    | keypair ',' keypair_list
    """
    if len(p) > 2:
        p[0] = p[3]
        p[0].append(p[1])
    else:
        p[0] = [p[1]] if p[1] else []


def p_keypair(p):
    """keypair : STRING ':' literal"""
    p[0] = (p[1], p[3])


def p_exprlist(p):
    """exprlist : empty
                | expr
                | expr ',' exprlist
    """
    if len(p) > 2:
        p[0] = p[3]
        p[0].append(p[1])
    else:
        p[0] = [p[1]] if p[1] else []


def p_opt_assignment(p):
    """opt_assignment : assign_name
                      | empty"""
    p[0] = p[1]


def p_assign_name(p):
    """assign_name : '=' IDENTIFIER"""
    p[0] = Identifier.of(p[2])


def p_empty(p):
    """empty :"""
    p[0] = None


def p_error(p):
    if p is not None:
        msg = f'Invalid Syntax. Found unexpected token {repr(p.type)} at position {p.lexpos} (line {p.lineno})'
    else:
        msg = 'Invalid syntax.'
    raise ParsingError(msg)


def p_simple_expr(p):
    """simple_expr : simple_literal """
    p[0] = SimpleExprNode.of(p[1])


def p_simple_literal(p):
    """simple_literal : STRING
                      | INTEGER
                      | FLOAT
                      | list_literal
    """
    p[0] = LiteralNode.of(p[1])
