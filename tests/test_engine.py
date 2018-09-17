import itertools as it
import random
import unittest
from io import StringIO
from unittest import mock

from feanor.builtin import BuiltInLibrary
from feanor.engine import *
from feanor.schema import Schema


class TestEngine(unittest.TestCase):

    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)
        self.library = BuiltInLibrary({}, self.rand)

    def test_can_build_a_generator_from_a_schema(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        engine = Engine(schema, self.library)

        self.assertEqual(3, engine.number_of_columns)
        values = list(engine.generate_data(1))
        self.assertEqual(1, len(values))
        expected_values = tuple(self.rand_copy.randint(0, 1_000_000) for _ in range(3))
        self.assertEqual(expected_values, values[0])

    def test_can_build_a_generator_from_a_schema_with_config(self):
        schema = Schema()
        schema.define_column('A', type='int', config={'min': 10})
        engine = Engine(schema, self.library)

        self.assertEqual(1, engine.number_of_columns)
        values = set(engine.generate_data(20))
        expected_values = {(self.rand_copy.randint(10, 1_000_000),) for _ in range(20)}
        self.assertEqual(expected_values, values)

    def test_can_generate_arbitrary_data_with_number_of_rows(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        engine = Engine(schema, self.library)

        generated_values = list(engine.generate_data(number_of_rows=10))
        self.assertEqual(10, len(generated_values))
        iterable = (self.rand_copy.randint(0, 1_000_000) for _ in range(30))
        self.assertEqual(list(zip(iterable, iterable, iterable)), generated_values)
        self.assertEqual(10, len(set(generated_values)))

    def test_can_generate_stream_of_data(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        engine = Engine(schema, self.library)

        generated_values = list(it.islice(engine.generate_data(), 1000))
        self.assertEqual(1000, len(generated_values))
        iterable = (self.rand_copy.randint(0, 1_000_000) for _ in range(3000))
        self.assertEqual(list(zip(iterable, iterable, iterable)), generated_values)

    def test_can_generate_two_identical_columns_by_referencing_same_arbitrary(self):
        schema = Schema()
        schema.add_arbitrary('bob', type='int')
        schema.define_column('A', arbitrary='bob')
        schema.define_column('B', arbitrary='bob')

        engine = Engine(schema, self.library)
        generated_values = list(engine.generate_data(number_of_rows=10))
        first_col, second_col = zip(*generated_values)
        self.assertEqual(first_col, second_col)

    def test_can_generate_two_identical_columns_by_referencing_name_of_auto_created_arbitrary(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', arbitrary='A')

        engine = Engine(schema, self.library)
        generated_values = list(engine.generate_data(number_of_rows=10))
        first_col, second_col = zip(*generated_values)
        self.assertEqual(first_col, second_col)


class TestFacade(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)
        self.library = BuiltInLibrary({}, self.rand)

    def test_generate_data_raises_if_missing_size_parameters(self):
        with self.assertRaises(TypeError):
            generate_data(Schema(), self.library, mock.MagicMock())

    def test_generate_data_raises_if_both_num_rows_and_num_bytes_are_specified(self):
        with self.assertRaises(TypeError):
            generate_data(Schema(), self.library, mock.MagicMock(), number_of_rows=10, byte_count=100)

    def test_can_generate_some_data(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        saved_data = StringIO()
        generate_data(schema, self.library, saved_data, number_of_rows=1)
        lines = saved_data.getvalue()
        expected_values = tuple(self.rand_copy.randint(0, 1_000_000) for _ in range(3))
        self.assertEqual(2, len(lines.splitlines()))
        self.assertEqual(['A,B,C', ','.join(map(str, expected_values))], lines.splitlines())

    def test_can_generate_some_data_no_header(self):
        schema = Schema(show_header=False)
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        saved_data = StringIO()
        generate_data(schema, self.library, saved_data, number_of_rows=1)
        lines = saved_data.getvalue()
        expected_values = tuple(self.rand_copy.randint(0, 1_000_000) for _ in range(3))
        self.assertEqual(1, len(lines.splitlines()))
        self.assertEqual([','.join(map(str, expected_values))], lines.splitlines())

    def test_can_generate_some_data_no_header_byte_count(self):
        schema = Schema(show_header=False)
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        saved_data = StringIO()
        generate_data(schema, self.library, saved_data, byte_count=128)
        lines = saved_data.getvalue()
        expected_values = [','.join(map(str, (self.rand_copy.randint(0, 1_000_000) for _ in range(3)))) for _ in
                           range(7)]
        self.assertEqual(7, len(lines.splitlines()))
        self.assertEqual(expected_values, lines.splitlines())

    def test_can_generate_some_data_bytecount(self):
        schema = Schema()
        schema.define_column('A', type='int')
        schema.define_column('B', type='int')
        schema.define_column('C', type='int')
        saved_data = StringIO()
        generate_data(schema, self.library, saved_data, byte_count=128)
        lines = saved_data.getvalue()
        expected_values = [','.join(map(str, (self.rand_copy.randint(0, 1_000_000) for _ in range(3)))) for _ in
                           range(6)]
        self.assertEqual(7, len(lines.splitlines()))
        self.assertEqual(['A,B,C'] + expected_values, lines.splitlines())
