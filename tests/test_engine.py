import unittest
import itertools as it

from fake_random import FakeRandom
from feanor.engine import Engine
from feanor.schema import Schema


class TestEngine(unittest.TestCase):

    def setUp(self):
        values = list(reversed(range(5000)))
        # noinspection PyDefaultArgument
        config = {
            'random': {(): [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]},
            'randint': {
                'default': lambda a, b: values.pop() % b,
            }
        }
        self.rand = FakeRandom.from_dict(config)

    def test_can_build_a_generator_from_a_schema(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')
        schema.add_column('C', type='int')
        engine = Engine(schema, random_funcs=self.rand)

        self.assertEqual(3, engine.number_of_columns)
        self.assertEqual('int', engine.columns[0].type)
        self.assertEqual('int', engine.columns[1].type)
        self.assertEqual('int', engine.columns[2].type)

    def test_can_build_a_generator_from_a_schema_with_config(self):
        schema = Schema()
        schema.add_column('A', type='int', config={'lowerbound': 10})
        engine = Engine(schema, random_funcs=self.rand)

        self.assertEqual(1, engine.number_of_columns)
        self.assertEqual('int', engine.columns[0].type)
        self.assertEqual(10, engine.columns[0].config.lowerbound)

    def test_can_generate_arbitrary_data_with_number_of_rows(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')
        schema.add_column('C', type='int')
        engine = Engine(schema, random_funcs=self.rand)

        generated_values = list(engine.generate_data(number_of_rows=10))
        self.assertEqual(10, len(generated_values))
        iterable = iter(range(30))
        self.assertEqual(list(zip(iterable, iterable, iterable)), generated_values)
        self.assertEqual(10, len(set(generated_values)))

    def test_can_generate_stream_of_data(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')
        schema.add_column('C', type='int')
        engine = Engine(schema, random_funcs=self.rand)

        generated_values = list(it.islice(engine.generate_data(), 1000))
        self.assertEqual(1000, len(generated_values))
        iterable = iter(range(3000))
        self.assertEqual(list(zip(iterable, iterable, iterable)), generated_values)

    def test_can_generate_two_identical_columns_by_referencing_same_arbitrary(self):
        schema = Schema()
        schema.add_arbitrary('bob', type='int')
        schema.add_column('A', arbitrary='bob')
        schema.add_column('B', arbitrary='bob')

        engine = Engine(schema, random_funcs=self.rand)
        generated_values = list(engine.generate_data(number_of_rows=10))
        first_col, second_col = zip(*generated_values)
        self.assertEqual(first_col, second_col)

    def test_can_generate_two_identical_columns_by_referencing_name_of_auto_created_arbitrary(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', arbitrary='column#0')

        engine = Engine(schema, random_funcs=self.rand)
        generated_values = list(engine.generate_data(number_of_rows=10))
        first_col, second_col = zip(*generated_values)
        self.assertEqual(first_col, second_col)
