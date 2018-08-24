import unittest

from feanor.dsl.ast import *


class TestIdentifier(unittest.TestCase):
    def test_equals_if_same_name(self):
        self.assertEqual(Identifier('a'), Identifier('a'))

    def test_not_equals_if_different_name(self):
        self.assertNotEqual(Identifier('a'), Identifier('b'))

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(Identifier('a'), 'a')

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Config({}),
            ReferenceNode.of('a'),
            TypeNameNode.of('a'),
            LiteralNode('a'),
            AssignNode.of(LiteralNode('a'), 'a'),
            CallNode.of('a', []),

        ]
        for node in other_nodes:
            self.assertNotEqual(Identifier('a'), node)


class TestConfig(unittest.TestCase):
    def test_equals_if_same_config(self):
        self.assertEqual(Config({'a': 17}), Config({'a': 17}))

    def test_not_equals_if_different_config(self):
        self.assertNotEqual(Config({'a': 17}), Config({'a': 18}))
        self.assertNotEqual(Config({'a': 17}), Config({'not_a': 17}))

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(Config({'a': 17}), {'a': 17})

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('{}'),
            ReferenceNode.of('{}'),
            TypeNameNode.of('{}'),
            LiteralNode({}),
            AssignNode.of(LiteralNode({}), '{}'),
            CallNode.of('{}', []),

        ]
        for node in other_nodes:
            self.assertNotEqual(Config({}), node)


class TestTypeNameNode(unittest.TestCase):
    def test_equals_if_same_name(self):
        self.assertEqual(TypeNameNode.of('a'), TypeNameNode.of('a'))

    def test_equals_if_same_name_with_config(self):
        self.assertEqual(TypeNameNode.of('a', {'b': 13}), TypeNameNode.of('a', {'b': 13}))

    def test_not_equals_if_different_name(self):
        self.assertNotEqual(TypeNameNode.of('a'), TypeNameNode.of('b'))

    def test_not_equals_if_different_config(self):
        self.assertNotEqual(TypeNameNode.of('a', {'a': 13}), TypeNameNode.of('b', {'a': 14}))

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(TypeNameNode.of('a'), 'a')

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('a'),
            Config({}),
            ReferenceNode.of('a'),
            LiteralNode('a'),
            AssignNode.of(LiteralNode('a'), 'a'),
            CallNode.of('a', []),

        ]
        for node in other_nodes:
            self.assertNotEqual(TypeNameNode.of('a'), node)


class TestReferenceNode(unittest.TestCase):
    def test_equals_if_same_name(self):
        self.assertEqual(ReferenceNode.of('a'), ReferenceNode.of('a'))

    def test_not_equals_if_different_name(self):
        self.assertNotEqual(ReferenceNode.of('a'), ReferenceNode.of('b'))

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(ReferenceNode.of('a'), 'a')

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('a'),
            Config({}),
            TypeNameNode.of('a'),
            LiteralNode('a'),
            AssignNode.of(LiteralNode('a'), 'a'),
            CallNode.of('a', []),

        ]
        for node in other_nodes:
            self.assertNotEqual(ReferenceNode.of('a'), node)


class TestLiteralNode(unittest.TestCase):
    def test_equals_if_same_string_value(self):
        self.assertEqual(LiteralNode.of('a'), LiteralNode.of('a'))

    def test_not_equals_if_different_string_value(self):
        self.assertNotEqual(LiteralNode.of('a'), LiteralNode.of('b'))

    def test_equals_if_same_int_value(self):
        self.assertEqual(LiteralNode.of(1), LiteralNode.of(1))

    def test_not_equals_if_different_int_value(self):
        self.assertNotEqual(LiteralNode.of(1), LiteralNode.of(2))

    def test_not_equals_if_different_int_value_vs_string_value(self):
        self.assertNotEqual(LiteralNode.of(1), LiteralNode.of('1'))

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(LiteralNode.of('a'), 'a')

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('a'),
            Config({}),
            TypeNameNode.of('a'),
            AssignNode.of(LiteralNode('a'), 'a'),
            CallNode.of('a', []),
        ]
        for node in other_nodes:
            self.assertNotEqual(LiteralNode.of('a'), node)

    def test_to_plain_object_returns_correct_value(self):
        expected_values = [
            'a',
            5,
            {'a': 1, 'b': 3},
            {'a': {'b': {'c': {'d': 1}}}},
        ]
        values = [
            'a',
            5,
            {'a': LiteralNode.of(1), 'b': LiteralNode.of(3)},
            {'a': LiteralNode.of({'b': LiteralNode.of({'c': LiteralNode.of({'d': LiteralNode.of(1)})})})},
        ]
        for value, expected in zip(values, expected_values):
            self.assertEqual(LiteralNode.of(value).to_plain_object(), expected)


class TestAssignNode(unittest.TestCase):
    def test_equals_if_same_name_same_expr(self):
        self.assertEqual(AssignNode.of(LiteralNode.of(1), 'a'), AssignNode.of(LiteralNode.of(1), 'a'))

    def test_not_equals_if_different_name(self):
        self.assertNotEqual(AssignNode.of(LiteralNode.of(1), 'a'), AssignNode.of(LiteralNode.of(1), 'b'))

    def test_not_equals_if_different_value(self):
        self.assertNotEqual(AssignNode.of(LiteralNode.of(1), 'a'), AssignNode.of(LiteralNode.of(2), 'a'))

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(AssignNode.of(LiteralNode.of(1), 'a'), 'a')
        self.assertNotEqual(AssignNode.of(LiteralNode.of(1), 'a'), 1)

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('a'),
            ReferenceNode.of('a'),
            Config({}),
            TypeNameNode.of('a'),
            LiteralNode('a'),
            CallNode.of('a', []),

        ]
        for node in other_nodes:
            self.assertNotEqual(AssignNode.of(LiteralNode('a'), 'a'), node)


class TestBinaryOpNode(unittest.TestCase):
    def test_equals_if_same_name_same_operands(self):
        self.assertEqual(
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a')),
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a'))
        )

    def test_not_equals_if_different_name(self):
        self.assertNotEqual(
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a')),
            BinaryOpNode.of('+', LiteralNode.of(1), Identifier.of('a'))
        )

    def test_not_equals_if_different_left_operand(self):
        self.assertNotEqual(
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a')),
            BinaryOpNode.of('|', LiteralNode.of(2), Identifier.of('a'))
        )

    def test_not_equals_if_different_right_operand(self):
        self.assertNotEqual(
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a')),
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('b'))
        )

    def test_not_equals_if_different_left_config(self):
        self.assertNotEqual(
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a'), LiteralNode.of(1)),
            BinaryOpNode.of('|', LiteralNode.of(2), Identifier.of('a'), LiteralNode.of(2))
        )

    def test_not_equals_if_different_right_config(self):
        self.assertNotEqual(
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a'), right_config=LiteralNode.of(1)),
            BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('b'), right_config=LiteralNode.of(2))
        )

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a')), 'a')
        self.assertNotEqual(BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a')), 1)

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('a'),
            ReferenceNode.of('a'),
            Config({}),
            TypeNameNode.of('a'),
            LiteralNode('a'),
            CallNode.of('a', []),

        ]
        for node in other_nodes:
            self.assertNotEqual(BinaryOpNode.of('|', LiteralNode.of(1), Identifier.of('a')), node)


class TestCallNode(unittest.TestCase):
    def test_equals_if_same_name_same_arguments(self):
        self.assertEqual(
            CallNode.of('a', [LiteralNode.of(1), Identifier.of('a')]),
            CallNode.of('a', [LiteralNode.of(1), Identifier.of('a')])
        )

    def test_not_equals_if_different_name(self):
        self.assertNotEqual(
            CallNode.of('a', [LiteralNode.of(1), Identifier.of('a')]),
            CallNode.of('b', [LiteralNode.of(1), Identifier.of('a')])
        )

    def test_not_equals_if_different_first_argument(self):
        self.assertNotEqual(
            CallNode.of('a', [LiteralNode.of(1), Identifier.of('a')]),
            CallNode.of('a', [LiteralNode.of(2), Identifier.of('a')])
        )

    def test_not_equals_if_different_second_argument(self):
        self.assertNotEqual(
            CallNode.of('a', [LiteralNode.of(1), Identifier.of('a')]),
            CallNode.of('a', [LiteralNode.of(1), Identifier.of('b')])
        )

    def test_not_equals_if_different_num_arguments(self):
        self.assertNotEqual(
            CallNode.of('a', [LiteralNode.of(1), Identifier.of('a')]),
            CallNode.of('a', [LiteralNode.of(1)])
        )

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(CallNode.of('a', [LiteralNode.of(1)]), 'a')
        self.assertNotEqual(CallNode.of('a', [LiteralNode.of(1)]), 1)

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('a'),
            ReferenceNode.of('a'),
            Config({}),
            TypeNameNode.of('a'),
            LiteralNode('a'),
            BinaryOpNode.of('a', LiteralNode.of(1), LiteralNode.of(2)),

        ]
        for node in other_nodes:
            self.assertNotEqual(CallNode.of('a', [LiteralNode.of(1)]), node)


class TestProjectionNode(unittest.TestCase):
    def test_equals_if_same_expr_same_indices(self):
        self.assertEqual(ProjectionNode.of(LiteralNode.of(1), 1, 2), ProjectionNode.of(LiteralNode.of(1), 1, 2))

    def test_not_equals_if_different_expr(self):
        self.assertNotEqual(ProjectionNode.of(LiteralNode.of(1), 1, 2), ProjectionNode.of(LiteralNode.of(2), 1, 2))

    def test_not_equals_if_different_indices(self):
        self.assertNotEqual(ProjectionNode.of(LiteralNode.of(1), 1, 2), ProjectionNode.of(LiteralNode.of(1), 1, 3))

    def test_not_equals_if_different_number_of_indices(self):
        self.assertNotEqual(ProjectionNode.of(LiteralNode.of(1), 1, 2), ProjectionNode.of(LiteralNode.of(1), 1))

    def test_not_equals_if_not_ast_node(self):
        self.assertNotEqual(ProjectionNode.of(LiteralNode.of(1), 1), 'a')
        self.assertNotEqual(ProjectionNode.of(LiteralNode.of(1), 1), 1)

    def test_not_equals_if_different_ast_node(self):
        other_nodes = [
            Identifier('1'),
            ReferenceNode.of('1'),
            Config({}),
            TypeNameNode.of('1'),
            LiteralNode(1),
            CallNode.of('1', [LiteralNode.of(1)]),
        ]
        for node in other_nodes:
            self.assertNotEqual(ProjectionNode.of(LiteralNode.of(1), 1), node)
