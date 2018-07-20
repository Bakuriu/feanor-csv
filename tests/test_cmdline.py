import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from feanor.main import parse_arguments


@patch('sys.stderr', open(os.devnull, 'w'))
class TestCommandLine(unittest.TestCase):

    @patch('sys.exit')
    def test_cannot_create_schema_if_size_parameter_missing(self, mock_sys_exit):
        parse_arguments(['-c', 'A', '-a', 'A', 'int'])
        mock_sys_exit.assert_called_with(2)

    @patch('sys.exit')
    def test_cannot_create_schema_with_one_column_but_no_arbitrary(self, mock_sys_exit):
        parse_arguments(['-c', 'A', '-n', '10'])
        mock_sys_exit.assert_called_with(2)

    @patch('sys.exit')
    def test_can_create_schema_with_one_column(self, _):
        schema, _, size_dict = parse_arguments(['-c', 'A', '-a', 'A', 'int', '-n', '5'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), schema.arbitraries[0])

    @patch('sys.exit')
    def test_can_create_schema_with_two_columns(self, _):
        schema, _, size_dict = parse_arguments(['-c', 'A', '-c', 'B', '-a', 'A', 'int', '-a', 'B', 'int', '-n', '5'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='B', type='int', config={}), arbitraries[1])

    @patch('sys.exit')
    def test_can_create_schema_with_two_identical_columns(self, _):
        schema, _, size_dict = parse_arguments(['-c', 'A', '-c', 'B', '-a', 'A', 'int', '-t', 'T', 'A', 'B', 'A', '-n', '5'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(1, len(schema.transformers))
        transformer = schema.transformers[0]
        self.assertEqual('T', transformer.name)
        self.assertEqual(['A'], transformer.inputs)
        self.assertEqual(['B'], transformer.outputs)
        self.assertEqual((-3,), transformer.transformer((-3,)))

    @patch('sys.exit')
    def test_can_create_schema_with_third_column_sum_of_two_columns(self, _):
        schema, _, size_dict = parse_arguments(['-c', 'A', '-c', 'B', '-c', 'C', '-a', 'A', 'int', '-a', 'B', 'int', '-t', 'T', 'A,B', 'C', 'A+B', '-n', '5'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B', 'C'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(SimpleNamespace(name='A', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='B', type='int', config={}), arbitraries[1])
        self.assertEqual(1, len(schema.transformers))
        transformer = schema.transformers[0]
        self.assertEqual('T', transformer.name)
        self.assertEqual(['A', 'B'], transformer.inputs)
        self.assertEqual(['C'], transformer.outputs)
        self.assertEqual((3,), transformer.transformer((1, 2)))
