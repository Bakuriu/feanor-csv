import unittest
from types import SimpleNamespace

from feanor.main import make_schema


class TestMakeSchema(unittest.TestCase):
    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema([], [('A', ('int', None, None))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(SimpleNamespace(name='A', arbitrary='column#0'), schema.columns[0])
        self.assertEqual(1, len(schema.columns))
        self.assertEqual(SimpleNamespace(name='column#0', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(1, len(schema.arbitraries))

    def test_can_make_schema_with_a_single_column_using_explicit_arbitrary(self):
        schema = make_schema([('bob', ('int', None))], [('A', (None, None, 'bob'))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(SimpleNamespace(name='A', arbitrary='bob'), schema.columns[0])
        self.assertEqual(1, len(schema.columns))
        self.assertEqual(SimpleNamespace(name='bob', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(1, len(schema.arbitraries))

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema([], [('A', ('int', None, None)), ('B', ('int', None, None))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(SimpleNamespace(name='A', arbitrary='column#0'), schema.columns[0])
        self.assertEqual(SimpleNamespace(name='B', arbitrary='column#1'), schema.columns[1])
        self.assertEqual(2, len(schema.columns))
        self.assertEqual(SimpleNamespace(name='column#0', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(SimpleNamespace(name='column#1', type='int', config={}), schema.arbitraries[1])
        self.assertEqual(2, len(schema.arbitraries))


    def test_can_make_schema_with_multiple_columns_using_explicit_arbitrary(self):
        schema = make_schema([('bob', ('int', None))], [('A', (None, None, 'bob')), ('B', ('int', None, None))], True)
        self.assertTrue(schema.show_header)
        self.assertEqual(SimpleNamespace(name='A', arbitrary='bob'), schema.columns[0])
        self.assertEqual(SimpleNamespace(name='B', arbitrary='column#1'), schema.columns[1])
        self.assertEqual(2, len(schema.columns))
        self.assertEqual(SimpleNamespace(name='bob', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(SimpleNamespace(name='column#1', type='int', config={}), schema.arbitraries[1])
        self.assertEqual(2, len(schema.arbitraries))