import unittest
from types import SimpleNamespace

from feanor.schema import (
    Schema, MissingVersionError, InvalidVersionNumberError, FunctionalTransformer, SchemaError,
    ProjectionTransformer,
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
