import argparse
import random
import unittest
from types import SimpleNamespace

from feanor.builtin import BuiltInLibrary
from feanor.library import EmptyLibrary
from feanor.main import (
    make_schema_cmdline, get_library, _parse_global_configuration, make_schema_expr,
    get_schema_size_and_library_params,
)
from feanor.schema import IdentityTransformer, Schema


class TestMakeSchemaCmdline(unittest.TestCase):

    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema_cmdline([('A', '%int')], [], show_header=True, library=EmptyLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(2, len(schema.transformers))
        expected_transformer = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        expected_transformer_copy = SimpleNamespace(name='transformer#1', inputs=['arbitrary#0'], outputs=['A'],
                                                    transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer, schema.transformers[0])
        self.assertEqual(expected_transformer_copy, schema.transformers[1])

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema_cmdline([('A', '%int'), ('B', '%int')], [], show_header=True, library=EmptyLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        self.assertEqual(4, len(schema.transformers))
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['arbitrary#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_A_copy = SimpleNamespace(name='transformer#2', inputs=['arbitrary#0'], outputs=['A'],
                                                      transformer=IdentityTransformer(1))
        expected_transformer_B_copy = SimpleNamespace(name='transformer#3', inputs=['arbitrary#1'], outputs=['B'],
                                                      transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])
        self.assertEqual(expected_transformer_A_copy, schema.transformers[2])
        self.assertEqual(expected_transformer_B_copy, schema.transformers[3])

    def test_can_make_schema_with_transformers(self):
        schema = make_schema_cmdline([('A', '@bob'), ('B', '%int')], [('bob', '%int')], show_header=True,
                                     library=EmptyLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        arbitraries = sorted(schema.arbitraries, key=lambda x: x.name)
        self.assertEqual(2, len(arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), arbitraries[0])
        self.assertEqual(SimpleNamespace(name='arbitrary#1', type='int', config={}), arbitraries[1])
        self.assertEqual(5, len(schema.transformers))
        expected_transformer_bob = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['bob'],
                                                   transformer=IdentityTransformer(1))
        expected_transformer_A = SimpleNamespace(name='transformer#1', inputs=['arbitrary#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#2', inputs=['arbitrary#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_A_copy = SimpleNamespace(name='transformer#3', inputs=['arbitrary#0'], outputs=['A'],
                                                      transformer=IdentityTransformer(1))
        expected_transformer_B_copy = SimpleNamespace(name='transformer#4', inputs=['arbitrary#1'], outputs=['B'],
                                                      transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_bob, schema.transformers[0])
        self.assertEqual(expected_transformer_A, schema.transformers[1])
        self.assertEqual(expected_transformer_B, schema.transformers[2])
        self.assertEqual(expected_transformer_A_copy, schema.transformers[3])
        self.assertEqual(expected_transformer_B_copy, schema.transformers[4])


class TestMakeSchemaExpr(unittest.TestCase):

    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema_expr('%int', ['A'], show_header=True, library=EmptyLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.arbitraries))
        self.assertEqual(SimpleNamespace(name='arbitrary#0', type='int', config={}), schema.arbitraries[0])
        self.assertEqual(1, len(schema.transformers))
        expected_transformer = SimpleNamespace(name='transformer#0', inputs=['arbitrary#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer, schema.transformers[0])

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema_expr('%int . %int', ['A', 'B'], show_header=True, library=EmptyLibrary())
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
        schema = make_schema_expr('let bob:=%int in @bob . %int', ['A', 'B'], show_header=True, library=EmptyLibrary())
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


class TestGetSchemaSizeAndLibraryParams(unittest.TestCase):
    def test_can_get_params_for_cmdline_with_number_of_rows(self):
        args = SimpleNamespace(
            library='builtin',
            global_configuration={},
            random_module=random,
            schema_definition_type='cmdline',
            columns=[('A', '@bob'), ('B', '%int')],
            expressions_defined=[('bob', '%int')],
            show_header=True,
            num_rows=10,
            stream_mode=None,
            num_bytes=None,
        )
        schema, library, size_dict = get_schema_size_and_library_params(args)

        self.assertIsInstance(library, BuiltInLibrary)
        self.assertIs(random, library.random_funcs)
        self.assertEqual({'number_of_rows': 10}, size_dict)

        # check resulting schema
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        self.assertEqual(5, len(schema.transformers))

    def test_can_get_params_for_cmdline_with_num_bytes(self):
        args = SimpleNamespace(
            library='builtin',
            global_configuration={},
            random_module=random,
            schema_definition_type='cmdline',
            columns=[('A', '@bob'), ('B', '%int')],
            expressions_defined=[('bob', '%int')],
            show_header=True,
            num_rows=None,
            stream_mode=None,
            num_bytes=128,
        )
        schema, library, size_dict = get_schema_size_and_library_params(args)

        self.assertIsInstance(library, BuiltInLibrary)
        self.assertIs(random, library.random_funcs)
        self.assertEqual({'byte_count': 128}, size_dict)

        # check resulting schema
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        self.assertEqual(5, len(schema.transformers))

    def test_can_get_params_for_cmdline_with_stream_mode(self):
        args = SimpleNamespace(
            library='builtin',
            global_configuration={},
            random_module=random,
            schema_definition_type='cmdline',
            columns=[('A', '@bob'), ('B', '%int')],
            expressions_defined=[('bob', '%int')],
            show_header=True,
            num_rows=None,
            stream_mode=True,
            num_bytes=None,
        )
        schema, library, size_dict = get_schema_size_and_library_params(args)

        self.assertIsInstance(library, BuiltInLibrary)
        self.assertIs(random, library.random_funcs)
        self.assertEqual({'stream_mode': True}, size_dict)

        # check resulting schema
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        self.assertEqual(5, len(schema.transformers))

    def test_can_get_params_for_expr_with_number_of_rows(self):
        args = SimpleNamespace(
            library='builtin',
            global_configuration={},
            random_module=random,
            schema_definition_type='expr',
            schema='%int . %int',
            columns_names='A,B',
            show_header=True,
            num_rows=10,
            stream_mode=None,
            num_bytes=None,
        )
        schema, library, size_dict = get_schema_size_and_library_params(args)

        self.assertIsInstance(library, BuiltInLibrary)
        self.assertIs(random, library.random_funcs)
        self.assertEqual({'number_of_rows': 10}, size_dict)

        # check resulting schema
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        self.assertEqual(2, len(schema.transformers))

    def test_can_get_params_for_expr_with_num_bytes(self):
        args = SimpleNamespace(
            library='builtin',
            global_configuration={},
            random_module=random,
            schema_definition_type='expr',
            schema='%int . %int',
            columns_names='A,B',
            show_header=True,
            num_rows=None,
            stream_mode=None,
            num_bytes=128,
        )
        schema, library, size_dict = get_schema_size_and_library_params(args)

        self.assertIsInstance(library, BuiltInLibrary)
        self.assertIs(random, library.random_funcs)
        self.assertEqual({'byte_count': 128}, size_dict)

        # check resulting schema
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        self.assertEqual(2, len(schema.transformers))

    def test_can_get_params_for_expr_with_stream_mode(self):
        args = SimpleNamespace(
            library='builtin',
            global_configuration={},
            random_module=random,
            schema_definition_type='expr',
            schema='%int . %int',
            columns_names='A,B',
            show_header=True,
            num_rows=None,
            stream_mode=True,
            num_bytes=None,
        )
        schema, library, size_dict = get_schema_size_and_library_params(args)

        self.assertIsInstance(library, BuiltInLibrary)
        self.assertIs(random, library.random_funcs)
        self.assertEqual({'stream_mode': True}, size_dict)

        # check resulting schema
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        self.assertEqual(2, len(schema.arbitraries))
        self.assertEqual(2, len(schema.transformers))

    def test_raises_error_with_invalid_schema_definition_type(self):
        args = SimpleNamespace(
            library='builtin',
            global_configuration={},
            random_module=random,
            schema_definition_type='invalid',
        )
        with self.assertRaises(ValueError):
            get_schema_size_and_library_params(args)


class TestGetLibrary(unittest.TestCase):
    def test_can_get_builtin_library(self):
        library = get_library('builtin', {}, random)
        self.assertIsInstance(library, BuiltInLibrary)
        self.assertEqual({}, library.global_configuration)
        self.assertIs(random, library.random_funcs)

    def test_raises_error_if_invalid_name(self):
        with self.assertRaises(ValueError):
            get_library('invalid', {}, random)


class TestParseGlobalConfiguration(unittest.TestCase):
    def test_can_parse_valid_configuration(self):
        config = _parse_global_configuration("{'int': {'min': 10, 'max': 5}}")
        self.assertEqual({'int': {'min': 10, 'max': 5}}, config)

    def test_raises_error_if_not_dict(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            _parse_global_configuration("[1,2,3]")
