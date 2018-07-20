import argparse
import unittest
from types import SimpleNamespace

from feanor.main import make_schema, ArbitraryType, TransformerType
from feanor.schema import ProjectionTransformer, FunctionalTransformer


class TestMakeSchema(unittest.TestCase):
    def test_can_make_schema_without_columns(self):
        schema = make_schema([], [], [], show_header=True)
        self.assertTrue(schema.show_header)
        self.assertEqual((), schema.columns)
        self.assertEqual((), schema.arbitraries)
        self.assertEqual((), schema.transformers)

    def test_can_make_schema_with_show_header_false(self):
        schema = make_schema([], [], [], show_header=False)
        self.assertFalse(schema.show_header)

    def test_can_make_schema_with_column_no_arbitraries(self):
        with self.assertRaises(ValueError) as ctx:
            make_schema(['A'], [], [], show_header=True)

        self.assertEqual("Invalid schema. Columns 'A' have no associated generator.", str(ctx.exception))

    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema(['A'], [('A', ('int', None))], [], show_header=True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(0, len(schema.transformers))

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema(['A', 'B'], [('A', ('int', None)), ('B', ('int', None))], [], show_header=True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='B', type='int', config={}), arbitraries[1])
        self.assertEqual(0, len(schema.transformers))

    def test_can_make_schema_with_transformers(self):
        schema = make_schema(['A', 'B'], [('bob', ('int', None)), ('B', ('int', None))],
                             [('A', (['bob'], ['A'], ProjectionTransformer(1, 0)))], show_header=True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='B', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='bob', type='int', config={}), arbitraries[1])
        self.assertEqual(1, len(schema.transformers))
        expected_tr = SimpleNamespace(name='A', inputs=['bob'], outputs=['A'], transformer=ProjectionTransformer(1, 0))
        self.assertEqual(expected_tr, schema.transformers[0])


class TestArbitraryType(unittest.TestCase):
    def test_arbitrary_does_not_modify_name(self):
        typer = ArbitraryType()
        self.assertEqual('not touched', typer('not touched'))

    def test_arbitrary_does_parse_type_on_second_call(self):
        typer = ArbitraryType()
        typer('unused')
        self.assertEqual(('int', {}), typer('int'))

    def test_arbitrary_does_parse_type_on_second_call_with_config(self):
        typer = ArbitraryType()
        typer('unused')
        self.assertEqual(('int', {'lowerbound': 10}), typer('int{"lowerbound":10}'))

    def test_arbitrary_raises_error_if_expression_is_invalid(self):
        typer = ArbitraryType()
        typer('name')
        with self.assertRaises(argparse.ArgumentTypeError):
            typer('invalid_expression +')

    def test_arbitrary_raises_error_if_invalid_conf(self):
        typer = ArbitraryType()
        typer('name')
        with self.assertRaises(argparse.ArgumentTypeError):
            typer('int{func:5}')

    def test_arbitrary_does_not_modify_every_even_call(self):
        typer = ArbitraryType()
        for i in range(20):
            self.assertEqual('gotcha!', typer('gotcha!'))
            typer('int')

    def test_arbitrary_does_parse_type_every_odd_call(self):
        typer = ArbitraryType()
        for i in range(20):
            typer('unused')
            self.assertEqual(('int', {}), typer('int'))

    def test_arbitrary_alternates_behaviour(self):
        typer = ArbitraryType()
        for i in range(20):
            self.assertEqual('gotcha!', typer('gotcha!'))
            self.assertEqual(('int', {}), typer('int'))


class TestTransformerType(unittest.TestCase):
    def test_transformer_does_not_modify_name(self):
        typer = TransformerType()
        self.assertEqual('not touched', typer('not touched'))

    def test_transformer_does_parse_inputs_on_second_call(self):
        typer = TransformerType()
        typer('unused')
        self.assertEqual(['A', 'B', 'C'], typer('A,B,C'))

    def test_transformer_does_parse_outputs_on_third_call(self):
        typer = TransformerType()
        typer('unused')
        typer('unused')
        self.assertEqual(['A', 'B', 'C'], typer('A,B,C'))

    def test_transformer_does_parse_expression_on_fourth_call(self):
        typer = TransformerType()
        typer('name')
        typer('A')
        typer('B')
        got = typer('x+1')
        self.assertIsInstance(got, FunctionalTransformer)
        self.assertEqual(1, got.arity)
        self.assertEqual(1, got.num_outputs)

    def test_transformer_does_parse_expression_on_fourth_call_multiple_inputs(self):
        typer = TransformerType()
        typer('name')
        typer('A,B')
        typer('B')
        got = typer('x+1')
        self.assertIsInstance(got, FunctionalTransformer)
        self.assertEqual(2, got.arity)
        self.assertEqual(1, got.num_outputs)

    def test_transformer_does_parse_expression_on_fourth_call_multiple_outputs(self):
        typer = TransformerType()
        typer('name')
        typer('A')
        typer('B,A')
        got = typer('x+1')
        self.assertIsInstance(got, FunctionalTransformer)
        self.assertEqual(1, got.arity)
        self.assertEqual(2, got.num_outputs)

    def test_transformer_does_parse_expression_on_fourth_call_multiple_inputs_and_outputs(self):
        typer = TransformerType()
        typer('name')
        typer('A,B')
        typer('B,A')
        got = typer('x+1')
        self.assertIsInstance(got, FunctionalTransformer)
        self.assertEqual(2, got.arity)
        self.assertEqual(2, got.num_outputs)

    def test_transformer_raises_error_if_expression_is_invalid(self):
        typer = TransformerType()
        typer('name')
        typer('A,B')
        typer('B,A')
        with self.assertRaises(argparse.ArgumentTypeError):
            typer('invalid_expression +')

    def test_transformer_does_not_modify_every_fourth_call(self):
        typer = TransformerType()
        for i in range(20):
            self.assertEqual('gotcha!', typer('gotcha!'))
            typer('unused')
            typer('unused')
            typer('unused')

    def test_transformer_alternates_behaviour(self):
        typer = TransformerType()
        for i in range(20):
            self.assertEqual('gotcha!', typer('gotcha!'))
            self.assertEqual(['A', 'B', 'C'], typer('A,B,C'))
            self.assertEqual(['D', 'E'], typer('D,E'))
            got = typer('x+1')
            self.assertIsInstance(got, FunctionalTransformer)
            self.assertEqual(3, got.arity)
            self.assertEqual(2, got.num_outputs)
