import unittest
from types import SimpleNamespace

from feanor.schema import Schema, MissingVersionError, InvalidVersionNumberError, FunctionalTransformer, SchemaError


class TestSchema(unittest.TestCase):
    def test_can_obtain_the_header_from_a_schema(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')
        schema.add_column('C', type='int')
        self.assertEqual(schema.header(), ('A', 'B', 'C'))

    def test_can_obtain_a_column_type(self):
        schema = Schema()
        schema.add_column('A', type='int')
        self.assertEqual(schema.columns[0].name, 'A')
        self.assertEqual(schema.columns[0].arbitrary, 'column#0')
        self.assertEqual(schema.arbitraries[0].name, 'column#0')
        self.assertEqual(schema.arbitraries[0].type, 'int')
        self.assertEqual(schema.arbitraries[0].config, {})

    def test_can_specify_header_visibility(self):
        schema = Schema(show_header=False)
        self.assertFalse(schema.show_header)

    def test_can_add_column_configuration(self):
        schema = Schema()
        schema.add_column('A', type='int', config={'a': 10})
        self.assertEqual(schema.columns[0].name, 'A')
        self.assertEqual(schema.columns[0].arbitrary, 'column#0')
        self.assertEqual(schema.arbitraries[0].name, 'column#0')
        self.assertEqual(schema.arbitraries[0].type, 'int')
        self.assertEqual(schema.arbitraries[0].config, {'a': 10})

    def test_creates_different_arbitraries_when_multiple_columns(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')
        schema.add_column('C', type='int')
        self.assertEqual(len(schema.columns), 3)
        self.assertEqual(len(schema.arbitraries), 3)
        self.assertEqual(schema.columns[0].name, 'A')
        self.assertEqual(schema.columns[0].arbitrary, 'column#0')
        self.assertEqual(schema.columns[1].name, 'B')
        self.assertEqual(schema.columns[1].arbitrary, 'column#1')
        self.assertEqual(schema.columns[2].name, 'C')
        self.assertEqual(schema.columns[2].arbitrary, 'column#2')
        self.assertEqual(schema.arbitraries[0].name, 'column#0')
        self.assertEqual(schema.arbitraries[0].type, 'int')
        self.assertEqual(schema.arbitraries[0].config, {})
        self.assertEqual(schema.arbitraries[1].name, 'column#1')
        self.assertEqual(schema.arbitraries[1].type, 'int')
        self.assertEqual(schema.arbitraries[1].config, {})
        self.assertEqual(schema.arbitraries[2].name, 'column#2')
        self.assertEqual(schema.arbitraries[2].type, 'int')
        self.assertEqual(schema.arbitraries[2].config, {})

    def test_can_create_column_by_referencing_arbitrary(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        schema.add_column('A', arbitrary='my_arbitrary')
        self.assertEqual(schema.columns[0].name, 'A')
        self.assertEqual(schema.columns[0].arbitrary, 'my_arbitrary')
        self.assertEqual(schema.arbitraries[0].name, 'my_arbitrary')
        self.assertEqual(schema.arbitraries[0].type, 'int')
        self.assertEqual(schema.arbitraries[0].config, {})

    def test_can_create_columns_with_same_arbitrary(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        schema.add_column('A', arbitrary='my_arbitrary')
        schema.add_column('B', arbitrary='my_arbitrary')
        self.assertEqual(schema.columns[0].name, 'A')
        self.assertEqual(schema.columns[0].arbitrary, 'my_arbitrary')
        self.assertEqual(schema.columns[1].name, 'B')
        self.assertEqual(schema.columns[1].arbitrary, 'my_arbitrary')
        self.assertEqual(len(schema.arbitraries), 1)
        self.assertEqual(schema.arbitraries[0].name, 'my_arbitrary')
        self.assertEqual(schema.arbitraries[0].type, 'int')
        self.assertEqual(schema.arbitraries[0].config, {})

    def test_cannot_specify_both_arbitrary_and_type(self):
        schema = Schema()
        with self.assertRaises(TypeError):
            schema.add_column('A', arbitrary='my_arbitrary', type='int')

    def test_cannot_specify_both_arbitrary_and_config(self):
        schema = Schema()
        with self.assertRaises(TypeError):
            schema.add_column('A', arbitrary='my_arbitrary', config={'a':1})

    def test_must_specify_arbitrary_or_type(self):
        schema = Schema()
        with self.assertRaises(TypeError):
            schema.add_column('A')

        with self.assertRaises(TypeError):
            schema.add_column('A', config={'a':1})

    def test_can_mix_reference_and_auto_generated_arbitraries(self):
        schema = Schema()
        schema.add_arbitrary('my_arbitrary', type='int')
        schema.add_column('A', arbitrary='my_arbitrary')
        schema.add_column('B', type='int')
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(len(arbitraries), 2)
        self.assertEqual(arbitraries[0], SimpleNamespace(name='column#1', type='int', config={}))
        self.assertEqual(arbitraries[1], SimpleNamespace(name='my_arbitrary', type='int', config={}))

    def test_can_add_a_transformer(self):
        schema = Schema()
        schema.add_column('A', type='int')
        add_one = FunctionalTransformer(lambda x: x+1)
        schema.add_transformer('my_transformer', inputs=['A'], outputs=['A'], transformer=add_one)
        self.assertEqual(len(schema.transformers), 1)
        self.assertEqual(schema.transformers[0], SimpleNamespace(name='my_transformer', inputs=['A'], outputs=['A'], transformer=add_one))

    def test_can_use_transformer_to_filter_value(self):
        schema = Schema()
        schema.add_column('A', type='int')

        def test_transformer(unused):
            return None

        ret_none = FunctionalTransformer(test_transformer)
        schema.add_transformer('my_transformer', inputs=['A'], outputs=['A'], transformer=ret_none)
        self.assertEqual(len(schema.transformers), 1)
        self.assertEqual(schema.transformers[0], SimpleNamespace(name='my_transformer', inputs=['A'], outputs=['A'], transformer=ret_none))

    def test_raises_an_error_if_inputs_do_not_exist(self):
        schema = Schema()
        schema.add_column('A', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        with self.assertRaises(SchemaError, msg="Inputs: 'B' are not defined in the schema."):
            schema.add_transformer('my_transformer', inputs=['B'], outputs=['A'], transformer=ret_none)

    def test_raises_an_error_if_outputs_do_not_exist(self):
        schema = Schema()
        schema.add_column('A', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        with self.assertRaises(SchemaError, msg="Outputs: 'B' are not defined in the schema."):
            schema.add_transformer('my_transformer', inputs=['A'], outputs=['B'], transformer=ret_none)

    def test_raises_an_error_if_num_inputs_do_not_match_arity(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        with self.assertRaises(SchemaError, msg="Got 2 inputs: 'A', 'A' but transformer's arity is 1."):
            schema.add_transformer('my_transformer', inputs=['A', 'B'], outputs=['B'], transformer=ret_none)

    def test_raises_an_error_if_num_outputs_do_not_match_arity(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x: None)
        with self.assertRaises(SchemaError, msg="Got two outputs: 'A', 'B' but transformer's number of outputs is 1."):
            schema.add_transformer('my_transformer', inputs=['A'], outputs=['A', 'B'], transformer=ret_none)

    def test_raises_an_error_if_double_output_name(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x, y: None, num_outputs=2)
        with self.assertRaises(SchemaError, msg="Outputs must be unique. Got multiple 'A' outputs."):
            schema.add_transformer('my_transformer', inputs=['A'], outputs=['A', 'A'], transformer=ret_none)

    def test_can_repeat_input_name_of_transformer(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')

        ret_none = FunctionalTransformer(lambda x, y: x+y)
        schema.add_transformer('my_transformer', inputs=['A', 'A'], outputs=['A'], transformer=ret_none)
        self.assertEqual(len(schema.transformers), 1)
        self.assertEqual(schema.transformers[0], SimpleNamespace(name='my_transformer', inputs=['A', 'A'], outputs=['A'], transformer=ret_none))


@unittest.skip
class TestSchemaParsing(unittest.TestCase):

    def test_can_parse_header_from_json_schema(self):
        schema = Schema.parse('{"version": "1.0", "header": ["A", "B", "C"]}')
        self.assertEqual(schema.header(), ('A', 'B', 'C'))

    def test_json_schema_must_have_version(self):
        with self.assertRaises(MissingVersionError):
            Schema.parse('{"header": ["A", "B", "C"]}')

    def test_json_schema_must_have_valid_version_number(self):
        for invalid_number in ('1', 'string', '1.0.2', ''):
            with self.assertRaises(InvalidVersionNumberError):
                Schema.parse('{"version": "%s", "header": ["A", "B", "C"]}' % invalid_number)