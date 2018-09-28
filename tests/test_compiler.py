import unittest

from feanor.builtin import BuiltInLibrary
from feanor.dsl.ast import *
from feanor.dsl.compiler import *
from feanor.dsl.types import *
from feanor.library import MockLibrary
from feanor.schema import *


class TestTypeInferencer(unittest.TestCase):
    def setUp(self):
        self.library = BuiltInLibrary({}, random)
        self.inferencer = TypeInferencer(self.library.compatibility())

    def test_can_infer_type_of_a_type_name_node(self):
        got = self.inferencer.infer(TypeNameNode.of('int'))
        self.assertEqual(SimpleType('int'), got)

    def test_can_infer_type_of_a_type_name_node_with_producer(self):
        got = self.inferencer.infer(TypeNameNode.of('int', 'fixed'))
        self.assertEqual(SimpleType('int'), got)

    def test_inferring_type_of_type_name_node_sets_info_value(self):
        tree = TypeNameNode.of('int')
        self.inferencer.infer(tree)
        self.assertEqual({'type': SimpleType('int')}, tree.info)

    def test_inferring_type_of_type_name_node_with_producer_sets_info_value(self):
        tree = TypeNameNode.of('int', 'fixed')
        self.inferencer.infer(tree)
        self.assertEqual({'type': SimpleType('int')}, tree.info)

    def test_can_infer_type_of_a_reference_node(self):
        expected_type = SimpleType('int')
        inferencer = TypeInferencer(self.library.compatibility(), env={'a': expected_type})
        got = inferencer.infer(ReferenceNode.of('a'))
        self.assertEqual(expected_type, got)

    def test_inferring_type_of_reference_node_sets_info_value(self):
        expected_type = SimpleType('int')
        tree = ReferenceNode.of('a')
        inferencer = TypeInferencer(self.library.compatibility(), env={'a': expected_type})
        inferencer.infer(tree)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_call(self):
        expected_type = SimpleType('int')
        arg_type = SimpleType('float')
        env = {'a': arg_type}
        inferencer = TypeInferencer(self.library.compatibility(), env=env,
                                    func_env={'func': ([arg_type], expected_type)})
        got = inferencer.infer(CallNode.of('func', [ReferenceNode.of('a')]))
        self.assertEqual(expected_type, got)

    def test_inferring_type_of_call_node_sets_info_value(self):
        expected_type = SimpleType('int')
        arg_type = SimpleType('float')
        env = {'a': arg_type}
        arg_node = ReferenceNode.of('a')
        tree = CallNode.of('func', [arg_node])
        inferencer = TypeInferencer(self.library.compatibility(), env=env,
                                    func_env={'func': ([arg_type], expected_type)})
        inferencer.infer(tree)
        self.assertEqual({'type': arg_type}, arg_node.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_call_when_called_with_compatible_argument(self):
        expected_type = SimpleType('int')
        arg_type = SimpleType('float')
        env = {'a': SimpleType('int')}
        inferencer = TypeInferencer(self.library.compatibility(), env=env,
                                    func_env={'func': ([arg_type], expected_type)})
        got = inferencer.infer(CallNode.of('func', [ReferenceNode.of('a')]))
        self.assertEqual(expected_type, got)

    def test_can_infer_type_of_merge(self):
        inferencer = TypeInferencer(compatibility=SimpleCompatibility(upperbound=lambda x, y: y))
        got = inferencer.infer(BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('float')))
        expected_type = SimpleType('float')
        self.assertEqual(expected_type, got)

    def test_inferring_type_of_merge_sets_info_value(self):
        left_arg = TypeNameNode.of('int')
        right_arg = TypeNameNode.of('float')
        tree = BinaryOpNode.of('+', left_arg, right_arg)
        left_arg_type = SimpleType('int')
        right_arg_type = SimpleType('float')
        expected_type = SimpleType('float')
        inferencer = TypeInferencer(compatibility=SimpleCompatibility(lambda x, y: y))
        inferencer.infer(tree)
        self.assertEqual({'type': left_arg_type}, left_arg.info)
        self.assertEqual({'type': right_arg_type}, right_arg.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_choice(self):
        got = self.inferencer.infer(BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float')))
        expected_type = ChoiceType([SimpleType('int'), SimpleType('float')])
        self.assertEqual(expected_type, got)
        self.assertEqual(1, got.num_outputs)

    def test_inferring_type_of_choice_sets_info_value(self):
        left_arg = TypeNameNode.of('int')
        right_arg = TypeNameNode.of('float')
        tree = BinaryOpNode.of('|', left_arg, right_arg)
        left_arg_type = SimpleType('int')
        right_arg_type = SimpleType('float')
        expected_type = ChoiceType([left_arg_type, right_arg_type])
        inferencer = TypeInferencer(compatibility=lambda x, y: True)
        inferencer.infer(tree)
        self.assertEqual({'type': left_arg_type}, left_arg.info)
        self.assertEqual({'type': right_arg_type}, right_arg.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_nested_choice(self):
        left_inner_choice = BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('float'))
        right_inner_choice = BinaryOpNode.of('|', TypeNameNode.of('string'), TypeNameNode.of('float'))
        tree = BinaryOpNode.of('|', left_inner_choice, right_inner_choice)
        got = self.inferencer.infer(tree)
        expected_type = ChoiceType([SimpleType('int'), SimpleType('float'), SimpleType('string'), SimpleType('float')])
        self.assertEqual(expected_type, got)
        self.assertEqual(1, got.num_outputs)

    def test_inferring_type_of_nested_choice_sets_info_value(self):
        left_arg = TypeNameNode.of('int')
        right_arg = TypeNameNode.of('float')
        left_inner_choice = BinaryOpNode.of('|', left_arg, right_arg)
        left_arg_2 = TypeNameNode.of('string')
        right_arg_2 = TypeNameNode.of('float')
        right_inner_choice = BinaryOpNode.of('|', left_arg_2, right_arg_2)
        tree = BinaryOpNode.of('|', left_inner_choice, right_inner_choice)
        left_arg_type = SimpleType('int')
        right_arg_type = SimpleType('float')
        left_arg_type_2 = SimpleType('string')
        right_arg_type_2 = SimpleType('float')
        left_inner_choice_type = ChoiceType([left_arg_type, right_arg_type])
        right_inner_choice_type = ChoiceType([left_arg_type_2, right_arg_type_2])
        expected_type = ChoiceType([left_arg_type, right_arg_type, left_arg_type_2, right_arg_type_2])
        self.inferencer.infer(tree)
        self.assertEqual({'type': left_arg_type}, left_arg.info)
        self.assertEqual({'type': right_arg_type}, right_arg.info)
        self.assertEqual({'type': left_arg_type_2}, left_arg_2.info)
        self.assertEqual({'type': right_arg_type_2}, right_arg_2.info)
        self.assertEqual({'type': left_inner_choice_type}, left_inner_choice.info)
        self.assertEqual({'type': right_inner_choice_type}, right_inner_choice.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_concatenation(self):
        got = self.inferencer.infer(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float')))
        expected_type = ParallelType([SimpleType('int'), SimpleType('float')])
        self.assertEqual(expected_type, got)
        self.assertEqual(2, got.num_outputs)

    def test_inferring_type_of_concatenation_sets_info_value(self):
        left_arg = TypeNameNode.of('int')
        right_arg = TypeNameNode.of('float')
        tree = BinaryOpNode.of('.', left_arg, right_arg)
        left_arg_type = SimpleType('int')
        right_arg_type = SimpleType('float')
        expected_type = ParallelType([left_arg_type, right_arg_type])
        self.inferencer.infer(tree)
        self.assertEqual({'type': left_arg_type}, left_arg.info)
        self.assertEqual({'type': right_arg_type}, right_arg.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_assignment(self):
        got = self.inferencer.infer(AssignNode.of(TypeNameNode.of('int'), 'a'))
        self.assertEqual(SimpleType('int'), got)

    def test_inferring_type_of_assignment_sets_info_value(self):
        expr = TypeNameNode.of('int')
        tree = AssignNode.of(expr, 'a')
        self.inferencer.infer(tree)
        expected_type = SimpleType('int')
        self.assertEqual({'type': expected_type}, expr.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_simple_projection(self):
        env = {'a': ParallelType([SimpleType('int'), SimpleType('float'), SimpleType('string')])}
        inferencer = TypeInferencer(self.library.compatibility(), env=env)
        got = inferencer.infer(ProjectionNode.of(ReferenceNode.of('a'), 1))
        self.assertEqual(SimpleType('float'), got)

    def test_inferring_type_of_simple_projection_sets_info_value(self):
        expr_type = ParallelType([SimpleType('int'), SimpleType('float'), SimpleType('string')])
        env = {'a': expr_type}
        expr = ReferenceNode.of('a')
        tree = ProjectionNode.of(expr, 1)
        inferencer = TypeInferencer(self.library.compatibility(), env=env)
        inferencer.infer(tree)
        expected_type = SimpleType('float')
        self.assertEqual({'type': expr_type}, expr.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_projection_with_multiple_indices(self):
        env = {'a': ParallelType([SimpleType('int'), SimpleType('float'), SimpleType('string')])}
        inferencer = TypeInferencer(self.library.compatibility(), env=env)
        got = inferencer.infer(ProjectionNode.of(ReferenceNode.of('a'), 1, 2))
        self.assertEqual(ParallelType([SimpleType('float'), SimpleType('string')]), got)

    def test_inferring_type_of_projection_with_multiple_indices_sets_info_value(self):
        expr_type = ParallelType([SimpleType('int'), SimpleType('float'), SimpleType('string')])
        env = {'a': expr_type}
        expr = ReferenceNode.of('a')
        tree = ProjectionNode.of(expr, 1, 2)
        inferencer = TypeInferencer(self.library.compatibility(), env=env)
        inferencer.infer(tree)
        expected_type = ParallelType([SimpleType('float'), SimpleType('string')])
        self.assertEqual({'type': expr_type}, expr.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_merge_with_multiple_columns(self):
        left_inner_types = [SimpleType('int'), SimpleType('float')]
        left_ty = ParallelType(left_inner_types)
        right_inner_types = [SimpleType('int'), SimpleType('int')]
        right_ty = ParallelType(right_inner_types)
        env = {
            'a': left_ty,
            'b': right_ty,
        }
        left_expr = ReferenceNode.of('a')
        right_expr = ReferenceNode.of('b')
        inferencer = TypeInferencer(compatibility=SimpleCompatibility(lambda x, y: x), env=env)
        got = inferencer.infer(BinaryOpNode.of('+', left_expr, right_expr))
        expected_type = ParallelType([SimpleType('int'), SimpleType('float')])
        self.assertEqual(expected_type, got)
        self.assertEqual(2, expected_type.num_outputs)

    def test_inferring_type_of_merge_with_multiple_columns_sets_info_value(self):
        left_inner_types = [SimpleType('int'), SimpleType('float')]
        left_ty = ParallelType(left_inner_types)
        right_inner_types = [SimpleType('int'), SimpleType('int')]
        right_ty = ParallelType(right_inner_types)
        env = {
            'a': left_ty,
            'b': right_ty,
        }
        left_expr = ReferenceNode.of('a')
        right_expr = ReferenceNode.of('b')
        tree = BinaryOpNode.of('+', left_expr, right_expr)
        inferencer = TypeInferencer(compatibility=SimpleCompatibility(lambda x, y: x), env=env)
        inferencer.infer(tree)
        expected_type = ParallelType([SimpleType('int'), SimpleType('float')])
        self.assertEqual({'type': left_ty}, left_expr.info)
        self.assertEqual({'type': right_ty}, right_expr.info)
        self.assertEqual({'type': expected_type}, tree.info)

    def test_can_infer_type_of_let_expression(self):
        got = self.inferencer.infer(LetNode.of([('a', TypeNameNode.of('int'))], ReferenceNode.of('a')))
        self.assertEqual(SimpleType('int'), got)

    def test_inferring_type_of_let_expression_sets_info_value(self):
        assignment = AssignNode.of(TypeNameNode.of('int'), 'a')
        reference = ReferenceNode.of('a')
        tree = LetNode([assignment], reference)
        self.inferencer.infer(tree)
        self.assertEqual({'type': SimpleType('int')}, assignment.info)
        self.assertEqual({'type': SimpleType('int')}, reference.info)
        self.assertEqual({'type': SimpleType('int')}, tree.info)

    def test_can_infer_type_of_simple_expr(self):
        got = self.inferencer.infer(SimpleExprNode.of(LiteralNode.of(10)))
        self.assertEqual(SimpleType('int'), got)

    def test_inferring_type_of_simple_expr_sets_info_value(self):
        literal = LiteralNode.of(10)
        tree = SimpleExprNode.of(literal)
        self.inferencer.infer(tree)
        self.assertEqual({'type': SimpleType('int')}, literal.info)
        self.assertEqual({'type': SimpleType('int')}, tree.info)

    def test_can_infer_type_of_simple_expr_with_list(self):
        got = self.inferencer.infer(SimpleExprNode.of(LiteralNode.of([1,2,3])))
        self.assertEqual(ParallelType(3*[SimpleType('int')]), got)

    def test_inferring_type_of_simple_expr_with_list_sets_info_value(self):
        literal = LiteralNode.of([1, 2, 3])
        tree = SimpleExprNode.of(literal)
        self.inferencer.infer(tree)
        self.assertEqual({'type': ParallelType(3*[SimpleType('int')])}, literal.info)
        self.assertEqual({'type': ParallelType(3*[SimpleType('int')])}, tree.info)

    def test_can_infer_type_of_simple_expr_with_string(self):
        got = self.inferencer.infer(SimpleExprNode.of(LiteralNode.of("ciao")))
        self.assertEqual(SimpleType('string'), got)

    def test_inferring_type_of_simple_expr_with_string_sets_info_value(self):
        literal = LiteralNode.of("ciao")
        tree = SimpleExprNode.of(literal)
        self.inferencer.infer(tree)
        self.assertEqual({'type': SimpleType('string')}, literal.info)
        self.assertEqual({'type': SimpleType('string')}, tree.info)

    def test_raises_error_when_merging_incompatible_types(self):
        with self.assertRaises(TypeError):
            self.inferencer.infer(BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('string')))

    def test_raises_error_when_merging_incompatible_types_with_more_columns(self):
        left_expr = ReferenceNode.of('a')
        right_expr = ReferenceNode.of('b')
        left_ty = ParallelType([SimpleType('int'), SimpleType('string')])
        right_ty = ParallelType([SimpleType('int'), SimpleType('int')])
        env = {
            'a': left_ty,
            'b': right_ty,
        }
        with self.assertRaises(TypeError):
            inferencer = TypeInferencer(self.library.compatibility(), env=env)
            inferencer.infer(BinaryOpNode.of('+', left_expr, right_expr))

    def test_raises_error_when_reassigning_same_name(self):
        # assign inside assign
        with self.assertRaises(TypeError):
            inferencer = TypeInferencer(self.library.compatibility())
            inferencer.infer(AssignNode.of(AssignNode.of(TypeNameNode.of('int'), 'a'), 'a'))
        # let inside assign
        with self.assertRaises(TypeError):
            inferencer = TypeInferencer(self.library.compatibility())
            inferencer.infer(AssignNode.of(LetNode.of([('a', TypeNameNode.of('int'))], TypeNameNode.of('int')), 'a'))
        # assign inside let
        with self.assertRaises(TypeError):
            inferencer = TypeInferencer(self.library.compatibility())
            inferencer.infer(LetNode.of([('a', AssignNode.of(TypeNameNode.of('int'), 'a'))], TypeNameNode.of('int')))
        # let inside let
        with self.assertRaises(TypeError):
            inferencer = TypeInferencer(self.library.compatibility())
            inferencer.infer(LetNode.of([('a', LetNode.of([('a', TypeNameNode.of('int'))], TypeNameNode.of('float')))],
                                        TypeNameNode.of('int')))

    def test_raises_error_if_projecting_on_a_non_composite_node(self):
        with self.assertRaises(TypeError):
            self.inferencer.infer(ProjectionNode.of(TypeNameNode.of('int'), (0, 1)))

    def test_raises_error_if_projecting_indices_outside_output_dimension(self):
        with self.assertRaises(TypeError) as ctx:
            self.inferencer.infer(
                ProjectionNode.of(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int')), 2))
        self.assertEqual('Indices out of range for projection', str(ctx.exception))

    def test_raises_error_if_function_called_with_incorrect_number_of_arguments(self):
        with self.assertRaises(TypeError) as ctx:
            inferencer = TypeInferencer(self.library.compatibility(),
                                        func_env={'ciao': ([SimpleType('int')], SimpleType('int'))})
            inferencer.infer(CallNode.of('ciao', [TypeNameNode.of('int'), TypeNameNode.of('float')]))
        self.assertEqual('Incorrect number of arguments to function ciao: 2 instead of 1', str(ctx.exception))

    def test_raises_error_if_function_called_with_unassignable_argument_type(self):
        # FIXME: compatibility is symmetric. So here we have no way of properly type checking a function call
        with self.assertRaises(TypeError) as ctx:
            inferencer = TypeInferencer(self.library.compatibility(),
                                        func_env={'ciao': ([SimpleType('int')], SimpleType('int'))})
            inferencer.infer(CallNode.of('ciao', [TypeNameNode.of('float')]))
        self.assertEqual('Incompatible types for argument 0 of ciao: float instead of int', str(ctx.exception))

    def test_raises_error_if_function_called_with_incompatible_argument_type(self):
        with self.assertRaises(TypeError) as ctx:
            inferencer = TypeInferencer(self.library.compatibility(),
                                        func_env={'ciao': ([SimpleType('int')], SimpleType('int'))})
            inferencer.infer(CallNode.of('ciao', [TypeNameNode.of('string')]))
        self.assertEqual('Incompatible types for argument 0 of ciao: string instead of int', str(ctx.exception))

    def test_raises_error_if_function_called_does_not_exist(self):
        with self.assertRaises(ValueError) as ctx:
            inferencer = TypeInferencer(self.library.compatibility())
            inferencer.infer(CallNode.of('ciao', [TypeNameNode.of('string')]))
        self.assertEqual("Unknown function 'ciao'", str(ctx.exception))

    def test_raises_error_if_merge_on_incompatible_parallel_types(self):
        with self.assertRaises(TypeError) as ctx:
            inferencer = TypeInferencer(self.library.compatibility(),
                                        env={
                                            'a': ParallelType([SimpleType('int')]),
                                            'b': ParallelType([SimpleType('string')])
                                        })
            inferencer.infer(BinaryOpNode.of('+', ReferenceNode.of('a'), ReferenceNode.of('b')))
        self.assertEqual("Incompatible types for merge: Parallel(int) and Parallel(string)", str(ctx.exception))

    def test_raises_error_if_merge_on_incompatible_types(self):
        with self.assertRaises(TypeError) as ctx:
            inferencer = TypeInferencer(self.library.compatibility(),
                                        env={'a': ParallelType([SimpleType('int')]), 'b': SimpleType('float')})
            inferencer.infer(BinaryOpNode.of('+', ReferenceNode.of('a'), ReferenceNode.of('b')))
        self.assertEqual("Incompatible types for merge: Parallel(int) and float", str(ctx.exception))

    def test_raises_error_if_trying_to_infer_type_of_literal_outside_simple_expr(self):
        with self.assertRaises(TypeError) as ctx:
            self.inferencer.infer(LiteralNode.of(5))
        self.assertEqual("This expression can only appear inside a simple expression: 5", str(ctx.exception))


class TestPairBasedCompatibility(unittest.TestCase):
    def _make_compat(self, pairs):
        compat = PairBasedCompatibility()
        compat.add_upperbounds(pairs)
        return compat

    def test_simple_type_is_assignable_to_itself_always(self):
        compatibility = self._make_compat(set())
        self.assertTrue(compatibility.is_assignable_to(SimpleType('int'), SimpleType('int')))

    def test_simple_type_is_not_compatible_to_itself_if_not_provided(self):
        compatibility = self._make_compat(set())
        self.assertFalse(compatibility.is_compatible(SimpleType('int'), SimpleType('int')))

    def test_simple_type_is_compatible_with_itself_if_provided(self):
        compatibility = self._make_compat({('int', 'int')})
        self.assertTrue(compatibility.is_compatible(SimpleType('int'), SimpleType('int')))

    def test_simple_type_is_compatible_with_other_type_if_provided(self):
        compatibility = self._make_compat({('int', 'float')})
        self.assertTrue(compatibility.is_compatible(SimpleType('int'), SimpleType('float')))
        self.assertTrue(compatibility.is_compatible(SimpleType('float'), SimpleType('int')))

    def test_simple_type_is_assignable_to_other_type_if_provided(self):
        compatibility = self._make_compat({('int', 'float')})
        self.assertTrue(compatibility.is_assignable_to(SimpleType('int'), SimpleType('float')))

    def test_simple_type_is_not_assignable_to_a_lowerbound(self):
        compatibility = self._make_compat({('int', 'float')})
        self.assertFalse(compatibility.is_assignable_to(SimpleType('float'), SimpleType('int')))

    def test_parallel_type_type_is_assignable_to_itself_always(self):
        compatibility = self._make_compat(set())
        left = ParallelType([SimpleType('int'), SimpleType('float')])
        right = ParallelType([SimpleType('int'), SimpleType('float')])
        self.assertTrue(compatibility.is_assignable_to(left, right))

    def test_parallel_type_type_is_not_compatible_to_itself_if_not_provided(self):
        compatibility = self._make_compat(set())
        left = ParallelType([SimpleType('int'), SimpleType('float')])
        right = ParallelType([SimpleType('int'), SimpleType('float')])
        self.assertFalse(compatibility.is_compatible(left, right))

    def test_parallel_type_type_is_compatible_with_itself_if_provided(self):
        compatibility = self._make_compat({('int', 'int'), ('float', 'float')})
        left = ParallelType([SimpleType('int'), SimpleType('float')])
        right = ParallelType([SimpleType('int'), SimpleType('float')])
        self.assertTrue(compatibility.is_compatible(left, right))

    def test_parallel_type_type_is_compatible_with_other_type_if_provided(self):
        compatibility = self._make_compat({('int', 'float', 'string')})
        left = ParallelType([SimpleType('int'), SimpleType('float')])
        right = ParallelType([SimpleType('float'), SimpleType('string')])
        self.assertTrue(compatibility.is_compatible(left, right))
        self.assertTrue(compatibility.is_compatible(right, left))

    def test_parallel_type_type_is_assignable_to_other_type_if_provided(self):
        compatibility = self._make_compat({('int', 'float', 'float')})
        left = ParallelType([SimpleType('int'), SimpleType('float')])
        right = ParallelType([SimpleType('float'), SimpleType('float')])
        self.assertTrue(compatibility.is_assignable_to(left, right))

    def test_parallel_type_type_is_not_assignable_to_a_lowerbound(self):
        compatibility = self._make_compat({('int', 'float', 'float')})
        left = ParallelType([SimpleType('int'), SimpleType('float')])
        right = ParallelType([SimpleType('float'), SimpleType('float')])
        self.assertFalse(compatibility.is_assignable_to(right, left))

    def test_choice_type_type_is_assignable_to_itself_always(self):
        compatibility = self._make_compat(set())
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = ChoiceType([SimpleType('int'), SimpleType('float')])
        self.assertTrue(compatibility.is_assignable_to(left, right))

    def test_choice_type_type_is_not_compatible_to_itself_if_not_provided(self):
        compatibility = self._make_compat(set())
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = ChoiceType([SimpleType('int'), SimpleType('float')])
        self.assertFalse(compatibility.is_compatible(left, right))

    def test_choice_type_type_is_not_compatible_with_itself_if_provided_only_self_compatibilities(self):
        compatibility = self._make_compat({('int', 'int'), ('float', 'float')})
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = ChoiceType([SimpleType('int'), SimpleType('float')])
        self.assertFalse(compatibility.is_compatible(left, right))

    def test_choice_type_type_is_compatible_with_itself_if_provided_all_pairs(self):
        compatibility = self._make_compat({('int', 'int', 'float', 'float')})
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = ChoiceType([SimpleType('int'), SimpleType('float')])
        self.assertTrue(compatibility.is_compatible(left, right))

    def test_choice_type_type_is_compatible_with_other_type_if_provided_all_pairs(self):
        compatibility = self._make_compat({('int', 'float', 'float', 'string', 'string')})
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = SimpleType('string')
        self.assertTrue(compatibility.is_compatible(left, right))
        self.assertTrue(compatibility.is_compatible(right, left))

    def test_choice_type_type_is_not_compatible_with_other_type_if_provided_only_some_pairs(self):
        compatibility = self._make_compat({('int', 'float'), ('float', 'string')})
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = SimpleType('string')
        self.assertFalse(compatibility.is_compatible(left, right))
        self.assertFalse(compatibility.is_compatible(right, left))

    def test_choice_type_type_is_assignable_to_other_type_if_provided(self):
        compatibility = self._make_compat({('int', 'float', 'float')})
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = ChoiceType([SimpleType('float'), SimpleType('float')])
        self.assertTrue(compatibility.is_assignable_to(left, right))

    def test_choice_type_type_is_not_assignable_to_a_lowerbound(self):
        compatibility = self._make_compat({('int', 'float', 'float')})
        left = ChoiceType([SimpleType('int'), SimpleType('float')])
        right = ChoiceType([SimpleType('float'), SimpleType('float')])
        self.assertFalse(compatibility.is_assignable_to(right, left))

    def test_parallel_type_can_be_compatible_with_choice_type(self):
        compatibility = self._make_compat({('int', 'int', 'float', 'float')})
        left_type = ChoiceType([ParallelType(2 * [SimpleType('int')]), ParallelType(2 * [SimpleType('float')])])
        right_type = ParallelType(2 * [SimpleType('float')])
        self.assertTrue(compatibility.is_compatible(left_type, right_type))
        self.assertTrue(compatibility.is_compatible(right_type, left_type))

    def test_simple_is_compatible_with_choice_type(self):
        compatibility = self._make_compat({('int', 'int', 'float', 'float')})
        left_type = SimpleType('int')
        right_type = ChoiceType([SimpleType('int'), SimpleType('float')])
        self.assertTrue(compatibility.is_compatible(left_type, right_type))
        self.assertTrue(compatibility.is_compatible(right_type, left_type))

    def test_any_type_is_compatible_with_anything(self):
        compatibility = self._make_compat(set())
        self.assertTrue(compatibility.is_compatible(AnyType(), SimpleType('int')))
        self.assertTrue(compatibility.is_compatible(SimpleType('int'), AnyType()))

    def test_can_assign_anything_to_any_type(self):
        compatibility = self._make_compat(set())
        self.assertTrue(compatibility.is_assignable_to(SimpleType('int'), AnyType()))

    def test_any_type_cannot_be_assigned_to_int(self):
        compatibility = self._make_compat(set())
        self.assertFalse(compatibility.is_assignable_to(AnyType(), SimpleType('int')))

    def test_any_type_can_be_assigned_to_any_type(self):
        compatibility = self._make_compat(set())
        self.assertTrue(compatibility.is_assignable_to(AnyType(), AnyType()))


class TestDefaultCompatibility(unittest.TestCase):
    def setUp(self):
        self.compatibility = BuiltInLibrary({}, random).compatibility()
        self.compatibility.add_upperbounds({('int', 'int'), ('float', 'float')})

    def test_identical_simple_types_are_compatible(self):
        self.assertTrue(self.compatibility.is_compatible(SimpleType('int'), SimpleType('int')))

    def test_composite_types_of_same_class_with_one_identical_type_are_compatible(self):
        for cls in (ChoiceType, ParallelType):
            self.assertTrue(
                self.compatibility.is_compatible(cls(2 * [SimpleType('int')]), cls(2 * [SimpleType('int')])))

    def test_two_non_compatible_simple_types_are_not_compatible(self):
        self.assertFalse(self.compatibility.is_compatible(SimpleType('int'), SimpleType('string')))

    def test_two_different_compatible_simple_types_are_compatible(self):
        self.assertTrue(self.compatibility.is_compatible(SimpleType('int'), SimpleType('float')))

    def test_composite_types_of_same_class_with_one_different_compatible_type_are_compatible(self):
        for cls in (ChoiceType, ParallelType):
            self.assertTrue(
                self.compatibility.is_compatible(cls([SimpleType('int')] * 2), cls([SimpleType('float')] * 2)))

    def test_composite_types_of_same_class_with_one_different_non_compatible_type_are_not_compatible(self):
        for cls in (ChoiceType, ParallelType):
            self.assertFalse(
                self.compatibility.is_compatible(cls([SimpleType('int')] * 2), cls([SimpleType('string')] * 2)))

    def test_composite_types_of_different_class_with_one_identical_type_are_not_compatible(self):
        arg = SimpleType('int')
        for first in [ChoiceType, ParallelType]:
            for second in [sec for sec in (ChoiceType, ParallelType) if sec != first]:
                self.assertFalse(self.compatibility.is_compatible(first([arg, arg]), second([arg, arg])))

    def test_composite_types_with_multiple_incompatible_types_are_not_compatible(self):
        for cls in (ChoiceType, ParallelType):
            self.assertFalse(self.compatibility.is_compatible(cls([SimpleType('int'), SimpleType('string')]),
                                                              cls([SimpleType('int'), SimpleType('not-string')])))

    def test_parallel_type_with_one_dimension_is_compatible_with_simple_type(self):
        self.assertTrue(self.compatibility.is_compatible(ParallelType([SimpleType('int')]), SimpleType('int')))
        # symmetric case:
        self.assertTrue(self.compatibility.is_compatible(SimpleType('int'), ParallelType([SimpleType('int')])))

    def test_parallel_type_with_more_than_one_dimension_is_not_compatible_with_simple_type(self):
        self.assertFalse(self.compatibility.is_compatible(ParallelType([SimpleType('int')] * 2), SimpleType('int')))
        # symmetric case:
        self.assertFalse(self.compatibility.is_compatible(SimpleType('int'), ParallelType([SimpleType('int')] * 2)))

    def test_choice_type_with_one_dimension_is_compatible_with_simple_type(self):
        self.assertTrue(self.compatibility.is_compatible(ChoiceType([SimpleType('int')]), SimpleType('int')))
        # symmetric case:
        self.assertTrue(self.compatibility.is_compatible(SimpleType('int'), ChoiceType(2 * [SimpleType('int')])))

    def test_choice_type_with_more_than_one_dimension_is_not_compatible_with_simple_type(self):
        self.assertFalse(
            self.compatibility.is_compatible(ChoiceType([ParallelType(2 * [SimpleType('int')])]), SimpleType('int')))
        # symmetric case:
        self.assertFalse(
            self.compatibility.is_compatible(SimpleType('int'), ChoiceType([ParallelType(2 * [SimpleType('int')])])))


class TestCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = Compiler(MockLibrary())

    def test_can_compile_a_type_name_node_with_no_config(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(TypeNameNode.of('int'))
        self.assertEqual(schema, got)

    def test_compiling_a_type_name_node_with_no_config_sets_info_value(self):
        tree = TypeNameNode.of('int')
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': None,
            'in_names': [],
            'out_names': ['producer#0'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_a_type_name_node_with_producer_no_config(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='fixed')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(TypeNameNode.of('int', 'fixed'))
        self.assertEqual(schema, got)

    def test_compiling_a_type_name_node_with_producer_no_config_sets_info_value(self):
        tree = TypeNameNode.of('int', 'fixed')
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': None,
            'in_names': [],
            'out_names': ['producer#0'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_a_type_name_node_with_config(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='int', config={'min': 10})
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(TypeNameNode.of('int', config={'min': 10}))
        self.assertEqual(schema, got)

    def test_compiling_a_type_name_node_with_config_sets_info_value(self):
        tree = TypeNameNode.of('int', config={'min': 10})
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': None,
            'in_names': [],
            'out_names': ['producer#0'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_a_type_name_node_with_producer_config(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='fixed', config={'value': 10})
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(TypeNameNode.of('int', 'fixed', config={'value': 10}))
        self.assertEqual(schema, got)

    def test_compiling_a_type_name_node_with_producer_config_sets_info_value(self):
        tree = TypeNameNode.of('int', 'fixed', config={'value': 10})
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': None,
            'in_names': [],
            'out_names': ['producer#0'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_an_assignment_of_a_type_name(self):
        schema = Schema()
        schema.add_column('a')
        schema.add_producer('producer#0', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(AssignNode.of(TypeNameNode.of('int'), 'a'))
        self.assertEqual(schema, got)

    def test_compiling_an_assignment_of_a_type_name_sets_info_value(self):
        tree = AssignNode.of(TypeNameNode.of('int'), 'a')
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': 'a',
            'in_names': ['producer#0'],
            'out_names': ['a'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_concatenation_of_two_type_names(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_column('column#1')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#1'], outputs=['column#1'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int')))
        self.assertEqual(schema, got)

    def test_compiling_concatenation_of_two_type_names_sets_info_value(self):
        tree = BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int'))
        self.compiler.compile(tree)
        expected_info = {
            'type': ParallelType([SimpleType('int'), SimpleType('int')]), 'assigned_name': None,
            'in_names': ['producer#0', 'producer#1'],
            'out_names': ['producer#0', 'producer#1'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_choice_of_two_type_names(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0', 'producer#1'], outputs=['transformer#0'],
                               transformer=ChoiceTransformer(2, 0.5, 0.5))
        schema.add_transformer('transformer#1', inputs=['transformer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('int')))
        self.assertEqual(schema, got)

    def test_compiling_choice_of_two_type_names_sets_info_value(self):
        tree = BinaryOpNode.of('|', TypeNameNode.of('int'), TypeNameNode.of('int'))
        self.compiler.compile(tree)
        expected_info = {
            'type': ChoiceType([SimpleType('int'), SimpleType('int')]), 'assigned_name': None,
            'out_names': ['transformer#0'],
            'in_names': ['producer#0', 'producer#1'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_merge_of_two_type_names(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0', 'producer#1'],
                               outputs=['transformer#0#0'],
                               transformer=MergeTransformer(2))
        schema.add_transformer('transformer#1', inputs=['transformer#0#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('int')))
        self.assertEqual(schema, got)

    def test_compiling_merge_of_two_type_names_sets_info_value(self):
        tree = BinaryOpNode.of('+', TypeNameNode.of('int'), TypeNameNode.of('int'))
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': None,
            'in_names': ['producer#0', 'producer#1'],
            'out_names': ['transformer#0#0'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_reference(self):
        schema = Schema()
        schema.add_column('a')
        schema.add_column('column#1')
        schema.add_producer('producer#0', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#0'], outputs=['column#1'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(
            BinaryOpNode.of(
                '.',
                AssignNode.of(TypeNameNode.of('int'), 'a'),
                ReferenceNode.of('a')
            )
        )
        self.assertEqual(schema, got)

    def test_compiling_reference_sets_info_value(self):
        tree = BinaryOpNode.of('.', AssignNode.of(TypeNameNode.of('int'), 'a'), ReferenceNode.of('a'))
        self.compiler.compile(tree)
        expected_info = {
            'type': ParallelType([SimpleType('int'), SimpleType('int')]),
            'in_names': ['a', 'producer#0'],
            'out_names': ['a', 'producer#0'],
            'assigned_name': None,
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_with_two_references_same_values(self):
        schema = Schema()
        schema.add_column('a')
        schema.add_column('column#1')
        schema.add_column('column#2')
        schema.add_producer('producer#0', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#0'], outputs=['column#1'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#2', inputs=['producer#0'], outputs=['column#2'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(
            BinaryOpNode.of(
                '.',
                AssignNode.of(TypeNameNode.of('int'), 'a'),
                BinaryOpNode.of(
                    '.',
                    ReferenceNode.of('a'),
                    ReferenceNode.of('a')
                )
            ))
        self.assertEqual(schema, got)

    def test_compiling_with_two_references_same_values_sets_info_value(self):
        tree = BinaryOpNode.of(
            '.',
            AssignNode.of(TypeNameNode.of('int'), 'a'),
            BinaryOpNode.of(
                '.',
                ReferenceNode.of('a'),
                ReferenceNode.of('a'),
            )
        )
        self.compiler.compile(tree)
        expected_info = {
            'type': ParallelType([SimpleType('int'), SimpleType('int'), SimpleType('int')]),
            'assigned_name': None,
            'in_names': ['a', 'producer#0', 'producer#0'],
            'out_names': ['a', 'producer#0', 'producer#0'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_an_assignment_of_two_type_names(self):
        schema = Schema()
        schema.add_column('a#0')
        schema.add_column('a#1')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='float')
        schema.add_transformer('transformer#0', inputs=['producer#0', 'producer#1'], outputs=['a#0', 'a#1'],
                               transformer=IdentityTransformer(2))
        got = self.compiler.compile(
            AssignNode.of(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float')), 'a'))
        self.assertEqual(schema, got)

    def test_compiling_an_assignment_of_two_type_names_sets_info_value(self):
        tree = AssignNode.of(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float')), 'a')
        self.compiler.compile(tree)
        expected_info = {
            'type': ParallelType([SimpleType('int'), SimpleType('float')]),
            'assigned_name': 'a',
            'in_names': ['producer#0', 'producer#1'],
            'out_names': ['a#0', 'a#1'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_projection_of_concatenation(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='float')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(
            ProjectionNode.of(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float')), 0))
        self.assertEqual(schema, got)

    def test_compiling_projection_of_concatenation_sets_info_values(self):
        tree = ProjectionNode.of(BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float')), 0)
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': None,
            'in_names': ['producer#0', 'producer#1'],
            'out_names': ['producer#0'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_double_assignment(self):
        schema = Schema()
        schema.add_column('b')
        schema.add_producer('producer#0', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['a'], outputs=['b'], transformer=IdentityTransformer(1))
        got = self.compiler.compile(AssignNode.of(AssignNode.of(TypeNameNode.of('int'), 'a'), 'b'))
        self.assertEqual(schema, got)

    def test_compiling_double_assignment_sets_info_value(self):
        tree = AssignNode.of(AssignNode.of(TypeNameNode.of('int'), 'a'), 'b')
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': 'b',
            'in_names': ['a'],
            'out_names': ['b'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_triple_assignment(self):
        schema = Schema()
        schema.add_column('c')
        schema.add_producer('producer#0', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['a'], outputs=['b'], transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#2', inputs=['b'], outputs=['c'], transformer=IdentityTransformer(1))
        got = self.compiler.compile(AssignNode.of(AssignNode.of(AssignNode.of(TypeNameNode.of('int'), 'a'), 'b'), 'c'))
        self.assertEqual(schema, got)

    def test_compiling_triple_assignment_sets_info_value(self):
        tree = AssignNode.of(AssignNode.of(AssignNode.of(TypeNameNode.of('int'), 'a'), 'b'), 'c')
        self.compiler.compile(tree)
        expected_info = {
            'type': SimpleType('int'),
            'assigned_name': 'c',
            'in_names': ['b'],
            'out_names': ['c'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_concatenation_with_assignment_inside(self):
        schema = Schema()
        schema.add_column('a')
        schema.add_column('column#1')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='float')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#1'], outputs=['column#1'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(
            BinaryOpNode.of('.', AssignNode.of(TypeNameNode.of('int'), 'a'), TypeNameNode.of('float')))
        self.assertEqual(schema, got)

    def test_compiling_concatenation_with_assignment_inside_sets_info_value(self):
        tree = BinaryOpNode.of('.', AssignNode.of(TypeNameNode.of('int'), 'a'), TypeNameNode.of('float'))
        self.compiler.compile(tree)
        expected_info = {
            'type': ParallelType([SimpleType('int'), SimpleType('float')]),
            'assigned_name': None,
            'in_names': ['a', 'producer#1'],
            'out_names': ['a', 'producer#1'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_concatenation_with_assignment_inside_on_concat(self):
        schema = Schema()
        schema.add_column('a#0')
        schema.add_column('a#1')
        schema.add_column('column#2')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='int')
        schema.add_producer('producer#2', type='float')
        schema.add_transformer('transformer#0', inputs=['producer#0', 'producer#1'], outputs=['a#0', 'a#1'],
                               transformer=IdentityTransformer(2))
        schema.add_transformer('transformer#1', inputs=['producer#2'], outputs=['column#2'],
                               transformer=IdentityTransformer(1))
        got = self.compiler.compile(BinaryOpNode.of('.', AssignNode.of(
            BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int')), 'a'), TypeNameNode.of('float')))
        self.assertEqual(schema, got)

    def test_compiling_concatenation_with_assignment_inside_on_concat_sets_info_value(self):
        tree = BinaryOpNode.of('.', AssignNode.of(
            BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int')), 'a'), TypeNameNode.of('float'))
        self.compiler.compile(tree)
        expected_info = {
            'type': ParallelType([SimpleType('int'), SimpleType('int'), SimpleType('float')]),
            'assigned_name': None,
            'in_names': ['a#0', 'a#1', 'producer#2'],
            'out_names': ['a#0', 'a#1', 'producer#2'],
        }
        self.assertEqual(expected_info, tree.info)

    def test_can_compile_simple_let_expression(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='int')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))

        got = self.compiler.compile(LetNode.of([('a', TypeNameNode.of('int'))], ReferenceNode.of('a')))
        self.assertEqual(schema, got)

    def test_can_compile_expression_with_type_config(self):
        schema = Schema()
        schema.add_column('column#0')
        schema.add_producer('producer#0', type='int', config={'min': 10})
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#0'], outputs=['column#0'],
                               transformer=IdentityTransformer(1))

        got = self.compiler.compile(
            LetNode.of([('a', TypeNameNode.of('int', config={'min': 10}))], ReferenceNode.of('a')))
        self.assertEqual(schema, got)

    def test_when_compiling_multiple_expressions_number_of_outputs_per_expression_is_taken_into_account(self):
        schema = Schema()
        schema.add_column('INTERO')
        schema.add_column('FLOAT')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='float')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['INTERO'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#1'], outputs=['FLOAT'],
                               transformer=IdentityTransformer(1))

        expr = BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('float'))
        got = self.compiler.compile(expr, column_names=['INTERO', 'FLOAT'])
        self.assertEqual(schema, got)

    def test_when_providing_less_than_the_number_of_columns_values_are_selected(self):
        schema = Schema()
        schema.add_column('a')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='float')
        schema.add_transformer('transformer#0', inputs=['producer#1'], outputs=['a'],
                               transformer=IdentityTransformer(1))

        expr = BinaryOpNode.of('.', TypeNameNode.of('int'), AssignNode.of(TypeNameNode.of('float'), 'a'))
        got = self.compiler.compile(expr, column_names=['a'])
        self.assertEqual(schema, got)

    def test_can_compile_call_node(self):
        library = MockLibrary()
        func = lambda x: x
        library.register_function('ciao', func, [SimpleType('string')], SimpleType('string'))
        compiler = Compiler(library)

        schema = Schema()
        schema.add_column('a')
        schema.add_producer('producer#0', type='string')
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['transformer#0'], transformer=FunctionalTransformer(func))
        schema.add_transformer('transformer#1', inputs=['transformer#0'], outputs=['a'], transformer=IdentityTransformer(1))

        expr = CallNode.of('ciao', [TypeNameNode.of('string')])
        got = compiler.compile(expr, column_names=['a'])
        self.assertEqual(schema, got)

    def test_can_compile_a_simple_expression(self):
        schema = Schema()
        schema.add_column('a')
        schema.add_producer('producer#0', type='fixed', config={'value': 5})
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'], transformer=IdentityTransformer(1))
        expr = SimpleExprNode.of(LiteralNode.of(5))
        got = self.compiler.compile(expr, column_names=['a'])
        self.assertEqual(schema, got)

    def test_can_compile_a_reference_to_an_env_var(self):
        library = MockLibrary()
        library.register_variable('ciao', 5, SimpleType('int'))
        compiler = Compiler(library)

        schema = Schema()
        schema.add_column('a')
        schema.add_producer('producer#0', type='fixed', config={'value': 5})
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'], transformer=IdentityTransformer(1))

        expr = ReferenceNode.of('ciao')
        got = compiler.compile(expr, column_names=['a'])
        self.assertEqual(schema, got)

    def test_multiple_references_to_env_var_do_not_create_more_producers(self):
        library = MockLibrary()
        library.register_variable('ciao', 5, SimpleType('int'))
        compiler = Compiler(library)

        schema = Schema()
        schema.add_column('a')
        schema.add_column('b')
        schema.add_producer('producer#0', type='fixed', config={'value': 5})
        schema.add_transformer('transformer#0', inputs=['producer#0'], outputs=['a'], transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#0'], outputs=['b'], transformer=IdentityTransformer(1))

        expr = BinaryOpNode.of('.', ReferenceNode.of('ciao'), ReferenceNode.of('ciao'))
        got = compiler.compile(expr, column_names=['a', 'b'])
        self.assertEqual(schema, got)

    def test_example_with_merge(self):
        schema = Schema()
        schema.add_column('transformer#1#0')
        schema.add_producer('producer#0', type='int')
        schema.add_producer('producer#1', type='int')
        schema.add_producer('producer#2', type='float')
        schema.add_transformer('transformer#0', inputs=['producer#1'], outputs=['a'],
                               transformer=IdentityTransformer(1))
        schema.add_transformer('transformer#1', inputs=['producer#0', 'a'], outputs=['transformer#1#0'],
                               transformer=MergeTransformer(2))

        expr = BinaryOpNode.of('.',
                               BinaryOpNode.of('+', TypeNameNode.of('int'), AssignNode.of(TypeNameNode.of('int'), 'a')),
                               TypeNameNode.of('float'))
        got = self.compiler.compile(expr, column_names=['transformer#1#0'])
        self.assertEqual(schema, got)

    def test_example_with_merge_incompatible_num_of_outputs(self):
        expr = BinaryOpNode.of(
            '+',
            TypeNameNode.of('int'),
            BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int'))
        )
        with self.assertRaises(TypeError):
            self.compiler.compile(expr, column_names=['transformer#1#0'])

    def test_example_with_merge_incompatible_num_of_outputs_more_outputs(self):
        expr = BinaryOpNode.of(
            '+',
            BinaryOpNode.of('.', TypeNameNode.of('int'), BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int'))),
            BinaryOpNode.of('.', TypeNameNode.of('int'), TypeNameNode.of('int'))
        )
        with self.assertRaises(TypeError):
            self.compiler.compile(expr, column_names=['transformer#1#0'])

    def test_raises_error_with_invalid_binary_operator(self):
        with self.assertRaises(TypeError):
            self.compiler.compile(BinaryOpNode.of('<', TypeNameNode.of('int'), TypeNameNode.of('float')))

    def test_raises_error_when_too_many_columns_specified(self):
        with self.assertRaises(TypeError) as ctx:
            self.compiler.compile(TypeNameNode.of('int'), column_names=['A', 'B'])
        self.assertEqual('defined 2 columns but only 1 values produced.', str(ctx.exception))

    def test_raises_error_if_reference_is_not_defined_and_not_a_constant(self):
        with self.assertRaises(KeyError) as ctx:
            self.compiler.compile(ReferenceNode.of('@non_existent'), column_names=['A'])
        self.assertEqual("'@non_existent'", str(ctx.exception))
