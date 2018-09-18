import re
import unittest
from types import SimpleNamespace
from unittest import TestCase

from feanor.schema import (
    Schema, FunctionalTransformer, SchemaError,
    ProjectionTransformer,
    ChoiceTransformer,
    MergeTransformer,
    IdentityTransformer,
)


class TestSchema(unittest.TestCase):
    def test_can_add_columns_to_a_schema(self):
        schema = Schema()
        schema.add_column('A')
        schema.add_column('B')
        schema.add_column('C')
        self.assertEqual(('A', 'B', 'C'), schema.columns)

    def test_add_column_raises_error_if_column_is_already_defined(self):
        schema = Schema()
        schema.add_column('A')
        with self.assertRaises(SchemaError) as ctx:
            schema.add_column('A')

        self.assertEqual("Column 'A' is already defined.", str(ctx.exception))

    def test_add_column_does_not_add_a_column_if_it_raises_error(self):
        schema = Schema()
        schema.add_column('A')
        with self.assertRaises(SchemaError):
            schema.add_column('A')

        self.assertEqual(('A',), schema.columns)

    def test_can_obtain_a_column_type(self):
        schema = Schema()
        schema.define_column('A', type='int')
        self.assertEqual(('A',), schema.columns)
        self.assertEqual('A', schema.arbitraries[0].name)
        self.assertEqual('int', schema.arbitraries[0].type)
        self.assertEqual({}, schema.arbitraries[0].config)

    def test_can_specify_header_visibility(self):
        schema = Schema(show_header=False)
        self.assertFalse(schema.show_header)

    def test_can_define_column_configuration(self):
        schema = Schema()
        schema.define_column('A', type='int', config={'a': 10})
        self.assertEqual(('A',), schema.columns)
        self.assertEqual('A', schema.arbitraries[0].name)
        self.assertEqual('int', schema.arbitraries[0].type)
        self.assertEqual({'a': 10}, schema.arbitraries[0].config)

    def test_creates_different_arbitraries_when_multiple_columns(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        self.assertEqual(('A', 'B', 'C'), schema.columns)
        self.assertEqual(3, len(schema.arbitraries))
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual('A', arbitraries[0].name)
        self.assertEqual('int', arbitraries[0].type)
        self.assertEqual({}, arbitraries[0].config)
        self.assertEqual('B', arbitraries[1].name)
        self.assertEqual('int', arbitraries[1].type)
        self.assertEqual({}, arbitraries[1].config)
        self.assertEqual('C', arbitraries[2].name)
        self.assertEqual('int', arbitraries[2].type)
        self.assertEqual({}, arbitraries[2].config)

    def test_can_create_column_by_referencing_arbitrary(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        schema.define_column('A', arbitrary='my_arbitrary')
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual('my_arbitrary', schema.arbitraries[0].name)
        self.assertEqual('int', schema.arbitraries[0].type)
        self.assertEqual({}, schema.arbitraries[0].config)
        self.assertEqual(1, len(schema.transformers))
        self.assertEqual('A', schema.transformers[0].name)
        self.assertEqual(['my_arbitrary'], schema.transformers[0].inputs)
        self.assertEqual(['A'], schema.transformers[0].outputs)
        self.assertEqual(ProjectionTransformer(1, 0), schema.transformers[0].transformer)

    def test_can_create_columns_with_same_arbitrary(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        schema.define_column('A', arbitrary='my_arbitrary')
        schema.define_column('B', arbitrary='my_arbitrary')
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual('my_arbitrary', schema.arbitraries[0].name)
        self.assertEqual('int', schema.arbitraries[0].type)
        self.assertEqual({}, schema.arbitraries[0].config)

    def test_str(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        schema.define_column('A', arbitrary='my_arbitrary')
        schema.define_column('B', arbitrary='my_arbitrary')
        str_regex = re.compile(r'''
            Schema\(
            \s*columns=\[[^]]+\],
            \s*arbitraries=\{my_arbitrary:\s*\{'type':\s'int',\s'config':\s\{\}\}\},
            \s*transformers=(\{'name':\s'(A|B)',\s*'transformer':\s<feanor\.schema\.ProjectionTransformer\sobject\sat\s\w+>,\s*'inputs':\s\[[^]]+\],\s'outputs':\s\[[^]]+\]\},?\s*)+
            show_header=True\s*
            \)
        ''', re.VERBOSE)
        self.assertRegex(str(schema), str_regex)

    def test_cannot_specify_both_arbitrary_and_type(self):
        schema = Schema()
        with self.assertRaises(TypeError):
            schema.define_column('A', arbitrary='my_arbitrary', type='int')

    def test_cannot_specify_both_arbitrary_and_config(self):
        schema = Schema()
        with self.assertRaises(TypeError):
            schema.define_column('A', arbitrary='my_arbitrary', config={'a': 1})

    def test_must_specify_arbitrary_or_type(self):
        schema = Schema()
        with self.assertRaises(TypeError):
            schema.define_column('A')

        with self.assertRaises(TypeError):
            schema.define_column('A', config={'a': 1})

    def test_raises_error_if_register_same_column_multiple_times(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        with self.assertRaises(SchemaError) as ctx:
            schema.add_arbitrary('my_arbitrary', type='int')

        self.assertEqual("Arbitrary 'my_arbitrary' is already defined.", str(ctx.exception))

    def test_raises_error_if_specified_arbitrary_is_not_defined(self):
        schema = Schema()
        with self.assertRaises(SchemaError):
            schema.define_column('A', arbitrary='non-existent')

    def test_raises_error_if_register_same_arbitrary_multiple_times(self):
        schema = Schema()
        schema.define_column('A', type='int')
        with self.assertRaises(SchemaError) as ctx:
            schema.define_column('A', type='int')

        self.assertEqual("Column 'A' is already defined.", str(ctx.exception))

    def test_can_mix_reference_and_auto_generated_arbitraries(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        schema.define_column('A', arbitrary='my_arbitrary')
        schema.define_column('B', type='int')
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='B', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='my_arbitrary', type='int', config={}), arbitraries[1])

    def test_can_add_a_transformer(self):
        schema = Schema()
        schema.define_column('A', type='int')
        add_one = FunctionalTransformer(lambda x: x + 1)
        schema.add_transformer('my_transformer', inputs=['A'], outputs=['A'], transformer=add_one)
        self.assertEqual(1, len(schema.transformers))
        self.assertEqual(SimpleNamespace(name='my_transformer', inputs=['A'], outputs=['A'], transformer=add_one),
                         schema.transformers[0])

    def test_can_use_transformer_to_filter_value(self):
        schema = Schema()
        schema.define_column('A', type='int')

        def test_transformer(unused):
            return None

        ret_none = FunctionalTransformer(test_transformer)
        schema.add_transformer('my_transformer', inputs=['A'], outputs=['A'], transformer=ret_none)
        self.assertEqual(1, len(schema.transformers))
        self.assertEqual(SimpleNamespace(name='my_transformer', inputs=['A'], outputs=['A'], transformer=ret_none),
                         schema.transformers[0])

    def test_raises_an_error_if_inputs_do_not_exist(self):
        schema = Schema()
        schema.define_column('A', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        with self.assertRaises(SchemaError) as ctx:
            schema.add_transformer('my_transformer', inputs=['B'], outputs=['A'], transformer=ret_none)
        self.assertEqual("Inputs: 'B' are not defined in the schema.", str(ctx.exception))

    def test_raises_an_error_if_num_inputs_do_not_match_arity(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        with self.assertRaises(SchemaError) as ctx:
            schema.add_transformer('my_transformer', inputs=['A', 'B'], outputs=['B'], transformer=ret_none)
        self.assertEqual("Got 2 inputs: 'A', 'B' but transformer's arity is 1.", str(ctx.exception))

    def test_raises_an_error_if_num_outputs_do_not_match_arity(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        with self.assertRaises(SchemaError) as ctx:
            schema.add_transformer('my_transformer', inputs=['A'], outputs=['A', 'B'], transformer=ret_none)
        self.assertEqual("Got 2 outputs: 'A', 'B' but transformer's number of outputs is 1.", str(ctx.exception))

    def test_raises_an_error_if_double_output_name(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x: None, num_outputs=2)
        with self.assertRaises(SchemaError) as ctx:
            schema.add_transformer('my_transformer', inputs=['A'], outputs=['A', 'A'], transformer=ret_none)
        self.assertEqual("Outputs must be unique. Got multiple 'A' outputs.", str(ctx.exception))

    def test_can_repeat_input_name_of_transformer(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x, y: x + y)
        schema.add_transformer('my_transformer', inputs=['A', 'A'], outputs=['A'], transformer=ret_none)
        self.assertEqual(len(schema.transformers), 1)
        self.assertEqual(SimpleNamespace(name='my_transformer', inputs=['A', 'A'], outputs=['A'], transformer=ret_none),
                         schema.transformers[0])

    def test_raises_error_if_register_same_transformer_multiple_times(self):
        schema = Schema()
        schema.define_column('A', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        schema.add_transformer('my_transformer', inputs=['A'], outputs=['A'], transformer=ret_none)
        with self.assertRaises(SchemaError) as ctx:
            schema.add_transformer('my_transformer', inputs=['A'], outputs=['A'], transformer=ret_none)
        self.assertEqual("Transformer 'my_transformer' is already defined.", str(ctx.exception))


class TestChoiceTransformer(TestCase):
    def test_raises_error_if_left_config_is_not_a_number(self):
        with self.assertRaises(TypeError):
            ChoiceTransformer(2, "something", 1)

    def test_raises_error_if_left_config_is_out_of_range(self):
        with self.assertRaises(TypeError):
            ChoiceTransformer(2, 2.0, 0)

    def test_raises_error_if_right_config_is_not_a_number(self):
        with self.assertRaises(TypeError):
            ChoiceTransformer(2, 1, "something")

    def test_raises_error_if_right_config_is_out_of_range(self):
        with self.assertRaises(TypeError):
            ChoiceTransformer(2, 0.5, 2.0)

    def test_raises_error_if_config_sum_is_out_of_range(self):
        with self.assertRaises(ValueError):
            ChoiceTransformer(2, 0.75, 0.75)

    def test_raises_error_if_too_many_inputs(self):
        transformer = ChoiceTransformer(2, 0.5, 0.5)
        with self.assertRaises(ValueError):
            transformer([0, 1, 2, 3])

    def test_raises_error_if_too_few_inputs(self):
        transformer = ChoiceTransformer(2, 0.5, 0.5)
        with self.assertRaises(ValueError):
            transformer([0])

    def test_always_return_left_input_if_probability_is_one(self):
        transformer = ChoiceTransformer(2, 1.0, 0.0)
        for _ in range(10):
            self.assertEqual([0], transformer([0, 1]))

    def test_always_return_right_input_if_probability_is_one(self):
        transformer = ChoiceTransformer(2, 0.0, 1.0)
        for _ in range(10):
            self.assertEqual([1], transformer([0, 1]))

    def test_always_return_none_if_probability_sum_is_zero(self):
        transformer = ChoiceTransformer(2, 0.0, 0.0)
        for _ in range(10):
            self.assertEqual((None,), transformer([0, 1]))

    def test_returns_all_values_if_probability_is_not_zero_or_one_and_sums_to_1(self):
        transformer = ChoiceTransformer(2, 0.5, 0.5)
        self.assertEqual({0, 1}, {transformer([0, 1])[0] for _ in range(50)})

    def test_returns_all_values_and_none_if_probability_is_not_zero_or_one_and_sums_less_than_1(self):
        transformer = ChoiceTransformer(2, 0.3, 0.3)
        self.assertEqual({0, 1, None}, {transformer([0, 1])[0] for _ in range(50)})

    def test_equal_transformer_are_equal(self):
        transformer = ChoiceTransformer(2, 0.3, 0.3)
        other_transformer = ChoiceTransformer(2, 0.3, 0.3)
        self.assertEqual(transformer, other_transformer)

    def test_different_transformer_are_not_equal(self):
        transformer = ChoiceTransformer(2, 0.3, 0.3)
        other_transformer = ChoiceTransformer(2, 0.25, 0.3)
        self.assertNotEqual(transformer, other_transformer)

    def test_equal_transformer_have_same_hash(self):
        transformer = ChoiceTransformer(2, 0.3, 0.3)
        other_transformer = ChoiceTransformer(2, 0.3, 0.3)
        self.assertEqual(hash(transformer), hash(other_transformer))


class TestMergeTransformer(TestCase):
    def test_can_merge_ints(self):
        transformer = MergeTransformer(4)
        self.assertEqual((1, 2), transformer([0, 1, 1, 1]))

    def test_can_merge_strings(self):
        transformer = MergeTransformer(4)
        self.assertEqual(("ac", "bd"), transformer(["a", "b", "c", "d"]))

    def test_equal_transformers_are_equal(self):
        transformer = MergeTransformer(4)
        other_transformer = MergeTransformer(4)
        self.assertEqual(transformer, other_transformer)

    def test_different_transformers_are_not_equal(self):
        transformer = MergeTransformer(4)
        other_transformer = MergeTransformer(6)
        self.assertNotEqual(transformer, other_transformer)

    def test_equal_transformers_have_same_hash(self):
        transformer = MergeTransformer(4)
        other_transformer = MergeTransformer(4)
        self.assertEqual(hash(transformer), hash(other_transformer))


class TestIdentityTransformer(TestCase):
    def test_can_return_identity_of_a_single_value(self):
        transformer = IdentityTransformer(1)
        self.assertEqual((0,), transformer([0]))

    def test_can_return_identity_of_multiple_values(self):
        transformer = IdentityTransformer(3)
        self.assertEqual((0, 1, 2), transformer([0, 1, 2]))

    def test_equal_transformers_are_equal(self):
        transformer = IdentityTransformer(1)
        other_transformer = IdentityTransformer(1)
        self.assertEqual(transformer, other_transformer)

    def test_different_transformers_are_not_equal(self):
        transformer = IdentityTransformer(1)
        other_transformer = IdentityTransformer(3)
        self.assertNotEqual(transformer, other_transformer)

    def test_equal_transformers_have_same_hash(self):
        transformer = IdentityTransformer(1)
        other_transformer = IdentityTransformer(1)
        self.assertEqual(hash(transformer), hash(other_transformer))


class TestProjectionTransformer(TestCase):
    def test_can_return_projection(self):
        transformer = ProjectionTransformer(2, 1)
        self.assertEqual((1,), transformer([0, 1]))

    def test_equal_transformers_are_equal(self):
        transformer = ProjectionTransformer(2, 0)
        other_transformer = ProjectionTransformer(2, 0)
        self.assertEqual(transformer, other_transformer)

    def test_different_transformers_are_not_equal(self):
        transformer = ProjectionTransformer(2, 0)
        other_transformer = ProjectionTransformer(2, 1)
        self.assertNotEqual(transformer, other_transformer)

    def test_equal_transformers_have_same_hash(self):
        transformer = ProjectionTransformer(2, 0)
        other_transformer = ProjectionTransformer(2, 0)
        self.assertEqual(hash(transformer), hash(other_transformer))


class TestFunctionalTransformer(TestCase):
    def test_can_apply_function_with_one_input_and_output(self):
        transformer = FunctionalTransformer(lambda x: x + 1)
        self.assertEqual((1,), transformer([0]))

    def test_can_apply_function_with_more_inputs_and_one_output(self):
        transformer = FunctionalTransformer(lambda x, y, z: x + y + z)
        self.assertEqual((3,), transformer([0, 1, 2]))

    def test_can_apply_function_with_one_input_and_more_outputs(self):
        transformer = FunctionalTransformer(lambda x: (x, x + 1, x + 2), num_outputs=3)
        self.assertEqual((0, 1, 2), transformer([0]))

    def test_can_apply_function_with_more_inputs_and_more_outputs(self):
        transformer = FunctionalTransformer(lambda x, y: (x, x + 1, x + y, y - x), num_outputs=4)
        self.assertEqual((0, 1, 7, 7), transformer([0, 7]))

    def test_can_equal_with_same_function(self):
        func = lambda x, y: (x, x + 1, x + y, y - x)
        transformer = FunctionalTransformer(func, num_outputs=4)
        other_transformer = FunctionalTransformer(func, num_outputs=4)
        self.assertEqual(transformer, other_transformer)

    def test_equal_transformers_have_same_hash(self):
        func = lambda x, y: (x, x + 1, x + y, y - x)
        transformer = FunctionalTransformer(func, num_outputs=4)
        other_transformer = FunctionalTransformer(func, num_outputs=4)
        self.assertEqual(hash(transformer), hash(other_transformer))
