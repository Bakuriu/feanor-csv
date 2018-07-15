import unittest
from itertools import cycle, islice

from fake_random import FakeRandom
from feanor.types.builtin import IntArbitrary, MultiArbitrary, FixedArbitrary, CyclingArbitrary, RepeaterArbitrary


class TestIntArbitrary(unittest.TestCase):
    def setUp(self):
        values = list(reversed(range(100)))
        config = {
            'random': {(): [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]},
            'randint': {'default': lambda a, b: values.pop() % b}
        }
        self.rand = FakeRandom.from_dict(config)

    def test_can_generate_a_random_number(self):
        arbitrary = IntArbitrary(random_funcs=self.rand)
        self.assertIsInstance(arbitrary(), int)

    def test_generates_different_numbers(self):
        arbitrary = IntArbitrary(random_funcs=self.rand)
        a = arbitrary()
        b = arbitrary()
        self.assertIsInstance(a, int)
        self.assertIsInstance(b, int)
        self.assertNotEqual(a, b)

    def test_can_specify_lowerbound(self):
        arbitrary = IntArbitrary(random_funcs=self.rand, config={'lowerbound': 10})
        self.assertEqual(arbitrary.config.lowerbound, 10)

    def test_can_specify_upperbound(self):
        arbitrary = IntArbitrary(random_funcs=self.rand, config={'upperbound': 10})
        self.assertEqual(arbitrary.config.upperbound, 10)

    def test_can_specify_bounds(self):
        arbitrary = IntArbitrary(random_funcs=self.rand, config={'lowerbound': 10, 'upperbound': 11})
        self.assertEqual(arbitrary.config.lowerbound, 10)
        self.assertEqual(arbitrary.config.upperbound, 11)


class TestMultiArbitrary(unittest.TestCase):
    def setUp(self):
        values = list(reversed(range(100)))
        config = {
            'random': {(): [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]},
            'randint': {'default': lambda a, b: values.pop() % b}
        }
        self.rand = FakeRandom.from_dict(config)

    def test_can_combine_multiple_arbitraries(self):
        arbitrary = MultiArbitrary(self.rand,
                                   [IntArbitrary(random_funcs=self.rand), IntArbitrary(random_funcs=self.rand)])
        value = arbitrary()
        self.assertIsInstance(value, tuple)
        self.assertEqual(len(value), 2)
        self.assertIsInstance(value[0], int)
        self.assertIsInstance(value[1], int)
        self.assertNotEqual(value[0], value[1])


class TestFixedArbitrary(unittest.TestCase):
    def test_always_returns_same_value(self):
        arbitrary = FixedArbitrary(FakeRandom(), config={'value': 5})
        self.assertEqual([arbitrary() for _ in range(10)], [5] * 10)


class TestCyclingArbitrary(unittest.TestCase):
    def test_always_returns_same_value(self):
        arbitrary = CyclingArbitrary(FakeRandom(), config={'values': range(5)})
        self.assertEqual([arbitrary() for _ in range(20)], list(islice(cycle(range(5)), 20)))


class TestRepeaterArbitrary(unittest.TestCase):
    def test_can_repeat_value(self):
        orig_arbitrary = CyclingArbitrary(FakeRandom(), {'values': range(3)})
        arbitrary = RepeaterArbitrary(FakeRandom(), orig_arbitrary, {'num_repeats': 3})
        self.assertEqual([arbitrary() for _ in range(9)], [0, 0, 0, 1, 1, 1, 2, 2, 2])
