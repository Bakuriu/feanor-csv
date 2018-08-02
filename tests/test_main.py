import unittest
from types import SimpleNamespace

from feanor.main import make_schema
from feanor.schema import ProjectionTransformer, IdentityTransformer


class TestMakeSchema(unittest.TestCase):

    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema([('A', '#int')], [], show_header=True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(1, len(schema.transformers))
        expected_transformer = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer, schema.transformers[0])

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema([('A', '#int'), ('B', '#int')], [], show_header=True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        self.assertEqual(2, len(schema.transformers))
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#1'], outputs=['B'],
                                               transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])

    def test_can_make_schema_with_transformers(self):
        schema = make_schema([('A', '@bob'), ('B', '#int')], [('bob', '#int')],show_header=True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        self.assertEqual(3, len(schema.transformers))
        expected_transformer_bob = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['bob'],
                                               transformer=IdentityTransformer(1))
        expected_transformer_A = SimpleNamespace(name='transformer#1', inputs=['arbitrary#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#2', inputs=['arbitrary#1'], outputs=['B'],
                                               transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_bob, schema.transformers[0])
        self.assertEqual(expected_transformer_A, schema.transformers[1])
        self.assertEqual(expected_transformer_B, schema.transformers[2])
