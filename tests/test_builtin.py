import random
import time
import unittest
from calendar import timegm
from datetime import datetime, timezone
from itertools import cycle, islice

from feanor.builtin import *


class TestIntProducer(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_number(self):
        producer = IntProducer(random_funcs=self.rand)
        self.assertIsInstance(producer(), int)

    def test_generates_different_numbers(self):
        producer = IntProducer(random_funcs=self.rand)
        a = producer()
        b = producer()
        self.assertIsInstance(a, int)
        self.assertIsInstance(b, int)
        self.assertEqual(self.rand_copy.randint(0, 1_000_000), a)
        self.assertEqual(self.rand_copy.randint(0, 1_000_000), b)

    def test_can_specify_min(self):
        producer = IntProducer(random_funcs=self.rand, config={'min': 10})
        self.assertEqual(10, producer.config.min)

    def test_can_specify_max(self):
        producer = IntProducer(random_funcs=self.rand, config={'max': 10})
        self.assertEqual(10, producer.config.max)

    def test_can_specify_bounds(self):
        producer = IntProducer(random_funcs=self.rand, config={'min': 10, 'max': 11})
        self.assertEqual(10, producer.config.min)
        self.assertEqual(11, producer.config.max)

    def test_max_bound_is_respected(self):
        producer = IntProducer(random_funcs=self.rand, config={'max': 10})
        got = {producer() for _ in range(25)}
        self.assertEqual(set(range(10)), got)
        got.add(producer())
        self.assertEqual(set(range(11)), got)


class TestFloatProducer(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)

    def test_can_generate_a_random_number(self):
        producer = FloatProducer(random_funcs=self.rand, config={'distribution': 'random'})
        self.assertIsInstance(producer(), float)

    def test_generates_different_numbers(self):
        producer = FloatProducer(random_funcs=self.rand, config={'distribution': 'random'})
        a = producer()
        b = producer()
        self.assertIsInstance(a, float)
        self.assertIsInstance(b, float)
        self.assertNotEqual(a, b)

    def test_can_specify_min(self):
        producer = FloatProducer(random_funcs=self.rand, config={'min': 10, 'distribution': 'uniform'})
        self.assertEqual(10, producer.config.min)

    def test_can_specify_max(self):
        producer = FloatProducer(random_funcs=self.rand, config={'max': 10, 'distribution': 'uniform'})
        self.assertEqual(10, producer.config.max)

    def test_can_specify_bounds(self):
        producer = FloatProducer(random_funcs=self.rand, config={'min': 10, 'max': 11, 'distribution': 'uniform'})
        self.assertEqual(10, producer.config.min)
        self.assertEqual(11, producer.config.max)

    def test_raises_error_if_passed_invalid_distribution(self):
        with self.assertRaises(ValueError):
            FloatProducer(random_funcs=self.rand, config={'distribution': 'invalid'})


class TestFixedProducer(unittest.TestCase):
    def test_always_returns_same_value(self):
        producer = FixedProducer(random.Random(0), config={'value': 5})
        self.assertEqual([5] * 10, [producer() for _ in range(10)])


class TestCyclingProducer(unittest.TestCase):
    def test_always_returns_same_value(self):
        producer = CyclingProducer(random.Random(0), config={'values': range(5)})
        self.assertEqual(list(islice(cycle(range(5)), 20)), [producer() for _ in range(20)])


class TestRepeaterProducer(unittest.TestCase):
    def test_can_repeat_value(self):
        orig_producer = CyclingProducer(random.Random(0), {'values': range(3)})
        producer = RepeaterProducer(random.Random(0), orig_producer, {'num_repeats': 3})
        self.assertEqual([0, 0, 0, 1, 1, 1, 2, 2, 2], [producer() for _ in range(9)])


class TestStringProducer(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_string(self):
        producer = StringProducer(random_funcs=self.rand, config={'characters': {'a', 'b'}})
        self.assertIsInstance(producer(), str)

    def test_generates_different_strings(self):
        producer = StringProducer(random_funcs=self.rand)
        a = producer()
        b = producer()
        self.assertIsInstance(a, str)
        self.assertIsInstance(b, str)
        self.assertNotEqual(a, b)

    def test_string_contains_only_selected_characters(self):
        producer = StringProducer(random_funcs=self.rand, config={'len': 1000, 'characters': 'abc'})
        self.assertEqual({'a', 'b', 'c'}, set(producer()))

    def test_string_is_of_specified_length(self):
        producer = StringProducer(random_funcs=self.rand, config={'len': 10})
        for _ in range(10):
            self.assertEqual(10, len(producer()))

    def test_can_specify_length_range(self):
        producer = StringProducer(random_funcs=self.rand, config={'min_len': 1, 'max_len': 5})
        got = {len(producer()) for _ in range(20)}
        self.assertEqual(set(range(1, 6)), got)


class TestAlphaProducer(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_string(self):
        producer = AlphaProducer(random_funcs=self.rand)
        self.assertIsInstance(producer(), str)

    def test_generates_different_strings(self):
        producer = AlphaProducer(random_funcs=self.rand)
        a = producer()
        b = producer()
        self.assertIsInstance(a, str)
        self.assertIsInstance(b, str)
        self.assertNotEqual(a, b)

    def test_string_contains_only_selected_characters(self):
        producer = AlphaProducer(random_funcs=self.rand, config={'len': 1000})
        self.assertTrue(producer().isalpha())

    def test_string_is_of_specified_length(self):
        producer = AlphaProducer(random_funcs=self.rand, config={'len': 10})
        for _ in range(10):
            self.assertEqual(10, len(producer()))

    def test_can_specify_length_range(self):
        producer = StringProducer(random_funcs=self.rand, config={'min_len': 1, 'max_len': 5})
        got = {len(producer()) for _ in range(20)}
        self.assertEqual(set(range(1, 6)), got)


class TestAlphaNumericProducer(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_string(self):
        producer = AlphaNumericProducer(random_funcs=self.rand)
        self.assertIsInstance(producer(), str)

    def test_generates_different_strings(self):
        producer = AlphaNumericProducer(random_funcs=self.rand)
        a = producer()
        b = producer()
        self.assertIsInstance(a, str)
        self.assertIsInstance(b, str)
        self.assertNotEqual(a, b)

    def test_string_contains_only_selected_characters(self):
        producer = AlphaNumericProducer(random_funcs=self.rand, config={'len': 1000})
        self.assertTrue(producer().isalnum())
        self.assertFalse(producer().isalpha())

    def test_string_is_of_specified_length(self):
        producer = AlphaNumericProducer(random_funcs=self.rand, config={'len': 10})
        for _ in range(10):
            self.assertEqual(10, len(producer()))

    def test_can_specify_length_range(self):
        producer = AlphaNumericProducer(random_funcs=self.rand, config={'min_len': 1, 'max_len': 5})
        got = {len(producer()) for _ in range(20)}
        self.assertEqual(set(range(1, 6)), got)


class TestDateProducer(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)
        self.start_ts = timegm(datetime(2018, 1, 1, tzinfo=timezone.utc).utctimetuple())
        self.end_ts = timegm(datetime(2018, 12, 31, 23, 59, 59, tzinfo=timezone.utc).utctimetuple())

    def test_can_generate_a_random_date(self):
        producer = DateProducer(random_funcs=self.rand, config={'min_year': 2018, 'max_year': 2018})
        self.assertIsInstance(producer(), datetime)

    def test_generates_different_dates(self):
        producer = DateProducer(random_funcs=self.rand, config={'min_year': 2018, 'max_year': 2018})
        a = producer()
        b = producer()
        self.assertIsInstance(a, datetime)
        self.assertIsInstance(b, datetime)
        self.assertNotEqual(a, b)

    def test_date_only_generates_selected_time_range(self):
        producer = DateProducer(random_funcs=self.rand, config={'min_year': 2018, 'max_year': 2018})
        got_years = {producer().year for _ in range(10000)}
        self.assertEqual({2018}, got_years)

    def test_date_only_generates_selected_time_range_with_slice(self):
        producer = DateProducer(random_funcs=self.rand, config={
            'min_year': 2018, 'max_year': 2018, 'mode': 'slice', 'min_hour': 3, 'max_hour': 7
        })
        got_hours = {producer().hour for _ in range(10000)}
        self.assertEqual({3, 4, 5, 6, 7}, got_hours)

    def test_can_generate_a_random_date_with_min_max_ts(self):
        producer = DateProducer(random_funcs=self.rand, config={'min_ts': self.start_ts, 'max_ts': self.end_ts})
        self.assertIsInstance(producer(), datetime)

    def test_generates_different_dates_with_min_max_ts(self):
        producer = DateProducer(random_funcs=self.rand, config={'min_ts': self.start_ts, 'max_ts': self.end_ts})
        a = producer()
        b = producer()
        self.assertIsInstance(a, datetime)
        self.assertIsInstance(b, datetime)
        self.assertNotEqual(a, b)

    def test_date_only_generates_selected_time_range_with_min_max_ts(self):
        producer = DateProducer(random_funcs=self.rand, config={'min_ts': self.start_ts, 'max_ts': self.end_ts})
        got_years = {producer().year for _ in range(10000)}
        self.assertEqual({2018}, got_years)

    def test_date_only_generates_selected_time_range_with_slice_with_min_max_ts(self):
        producer = DateProducer(random_funcs=self.rand, config={
            'min_ts': self.start_ts, 'max_ts': self.end_ts, 'mode': 'slice', 'min_hour': 3, 'max_hour': 7
        })
        got_hours = {producer().hour for _ in range(10000)}
        self.assertEqual({3, 4, 5, 6, 7}, got_hours)



    def test_raises_error_if_mode_is_invalid(self):
        with self.assertRaises(ValueError):
            DateProducer(random_funcs=self.rand, config={'mode': 'invalid'})
