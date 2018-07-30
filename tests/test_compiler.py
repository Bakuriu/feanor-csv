import unittest

from feanor.dsl.ast import *
from feanor.dsl.compiler import *
from feanor.dsl.types import *


class TestGetType(unittest.TestCase):
    def test_can_get_the_type_of_a_type_name_node(self):
        got = get_type(TypeNameNode.of('int'))
        self.assertEqual(SimpleType('int', {}), got)

    def test_can_get_the_type_of_a_reference_node(self):
        expected_type = SimpleType('int', {})
        got = get_type(ReferenceNode.of('a'), {'a': expected_type})
        self.assertEqual(expected_type, got)

    def test_can_get_type_from_call(self):
        expected_type = SimpleType('int', {})
        arg_type = SimpleType('float', {})
        env = {'a': arg_type}
        got = get_type(CallNode.of('func', [ReferenceNode.of('a')]), env=env,
                       func_env={'func': ([arg_type], expected_type)})
        self.assertEqual(expected_type, got)

    def test_can_get_type_from_merge(self):
        got = get_type(BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('float')),
                       compatible=lambda x, y: True)
        expected_config = {'left_config': {}, 'right_config': {}}
        expected_type = MergeType([SimpleType('int', {}), SimpleType('float', {})], config=expected_config)
        self.assertEqual(expected_type, got)

    def test_can_get_type_from_choice(self):
        got = get_type(BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float')))
        expected_config = {'left_config': {}, 'right_config': {}}
        expected_type = ChoiceType([SimpleType('int', {}), SimpleType('float', {})], config=expected_config)
        self.assertEqual(expected_type, got)
        self.assertEqual(1, got.num_outputs)

    def test_can_get_type_from_parallel(self):
        got = get_type(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float')))
        expected_config = {'left_config': {}, 'right_config': {}}
        expected_type = ParallelType([SimpleType('int', {}), SimpleType('float', {})], config=expected_config)
        self.assertEqual(expected_type, got)
        self.assertEqual(2, got.num_outputs)

    def test_can_get_type_from_assignment(self):
        got = get_type(AssignNode.of(TypeNameNode.of('int'), 'a'))
        self.assertEqual(SimpleType('int', {}), got)

    def test_can_get_type_from_simple_projection(self):
        env = {'a': ParallelType([SimpleType('int'), SimpleType('float'), SimpleType('string')])}
        got = get_type(ProjectionNode.of(ReferenceNode.of('a'), 1), env=env)
        self.assertEqual(SimpleType('float'), got)

    def test_can_get_type_from_projection_with_multiple_indices(self):
        env = {'a': ParallelType([SimpleType('int'), SimpleType('float'), SimpleType('string')])}
        got = get_type(ProjectionNode.of(ReferenceNode.of('a'), 1, 2), env=env)
        self.assertEqual(ParallelType([SimpleType('float'), SimpleType('string')]), got)

    def test_can_get_type_of_merge_with_multiple_columns(self):
        left_expr = ReferenceNode.of('a')
        right_expr = ReferenceNode.of('b')
        left_ty = ParallelType([SimpleType('int'), SimpleType('float')])
        right_ty = ParallelType([SimpleType('int'), SimpleType('int')])
        env = {
            'a': left_ty,
            'b': right_ty,
        }
        got = get_type(BinaryOpNode.of('+', left_expr, right_expr), env=env, compatible=lambda x, y: True)
        expected_config = {'left_config': {}, 'right_config': {}}
        expected_type = MergeType([left_ty, right_ty], config=expected_config)
        self.assertEqual(expected_type, got)
        self.assertEqual(2, expected_type.num_outputs)

    def test_raises_error_when_merging_incompatible_types(self):
        with self.assertRaises(TypeError):
            get_type(BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('float')))

    def test_raises_error_when_merging_incompatible_types_with_more_columns(self):
        left_expr = ReferenceNode.of('a')
        right_expr = ReferenceNode.of('b')
        left_ty = ParallelType([SimpleType('int'), SimpleType('float')])
        right_ty = ParallelType([SimpleType('int'), SimpleType('int')])
        env = {
            'a': left_ty,
            'b': right_ty,
        }
        with self.assertRaises(TypeError):
            get_type(BinaryOpNode.of('+', left_expr, right_expr), env=env)


class TestDefaultCompatibility(unittest.TestCase):
    def test_identical_simple_types_are_compatible(self):
        self.assertTrue(default_compatibility(SimpleType('int'), SimpleType('int')))

    def test_composite_types_of_same_class_with_one_identical_type_are_compatible(self):
        for cls in (ChoiceType, MergeType, ParallelType):
            self.assertTrue(default_compatibility(cls([SimpleType('int')]), cls([SimpleType('int')])))

    def test_two_non_identical_simple_types_are_not_compatible(self):
        self.assertFalse(default_compatibility(SimpleType('int'), SimpleType('float')))

    def test_composite_types_of_same_class_with_one_different_type_are_not_compatible(self):
        for cls in (ChoiceType, MergeType, ParallelType):
            self.assertFalse(default_compatibility(cls([SimpleType('int')]), cls([SimpleType('float')])))

    def test_composite_types_of_different_class_with_one_identical_type_are_not_compatible(self):
        arg = SimpleType('int')
        for first in [ChoiceType, MergeType, ParallelType]:
            for second in [sec for sec in (ChoiceType, MergeType, ParallelType) if sec != first]:
                self.assertFalse(default_compatibility(first([arg]), second([arg])))

    def test_composite_types_with_multiple_incompatible_types_are_not_compatible(self):
        for cls in (ChoiceType, MergeType, ParallelType):
            self.assertFalse(default_compatibility(cls([SimpleType('int'), SimpleType('string')]),
                                                   cls([SimpleType('int'), SimpleType('not-string')])))
