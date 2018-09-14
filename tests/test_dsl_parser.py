import unittest

from feanor.dsl import get_parser
from feanor.dsl.ast import *


class ParsingTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = get_parser()


class TestParser(ParsingTestCase):

    def test_can_parse_type(self):
        got = self.parser.parse('%int')
        self.assertEqual(TypeNameNode.of('int'), got)

    def test_can_parse_type_with_empty_config(self):
        got = self.parser.parse('%int{}')
        self.assertEqual(TypeNameNode.of('int'), got)

    def test_can_parse_type_with_config(self):
        got = self.parser.parse('%int{"min":10,"max":15}')
        self.assertEqual(TypeNameNode.of('int', {'min': 10, 'max': 15}), got)

    def test_can_parse_reference(self):
        got = self.parser.parse('@int')
        self.assertEqual(ReferenceNode.of('int'), got)

    def test_can_parse_choice(self):
        got = self.parser.parse('%int<|>%float')
        expected = BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float'))
        self.assertEqual(expected, got)

    def test_can_parse_choice_no_angle_parenthesis(self):
        got = self.parser.parse('%int|%float')
        expected = BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float'))
        self.assertEqual(expected, got)

    def test_can_parse_choice_with_left_config(self):
        got = self.parser.parse('%int<5|>%float')
        expected = BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float'), LiteralNode(5))
        self.assertEqual(expected, got)

    def test_can_parse_choice_with_right_config(self):
        got = self.parser.parse('%int<|"ciao">%float')
        expected = BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float'),
                                   right_config=LiteralNode("ciao"))
        self.assertEqual(expected, got)

    def test_can_parse_choice_with_left_and_right_config(self):
        got = self.parser.parse('%int<"ciao"|5>%float')
        expected = BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float'), LiteralNode("ciao"),
                                   LiteralNode(5))
        self.assertEqual(expected, got)

    def test_can_parse_merge(self):
        got = self.parser.parse('%int + %float')
        expected = BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('float'))
        self.assertEqual(expected, got)

    def test_can_parse_concat(self):
        got = self.parser.parse('%int . %float')
        expected = BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float'))
        self.assertEqual(expected, got)

    def test_can_parse_concat_center_dot(self):
        got = self.parser.parse('%int·%float')
        expected = BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float'))
        self.assertEqual(expected, got)

    def test_call_no_arguments(self):
        got = self.parser.parse('func()')
        expected = CallNode.of('func', ())
        self.assertEqual(expected, got)

    def test_call_one_argument(self):
        got = self.parser.parse('func(@a)')
        expected = CallNode.of('func', (ReferenceNode.of('a'),))
        self.assertEqual(expected, got)

    def test_call_two_arguments(self):
        got = self.parser.parse('func(@a,%int)')
        expected = CallNode.of('func', (ReferenceNode.of('a'), TypeNameNode.of('int')))
        self.assertEqual(expected, got)

    def test_let_expression_with_one_define(self):
        got = self.parser.parse('let a := %int in @a')
        expected = LetNode.of([('a', TypeNameNode.of('int'))], ReferenceNode.of('a'))
        self.assertEqual(expected, got)

    def test_let_expression_with_two_defines(self):
        got = self.parser.parse('let a := %int b := %float in @a+@b')
        expected = LetNode.of([('a', TypeNameNode.of('int')), ('b', TypeNameNode.of('float'))],
                              BinaryOpNode.of('+', ReferenceNode.of('a'), ReferenceNode.of('b')))
        self.assertEqual(expected, got)

    def test_parenthesis_do_not_add_a_node_in_ast(self):
        got = self.parser.parse('(%int)')
        expected = TypeNameNode.of('int')
        self.assertEqual(expected, got)

    def test_assignment_with_type(self):
        got = self.parser.parse('(%int)=name')
        expected = AssignNode.of(TypeNameNode.of('int'), 'name')
        self.assertEqual(expected, got)

    def test_assignment_with_reference(self):
        got = self.parser.parse('(@int)=name')
        expected = AssignNode.of(ReferenceNode.of('int'), 'name')
        self.assertEqual(expected, got)

    def test_projection(self):
        got = self.parser.parse('%int_3')
        expected = ProjectionNode.of(TypeNameNode.of('int'), 3)
        self.assertEqual(expected, got)

    def test_projection_single_index_in_parenthesis(self):
        got = self.parser.parse('%int_(3)')
        expected = ProjectionNode.of(TypeNameNode.of('int'), 3)
        self.assertEqual(expected, got)

    def test_projection_can_have_multiple_indices(self):
        got = self.parser.parse('%int _ (3,5, 7)')
        expected = ProjectionNode.of(TypeNameNode.of('int'), 3, 5, 7)
        self.assertEqual(expected, got)


class TestOperatorPrecedence(ParsingTestCase):

    def test_projection_has_higher_precedence_than_choice(self):
        got = self.parser.parse('%float | %int_3')
        expected = BinaryOpNode.of('|', TypeNameNode.of('float'), ProjectionNode.of(TypeNameNode.of('int'), 3))
        self.assertEqual(expected, got)

    def test_projection_has_higher_precedence_than_merge(self):
        got = self.parser.parse('%float + %int_3')
        expected = BinaryOpNode.of('+', TypeNameNode.of('float'), ProjectionNode.of(TypeNameNode.of('int'), 3))
        self.assertEqual(expected, got)

    def test_projection_has_higher_precedence_than_concat(self):
        got = self.parser.parse('%float · %int_3')
        expected = BinaryOpNode.of('.', TypeNameNode.of('float'), ProjectionNode.of(TypeNameNode.of('int'), 3))
        self.assertEqual(expected, got)

    def test_concat_has_higher_precedence_than_choice(self):
        got = self.parser.parse('%float | %int · %int')
        expected = BinaryOpNode.of(
            '|',
            TypeNameNode.of('float'),
            BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int'))
        )
        self.assertEqual(expected, got)

    def test_concat_has_higher_precedence_than_merge(self):
        got = self.parser.parse('%float + %int · %int')
        expected = BinaryOpNode.of(
            '+',
            TypeNameNode.of('float'),
            BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int'))
        )
        self.assertEqual(expected, got)

    def test_merge_has_higher_precedence_than_choice(self):
        got = self.parser.parse('%float | %int + %int')
        expected = BinaryOpNode.of(
            '|',
            TypeNameNode.of('float'),
            BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('int'))
        )
        self.assertEqual(expected, got)


class TestComplexExpressions(ParsingTestCase):
    def test_assignment_can_be_used_as_operand(self):
        got = self.parser.parse('(%int)=a + %float')
        expected = BinaryOpNode.of(
            '+',
            AssignNode.of(TypeNameNode.of('int'), 'a'),
            TypeNameNode.of('float'),
        )
        self.assertEqual(expected, got)

    def test_call_one_argument_complex(self):
        got = self.parser.parse('func((@a<|>%int))')
        arg_one = BinaryOpNode.of('|', ReferenceNode.of('a'), TypeNameNode.of('int'))
        expected = CallNode.of('func', (arg_one,))
        self.assertEqual(expected, got)

    def test_call_two_arguments_complex(self):
        got = self.parser.parse('func((@a<|>%int),(@b + %float))')
        arg_one = BinaryOpNode.of('|', ReferenceNode.of('a'), TypeNameNode.of('int'))
        arg_two = BinaryOpNode.of('+', ReferenceNode.of('b'), TypeNameNode.of('float'))
        expected = CallNode.of('func', (arg_one, arg_two))
        self.assertEqual(expected, got)

    def test_assignment_complex_expression(self):
        got = self.parser.parse('(%int + %float)=name')
        expr = BinaryOpNode.of(
            '+',
            TypeNameNode.of('int'),
            TypeNameNode.of('float'),
        )
        expected = AssignNode.of(expr, 'name')
        self.assertEqual(expected, got)


class TestPerformance(ParsingTestCase):
    def test_can_deeply_nest_expression(self):
        got = self.parser.parse('(' * 1500 + '%int' + ')' * 1500)
        expected = TypeNameNode.of('int')
        self.assertEqual(expected, got)


class TestIncorrectExpressions(ParsingTestCase):
    def test_raises_error_if_invalid_type_name(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('#.int')

    def test_raises_error_if_invalid_reference_name(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('@.bad-ref')

    def test_raises_error_if_invalid_function_call_name(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('my.function(%int)')

    def test_raises_error_if_argument_is_literal(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('ciao(5)')

    def test_raises_error_if_unbalanced_parenthesis(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('(%int|%float))')

    def test_raises_error_if_missing_colon_in_config(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('%int{"a"5}')

    def test_raises_error_if_missing_quote(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('%int{"ciao: 5}')

    def test_raises_error_if_missing_final_brace(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('%int{"ciao":5')

    def test_raises_error_if_merge_inside_angle_parenthesis(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('%int <+> %float')

    def test_raises_error_if_concat_inside_angle_parenthesis(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('%int <.> %float')

    def test_raises_error_if_no_defines_in_let(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('let in %int')

    def test_raises_error_if_redefinition_in_let(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('let a := %int a := %float in @a')

    def test_raises_error_if_expr_in_place_of_identifier(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('let @a := %int in @a')

    def test_raises_error_if_try_to_name_variable_let(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('let let := %int in @a')

    def test_raises_error_if_try_to_name_variable_in(self):
        with self.assertRaises(ParsingError):
            self.parser.parse('let in := %int in @a')
