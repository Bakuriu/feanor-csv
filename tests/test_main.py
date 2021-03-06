import io
import os
import random
import argparse
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace

from feanor.builtin import BuiltInLibrary
from feanor.library import MockLibrary
from feanor.main import (
    make_schema_cmdline, get_library, _parse_global_configuration, make_schema_expr,
    get_schema_size_and_library_params,
    _parse_define,
)
from feanor.schema import IdentityTransformer


class TestMakeSchemaCmdline(unittest.TestCase):

    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema_cmdline([('A', '%int')], [], show_header=True, library=MockLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.producers))
        self.assertEqual(SimpleNamespace(name='producer#0', type='int', config={}), schema.producers[0])
        self.assertEqual(2, len(schema.transformers))
        expected_transformer = SimpleNamespace(name='transformer#0', inputs=['producer#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        expected_transformer_copy = SimpleNamespace(name='transformer#1', inputs=['producer#0'], outputs=['A'],
                                                    transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer, schema.transformers[0])
        self.assertEqual(expected_transformer_copy, schema.transformers[1])

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema_cmdline([('A', '%int'), ('B', '%int')], [], show_header=True, library=MockLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        producers = sorted(schema.producers, key=lambda x: x.name)
        self.assertEqual(2, len(producers))
        self.assertEqual(SimpleNamespace(name='producer#0', type='int', config={}), producers[0])
        self.assertEqual(SimpleNamespace(name='producer#1', type='int', config={}), producers[1])
        self.assertEqual(4, len(schema.transformers))
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['producer#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['producer#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_A_copy = SimpleNamespace(name='transformer#2', inputs=['producer#0'], outputs=['A'],
                                                      transformer=IdentityTransformer(1))
        expected_transformer_B_copy = SimpleNamespace(name='transformer#3', inputs=['producer#1'], outputs=['B'],
                                                      transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])
        self.assertEqual(expected_transformer_A_copy, schema.transformers[2])
        self.assertEqual(expected_transformer_B_copy, schema.transformers[3])

    def test_can_make_schema_with_transformers(self):
        schema = make_schema_cmdline([('A', '@bob'), ('B', '%int')], [('bob', '%int')], show_header=True,
                                     library=MockLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        producers = sorted(schema.producers, key=lambda x: x.name)
        self.assertEqual(2, len(producers))
        self.assertEqual(SimpleNamespace(name='producer#0', type='int', config={}), producers[0])
        self.assertEqual(SimpleNamespace(name='producer#1', type='int', config={}), producers[1])
        self.assertEqual(5, len(schema.transformers))
        expected_transformer_bob = SimpleNamespace(name='transformer#0', inputs=['producer#0'], outputs=['bob'],
                                                   transformer=IdentityTransformer(1))
        expected_transformer_A = SimpleNamespace(name='transformer#1', inputs=['producer#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#2', inputs=['producer#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_A_copy = SimpleNamespace(name='transformer#3', inputs=['producer#0'], outputs=['A'],
                                                      transformer=IdentityTransformer(1))
        expected_transformer_B_copy = SimpleNamespace(name='transformer#4', inputs=['producer#1'], outputs=['B'],
                                                      transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_bob, schema.transformers[0])
        self.assertEqual(expected_transformer_A, schema.transformers[1])
        self.assertEqual(expected_transformer_B, schema.transformers[2])
        self.assertEqual(expected_transformer_A_copy, schema.transformers[3])
        self.assertEqual(expected_transformer_B_copy, schema.transformers[4])


class TestMakeSchemaExpr(unittest.TestCase):

    def test_can_make_schema_with_a_single_column(self):
        schema = make_schema_expr('%int', ['A'], show_header=True, library=MockLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A',), schema.columns)
        self.assertEqual(1, len(schema.producers))
        self.assertEqual(SimpleNamespace(name='producer#0', type='int', config={}), schema.producers[0])
        self.assertEqual(1, len(schema.transformers))
        expected_transformer = SimpleNamespace(name='transformer#0', inputs=['producer#0'], outputs=['A'],
                                               transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer, schema.transformers[0])

    def test_can_make_schema_with_multiple_columns(self):
        schema = make_schema_expr('%int . %int', ['A', 'B'], show_header=True, library=MockLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        producers = sorted(schema.producers, key=lambda x: x.name)
        self.assertEqual(2, len(producers))
        self.assertEqual(SimpleNamespace(name='producer#0', type='int', config={}), producers[0])
        self.assertEqual(SimpleNamespace(name='producer#1', type='int', config={}), producers[1])
        self.assertEqual(2, len(schema.transformers))
        expected_transformer_A = SimpleNamespace(name='transformer#0', inputs=['producer#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#1', inputs=['producer#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_A, schema.transformers[0])
        self.assertEqual(expected_transformer_B, schema.transformers[1])

    def test_can_make_schema_with_transformers(self):
        schema = make_schema_expr('let bob:=%int in @bob . %int', ['A', 'B'], show_header=True, library=MockLibrary())
        self.assertTrue(schema.show_header)
        self.assertEqual(('A', 'B'), schema.columns)
        producers = sorted(schema.producers, key=lambda x: x.name)
        self.assertEqual(2, len(producers))
        self.assertEqual(SimpleNamespace(name='producer#0', type='int', config={}), producers[0])
        self.assertEqual(SimpleNamespace(name='producer#1', type='int', config={}), producers[1])
        self.assertEqual(3, len(schema.transformers))
        expected_transformer_bob = SimpleNamespace(name='transformer#0', inputs=['producer#0'], outputs=['bob'],
                                                   transformer=IdentityTransformer(1))
        expected_transformer_A = SimpleNamespace(name='transformer#1', inputs=['producer#0'], outputs=['A'],
                                                 transformer=IdentityTransformer(1))
        expected_transformer_B = SimpleNamespace(name='transformer#2', inputs=['producer#1'], outputs=['B'],
                                                 transformer=IdentityTransformer(1))
        self.assertEqual(expected_transformer_bob, schema.transformers[0])
        self.assertEqual(expected_transformer_A, schema.transformers[1])
        self.assertEqual(expected_transformer_B, schema.transformers[2])


class TestGetSchemaSizeAndLibraryParams(unittest.TestCase):
    def test_can_get_params_for_cmdline_with_number_of_rows(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
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
        self.assertEqual(2, len(schema.producers))
        self.assertEqual(5, len(schema.transformers))

    def test_can_get_params_for_cmdline_with_num_bytes(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
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
        self.assertEqual(2, len(schema.producers))
        self.assertEqual(5, len(schema.transformers))

    def test_can_get_params_for_cmdline_with_stream_mode(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
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
        self.assertEqual(2, len(schema.producers))
        self.assertEqual(5, len(schema.transformers))

    def test_can_get_params_for_expr_with_number_of_rows(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
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
        self.assertEqual(2, len(schema.producers))
        self.assertEqual(2, len(schema.transformers))

    def test_can_get_params_for_expr_with_num_bytes(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
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
        self.assertEqual(2, len(schema.producers))
        self.assertEqual(2, len(schema.transformers))

    def test_can_get_params_for_expr_with_stream_mode(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
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
        self.assertEqual(2, len(schema.producers))
        self.assertEqual(2, len(schema.transformers))

    def test_raises_error_with_invalid_schema_definition_type(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
            schema_definition_type='invalid',
        )
        with self.assertRaises(ValueError):
            get_schema_size_and_library_params(args)

    def test_can_set_random_seed(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=0,
            schema_definition_type='cmdline',
            columns=[('A', '@bob'), ('B', '%int')],
            expressions_defined=[('bob', '%int')],
            show_header=True,
            num_rows=10,
            stream_mode=None,
            num_bytes=None,
        )
        _, library, _ = get_schema_size_and_library_params(args)
        self.assertEqual(0.8444218515250481, library.random_funcs.random())
        self.assertEqual(0.7579544029403025, library.random_funcs.random())
        self.assertEqual(0.420571580830845, library.random_funcs.random())

    def test_can_omit_column_names(self):
        args = SimpleNamespace(
            library='feanor.builtin',
            global_configuration={},
            define={},
            random_module=random,
            random_seed=None,
            schema_definition_type='expr',
            schema='%int . %int',
            columns_names='',
            show_header=False,
            num_rows=1,
            stream_mode=False,
            num_bytes=None,
        )
        schema, _, _ = get_schema_size_and_library_params(args)
        self.assertEqual(('column#0', 'column#1'), schema.columns)


class TestGetLibrary(unittest.TestCase):
    def setUp(self):
        self.fake_modules_dir = os.path.join(os.path.dirname(__file__), 'fake_modules')

    def test_can_get_builtin_library(self):
        library = get_library('feanor.builtin', {}, {}, random)
        self.assertIsInstance(library, BuiltInLibrary)
        self.assertEqual({}, library.global_configuration)
        self.assertIs(random, library.random_funcs)

    def test_exits_with_code_one_error_if_invalid_name(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            get_library('invalid', {}, {}, random)
        self.assertEqual(1, e.exception.code)

    def test_exits_with_code_one_error_if_library_requests_exit_during_import(self):
        output = io.StringIO()
        with redirect_stderr(output) as new_stderr, self.assertRaises(SystemExit) as e:
            get_library(os.path.join(self.fake_modules_dir, 'fake_library_exits.py'), {}, {}, random)
        self.assertEqual(1, e.exception.code)
        self.assertRegex(new_stderr.getvalue(),
                         r"Exit requested while importing library '[^']+/fake_library_exits.py'. Exit code 7")

    def test_exits_with_code_one_error_if_library_raises_exception_during_import(self):
        output = io.StringIO()
        with redirect_stderr(output) as new_stderr, self.assertRaises(SystemExit) as e:
            get_library(os.path.join(self.fake_modules_dir, 'fake_library_exception.py'), {}, {}, random)
        self.assertEqual(1, e.exception.code)
        self.assertRegex(new_stderr.getvalue(),
                         r"Exception while importing library '[^']+/fake_library_exception.py'.\nException: error!\n")

    def test_exits_with_code_one_error_if_library_raises_fatal_error_during_import(self):
        output = io.StringIO()
        with redirect_stderr(output) as new_stderr, self.assertRaises(SystemExit) as e:
            get_library(os.path.join(self.fake_modules_dir, 'fake_library_fatal_error.py'), {}, {}, random)
        self.assertEqual(1, e.exception.code)
        self.assertRegex(new_stderr.getvalue(),
                         r"Fatal error while importing library '[^']+/fake_library_fatal_error.py'.\nBaseException: fatal error!\n")

    def test_exits_with_code_one_error_if_library_raises_exception_during_initialization(self):
        output = io.StringIO()
        with redirect_stderr(output) as new_stderr, self.assertRaises(SystemExit) as e:
            get_library(os.path.join(self.fake_modules_dir, 'fake_library_exception_on_init.py'), {}, {}, random)
        self.assertEqual(1, e.exception.code)
        self.assertRegex(new_stderr.getvalue(),
                         r"Exception while initializing library '[^']+/fake_library_exception_on_init.py'.\nException: error!\n")

    def test_exits_with_code_one_error_if_library_raises_fatal_error_during_initialization(self):
        output = io.StringIO()
        with redirect_stderr(output) as new_stderr, self.assertRaises(SystemExit) as e:
            get_library(os.path.join(self.fake_modules_dir, 'fake_library_fatal_error_on_init.py'), {}, {}, random)
        self.assertEqual(1, e.exception.code)
        self.assertRegex(new_stderr.getvalue(),
                         r"Fatal error while initializing library '[^']+/fake_library_fatal_error_on_init.py'.\nBaseException: fatal error!\n")


class TestParseGlobalConfiguration(unittest.TestCase):
    def test_can_parse_valid_configuration(self):
        config = _parse_global_configuration("{'int': {'min': 10, 'max': 5}}")
        self.assertEqual({'int': {'min': 10, 'max': 5}}, config)

    def test_raises_error_if_not_dict(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            _parse_global_configuration("[1,2,3]")


class TestParseDefine(unittest.TestCase):
    def test_can_parse_a_define_without_configuration(self):
        define = _parse_define("a := %int")
        self.assertEqual({'a': {'producer': 'int', 'config': {}}}, define)

    def test_can_parse_a_define_with_configuration(self):
        define = _parse_define("a := %int{'max': 10}")
        self.assertEqual({'a': {'producer': 'int', 'config': {'max': 10}}}, define)

    def test_can_parse_multiple_defines(self):
        define = _parse_define("a := %int\nb := %float")
        expected = {
            'a': {'producer': 'int', 'config': {}},
            'b': {'producer': 'float', 'config': {}},
        }
        self.assertEqual(expected, define)

    def test_raises_error_if_invalid_define(self):
        invalid_expressions = [
            'int = %int',
            'completely wrong',
            'int := %int{"v": 5',
        ]
        for invalid_expression in invalid_expressions:
            with self.assertRaises(argparse.ArgumentTypeError):
                _parse_define(invalid_expression)

    def test_raises_error_if_multiple_definitions_of_same_name(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            _parse_define('a := %int\n a := %float')
