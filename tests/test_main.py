import unittest
from types import SimpleNamespace

from feanor.main import make_schema
from feanor.schema import ProjectionTransformer


class TestMakeSchema(unittest.TestCase):
    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema([], [('A', ('int', None, None))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), schema.arbitraries[0])

    def test_can_make_schema_with_a_single_column_using_explicit_arbitrary(self):
        schema = make_schema([('bob', ('int', None))], [('A', (None, None, 'bob'))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='bob', type='int', config={}), schema.arbitraries[0])

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema([], [('A', ('int', None, None)), ('B', ('int', None, None))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key= lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='B', type='int', config={}), arbitraries[1])


    def test_can_make_schema_with_multiple_columns_using_explicit_arbitrary(self):
        schema = make_schema([('bob', ('int', None))], [('A', (None, None, 'bob')), ('B', ('int', None, None))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='B', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='bob', type='int', config={}), arbitraries[1])
        self.assertEqual(1, len(schema.transformers))
        self.assertEqual(SimpleNamespace(name='A', inputs=['bob'], outputs=['A'], transformer=ProjectionTransformer(1, 0)), schema.transformers[0])
