import random
import time
import unittest
from calendar import timegm
from datetime import datetime, timezone
from itertools import cycle, islice

from feanor.builtin import *


class TestIntArbitrary(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_number(self):
        arbitrary = IntArbitrary(random_funcs=self.rand)
        self.assertIsInstance(arbitrary(), int)

    def test_generates_different_numbers(self):
        arbitrary = IntArbitrary(random_funcs=self.rand)
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, int)
        self.assertIsInstance(b, int)
        self.assertEqual(self.rand_copy.randint(0, 1_000_000), a)
        self.assertEqual(self.rand_copy.randint(0, 1_000_000), b)

    def test_can_specify_min(self):
        arbitrary = IntArbitrary(random_funcs=self.rand, config={'min': 10})
        self.assertEqual(10, arbitrary.config.min)

    def test_can_specify_max(self):
        arbitrary = IntArbitrary(random_funcs=self.rand, config={'max': 10})
        self.assertEqual(10, arbitrary.config.max)

    def test_can_specify_bounds(self):
        arbitrary = IntArbitrary(random_funcs=self.rand, config={'min': 10, 'max': 11})
        self.assertEqual(10, arbitrary.config.min)
        self.assertEqual(11, arbitrary.config.max)

    def test_max_bound_is_respected(self):
        arbitrary = IntArbitrary(random_funcs=self.rand, config={'max': 10})
        got = {arbitrary() for _ in range(25)}
        self.assertEqual(set(range(10)), got)
        got.add(arbitrary())
        self.assertEqual(set(range(11)), got)


class TestFloatArbitrary(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)

    def test_can_generate_a_random_number(self):
        arbitrary = FloatArbitrary(random_funcs=self.rand, config={'distribution': 'random'})
        self.assertIsInstance(arbitrary(), float)

    def test_generates_different_numbers(self):
        arbitrary = FloatArbitrary(random_funcs=self.rand, config={'distribution': 'random'})
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, float)
        self.assertIsInstance(b, float)
        self.assertNotEqual(a, b)

    def test_can_specify_min(self):
        arbitrary = FloatArbitrary(random_funcs=self.rand, config={'min': 10, 'distribution': 'uniform'})
        self.assertEqual(10, arbitrary.config.min)

    def test_can_specify_max(self):
        arbitrary = FloatArbitrary(random_funcs=self.rand, config={'max': 10, 'distribution': 'uniform'})
        self.assertEqual(10, arbitrary.config.max)

    def test_can_specify_bounds(self):
        arbitrary = FloatArbitrary(random_funcs=self.rand, config={'min': 10, 'max': 11, 'distribution': 'uniform'})
        self.assertEqual(10, arbitrary.config.min)
        self.assertEqual(11, arbitrary.config.max)

    def test_raises_error_if_passed_invalid_distribution(self):
        with self.assertRaises(ValueError):
            FloatArbitrary(random_funcs=self.rand, config={'distribution': 'invalid'})


class TestFixedArbitrary(unittest.TestCase):
    def test_always_returns_same_value(self):
        arbitrary = FixedArbitrary(random.Random(0), config={'value': 5})
        self.assertEqual([5] * 10, [arbitrary() for _ in range(10)])


class TestCyclingArbitrary(unittest.TestCase):
    def test_always_returns_same_value(self):
        arbitrary = CyclingArbitrary(random.Random(0), config={'values': range(5)})
        self.assertEqual(list(islice(cycle(range(5)), 20)), [arbitrary() for _ in range(20)])


class TestRepeaterArbitrary(unittest.TestCase):
    def test_can_repeat_value(self):
        orig_arbitrary = CyclingArbitrary(random.Random(0), {'values': range(3)})
        arbitrary = RepeaterArbitrary(random.Random(0), orig_arbitrary, {'num_repeats': 3})
        self.assertEqual([0, 0, 0, 1, 1, 1, 2, 2, 2], [arbitrary() for _ in range(9)])


class TestStringArbitrary(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_string(self):
        arbitrary = StringArbitrary(random_funcs=self.rand, config={'characters': {'a', 'b'}})
        self.assertIsInstance(arbitrary(), str)

    def test_generates_different_strings(self):
        arbitrary = StringArbitrary(random_funcs=self.rand)
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, str)
        self.assertIsInstance(b, str)
        self.assertNotEqual(a, b)

    def test_string_contains_only_selected_characters(self):
        arbitrary = StringArbitrary(random_funcs=self.rand, config={'len': 1000, 'characters': 'abc'})
        self.assertEqual({'a', 'b', 'c'}, set(arbitrary()))

    def test_string_is_of_specified_length(self):
        arbitrary = StringArbitrary(random_funcs=self.rand, config={'len': 10})
        for _ in range(10):
            self.assertEqual(10, len(arbitrary()))

    def test_can_specify_length_range(self):
        arbitrary = StringArbitrary(random_funcs=self.rand, config={'min_len': 1, 'max_len': 5})
        got = {len(arbitrary()) for _ in range(20)}
        self.assertEqual(set(range(1, 6)), got)


class TestAlphaArbitrary(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_string(self):
        arbitrary = AlphaArbitrary(random_funcs=self.rand)
        self.assertIsInstance(arbitrary(), str)

    def test_generates_different_strings(self):
        arbitrary = AlphaArbitrary(random_funcs=self.rand)
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, str)
        self.assertIsInstance(b, str)
        self.assertNotEqual(a, b)

    def test_string_contains_only_selected_characters(self):
        arbitrary = AlphaArbitrary(random_funcs=self.rand, config={'len': 1000})
        self.assertTrue(arbitrary().isalpha())

    def test_string_is_of_specified_length(self):
        arbitrary = AlphaArbitrary(random_funcs=self.rand, config={'len': 10})
        for _ in range(10):
            self.assertEqual(10, len(arbitrary()))

    def test_can_specify_length_range(self):
        arbitrary = StringArbitrary(random_funcs=self.rand, config={'min_len': 1, 'max_len': 5})
        got = {len(arbitrary()) for _ in range(20)}
        self.assertEqual(set(range(1, 6)), got)


class TestAlphaNumericArbitrary(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)

    def test_can_generate_a_random_string(self):
        arbitrary = AlphaNumericArbitrary(random_funcs=self.rand)
        self.assertIsInstance(arbitrary(), str)

    def test_generates_different_strings(self):
        arbitrary = AlphaNumericArbitrary(random_funcs=self.rand)
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, str)
        self.assertIsInstance(b, str)
        self.assertNotEqual(a, b)

    def test_string_contains_only_selected_characters(self):
        arbitrary = AlphaNumericArbitrary(random_funcs=self.rand, config={'len': 1000})
        self.assertTrue(arbitrary().isalnum())
        self.assertFalse(arbitrary().isalpha())

    def test_string_is_of_specified_length(self):
        arbitrary = AlphaNumericArbitrary(random_funcs=self.rand, config={'len': 10})
        for _ in range(10):
            self.assertEqual(10, len(arbitrary()))

    def test_can_specify_length_range(self):
        arbitrary = AlphaNumericArbitrary(random_funcs=self.rand, config={'min_len': 1, 'max_len': 5})
        got = {len(arbitrary()) for _ in range(20)}
        self.assertEqual(set(range(1, 6)), got)


class TestDateArbitrary(unittest.TestCase):
    def setUp(self):
        self.rand = random.Random(0)
        self.rand_copy = random.Random(0)
        self.start_ts = timegm(datetime(2018, 1, 1, tzinfo=timezone.utc).utctimetuple())
        self.end_ts = timegm(datetime(2018, 12, 31, 23, 59, 59, tzinfo=timezone.utc).utctimetuple())

    def test_can_generate_a_random_date(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={'min_year': 2018, 'max_year': 2018})
        self.assertIsInstance(arbitrary(), datetime)

    def test_generates_different_dates(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={'min_year': 2018, 'max_year': 2018})
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, datetime)
        self.assertIsInstance(b, datetime)
        self.assertNotEqual(a, b)

    def test_date_only_generates_selected_time_range(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={'min_year': 2018, 'max_year': 2018})
        got_years = {arbitrary().year for _ in range(10000)}
        self.assertEqual({2018}, got_years)

    def test_date_only_generates_selected_time_range_with_slice(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={
            'min_year': 2018, 'max_year': 2018, 'mode': 'slice', 'min_hour': 3, 'max_hour': 7
        })
        got_hours = {arbitrary().hour for _ in range(10000)}
        self.assertEqual({3, 4, 5, 6, 7}, got_hours)

    def test_can_generate_a_random_date_with_min_max_ts(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={'min_ts': self.start_ts, 'max_ts': self.end_ts})
        self.assertIsInstance(arbitrary(), datetime)

    def test_generates_different_dates_with_min_max_ts(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={'min_ts': self.start_ts, 'max_ts': self.end_ts})
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, datetime)
        self.assertIsInstance(b, datetime)
        self.assertNotEqual(a, b)

    def test_date_only_generates_selected_time_range_with_min_max_ts(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={'min_ts': self.start_ts, 'max_ts': self.end_ts})
        got_years = {arbitrary().year for _ in range(10000)}
        self.assertEqual({2018}, got_years)

    def test_date_only_generates_selected_time_range_with_slice_with_min_max_ts(self):
        arbitrary = DateArbitrary(random_funcs=self.rand, config={
            'min_ts': self.start_ts, 'max_ts': self.end_ts, 'mode': 'slice', 'min_hour': 3, 'max_hour': 7
        })
        got_hours = {arbitrary().hour for _ in range(10000)}
        self.assertEqual({3, 4, 5, 6, 7}, got_hours)



    def test_raises_error_if_mode_is_invalid(self):
        with self.assertRaises(ValueError):
            DateArbitrary(random_funcs=self.rand, config={'mode': 'invalid'})
