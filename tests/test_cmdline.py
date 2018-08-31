import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from feanor.main import parse_arguments
from feanor.schema import IdentityTransformer, MergeTransformer


@patch('sys.stderr', open(os.devnull, 'w'))
class TestCommandLine(unittest.TestCase):

    @patch('sys.exit')
    def test_cannot_create_schema_if_size_parameter_missing(self, mock_sys_exit):
        try:
            parse_arguments(['cmdline', '-c', 'A', '#int'])
        except TypeError:
            # unfortunately argparse relies on sys.exit to "exit" a function, so when it
            # is mocked the function returns without an issue with None and causes a TypeError.
            pass
        mock_sys_exit.assert_called_with(2)

    @patch('sys.exit')
    def test_cannot_create_schema_with_one_column_but_no_arbitrary(self, mock_sys_exit):
        try:
            parse_arguments(['-n', '10', 'cmdline', '-c', 'A'])
        except TypeError:
            # unfortunately argparse relies on sys.exit to "exit" a function, so when it
            # is mocked the function returns without an issue with None and causes a TypeError.
            pass
        mock_sys_exit.assert_called_with(2)

    @patch('sys.exit')
    def test_cannot_create_schema_without_specifying_cmdline_and_expr(self, mock_sys_exit):
        try:
            parse_arguments(['-n', '10', '-c', 'A', '#int'])
        except TypeError:
            # unfortunately argparse relies on sys.exit to "exit" a function, so when it
            # is mocked the function returns without an issue with None and causes a TypeError.
            pass
        mock_sys_exit.assert_called_with(2)

        try:
            parse_arguments(['-n', '10', 'let a := #int in @a'])
        except TypeError:
            # unfortunately argparse relies on sys.exit to "exit" a function, so when it
            # is mocked the function returns without an issue with None and causes a TypeError.
            pass
        mock_sys_exit.assert_called_with(2)

    @patch('sys.exit')
    def test_can_create_schema_with_one_column(self, _):
        schema,  _, _, size_dict = parse_arguments(['-n', '5', 'cmdline', '-c', 'A', '#int'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), schema.arbitraries[0])
        expected_transformer = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer, schema.transformers[0])

    @patch('sys.exit')
    def test_can_create_schema_with_two_columns(self, _):
        schema,  _, _, size_dict = parse_arguments(['-n', '5', 'cmdline', '-c', 'A', '#int', '-c', 'B', '#int'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])

    @patch('sys.exit')
    def test_can_create_schema_with_two_identical_columns(self, _):
        schema,  _, _, size_dict = parse_arguments(['-n', '5', 'cmdline', '-c', 'A', '#int', '-c', 'B', '@A'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(4, len(schema.transformers))
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#0'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_A_copy = SimpleNamespace(name='transformer#2', inputs=['arbitrary#0'], outputs=['A'],
                                                      transformer=IdentityTransformer(1))
        expected_transformer_B_copy = SimpleNamespace(name='transformer#3', inputs=['arbitrary#0'], outputs=['B'],
                                                      transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])
        self.assertEqual(expected_transformer_A_copy, schema.transformers[2])
        self.assertEqual(expected_transformer_B_copy, schema.transformers[3])

    @patch('sys.exit')
    def test_can_create_schema_with_third_column_sum_of_two_columns(self, _):
        schema,  _, _, size_dict = parse_arguments(
            ['-n', '5', 'cmdline', '-c', 'A', '#int', '-c', 'B', '#int', '-c', 'C', '@A+@B'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B', 'C'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_merge = SimpleNamespace(name='transformer#2', inputs=['arbitrary#0', 'arbitrary#1'],
                                                     outputs=['transformer#2#0'],
                                                     transformer=MergeTransformer(2))
        expected_transformer_C = SimpleNamespace(name='transformer#3', inputs=['transformer#2#0'], outputs=['C'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])
        self.assertEqual(expected_transformer_merge, schema.transformers[2])
        self.assertEqual(expected_transformer_C, schema.transformers[3])

    @patch('sys.exit')
    def test_can_create_complex_schema_using_alias(self, _):
        schema, _, _, size_dict = parse_arguments(
            ['-n', '5', 'options', '-c', 'A', '#int', '-c', 'B', '#int', '-c', 'C', '@A+@B'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B', 'C'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_merge = SimpleNamespace(name='transformer#2', inputs=['arbitrary#0', 'arbitrary#1'],
                                                     outputs=['transformer#2#0'],
                                                     transformer=MergeTransformer(2))
        expected_transformer_C = SimpleNamespace(name='transformer#3', inputs=['transformer#2#0'], outputs=['C'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])
        self.assertEqual(expected_transformer_merge, schema.transformers[2])
        self.assertEqual(expected_transformer_C, schema.transformers[3])

    @patch('sys.exit')
    def test_can_create_schema_with_one_column_using_expr(self, _):
        schema, _, _, size_dict = parse_arguments(['-n', '5', 'expr', '--columns', 'A', '#int'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), schema.arbitraries[0])
        expected_transformer = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer, schema.transformers[0])

    @patch('sys.exit')
    def test_can_create_schema_with_two_columns_using_expr(self, _):
        schema, _, _, size_dict = parse_arguments(['-n', '5', 'expr', '--columns', 'A,B', '#int . #int'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])

    @patch('sys.exit')
    def test_can_create_schema_with_two_identical_columns_using_expr(self, _):
        schema, _, _, size_dict = parse_arguments(['-n', '5', 'expr', '--columns', 'A,B', 'let A := #int in @A . @A'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(3, len(schema.transformers))
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_A_copy = SimpleNamespace(name='transformer#1', inputs=['arbitrary#0'], outputs=['A'],
                                                      transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#2', inputs=['arbitrary#0'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_A_copy, schema.transformers[1])
        self.assertEqual(expected_transformer_B, schema.transformers[2])

    @patch('sys.exit')
    def test_can_create_schema_with_columns_with_config(self, _):
        schema, _, _, size_dict = parse_arguments(['-n', '5', 'expr', '--columns', 'A', '#int{"min":10}'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={'min': 10}), schema.arbitraries[0])
        self.assertEqual(1, len(schema.transformers))
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])

    @patch('sys.exit')
    def test_can_create_schema_with_third_column_sum_of_two_columns_using_expr(self, _):
        schema, _, _, size_dict = parse_arguments(
            ['-n', '5', 'expr', '--columns', 'A,B,C', '(#int)=A . (#int)=B . (@A+@B)'])
        self.assertEqual({'number_of_rows': 5}, size_dict)
        self.assertEqual(('A', 'B', 'C'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_merge = SimpleNamespace(name='transformer#2', inputs=['arbitrary#0', 'arbitrary#1'],
                                                     outputs=['transformer#2#0'],
                                                     transformer=MergeTransformer(2))
        expected_transformer_C = SimpleNamespace(name='transformer#3', inputs=['transformer#2#0'], outputs=['C'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])
        self.assertEqual(expected_transformer_merge, schema.transformers[2])
        self.assertEqual(expected_transformer_C, schema.transformers[3])
