import itertools as it
import random
import unittest

from feanor.builtin import BuiltInLibrary
from feanor.engine import Engine
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
