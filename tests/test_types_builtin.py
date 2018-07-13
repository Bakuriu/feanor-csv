import unittest

from fake_random import FakeRandom
from feanor.types.builtin import IntArbitrary, MultiArbitrary


class TestIntArbitrary(unittest.TestCase):
    def setUp(self):
        values = list(reversed(range(100)))
        config = {
            'random': {(): [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]},
            'randint': {'default': lambda a,b: values.pop() % b}
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


class TestMultiArbitrary(unittest.TestCase):
    def setUp(self):
        values = list(reversed(range(100)))
        config = {
            'random': {(): [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]},
            'randint': {'default': lambda a,b: values.pop() % b}
        }
        self.rand = FakeRandom.from_dict(config)

    def test_can_combine_multiple_arbitraries(self):
        arbitrary = MultiArbitrary(self.rand, [IntArbitrary(random_funcs=self.rand), IntArbitrary(random_funcs=self.rand)])
        value = arbitrary()
        self.assertIsInstance(value, tuple)
        self.assertEqual(len(value), 2)
        self.assertIsInstance(value[0], int)
        self.assertIsInstance(value[1], int)
        self.assertNotEqual(value[0], value[1])
