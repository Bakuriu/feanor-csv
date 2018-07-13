import unittest

from fake_random import FakeRandom


class TestFakeRandom(unittest.TestCase):
    def test_can_return_one_value(self):
        rand = FakeRandom()
        rand.register('random', (), [0.1])
        self.assertEqual(0.1, rand.random())

    def test_can_return_one_value_for_multiple_methods(self):
        rand = FakeRandom()
        rand.register('a', (), [0])
        rand.register('b', (), [1])
        rand.register('c', (), [2])
        got = [rand.a(), rand.b(), rand.c()]
        self.assertEqual([0, 1, 2], got)

    def test_can_return_multiple_different_values(self):
        rand = FakeRandom()
        rand.register('random', (), [0.1, 0.2, 0.3])
        got = [rand.random() for _ in range(3)]
        self.assertEqual([0.1, 0.2, 0.3], got)

    def test_can_return_multiple_different_values_for_multiple_methods(self):
        rand = FakeRandom()
        rand.register('a', (), [0, 1, 2])
        rand.register('b', (), [3, 4, 5])
        rand.register('c', (), [6, 7])
        got = [rand.a(), rand.a(), rand.a(), rand.b(), rand.b(), rand.b(), rand.c(), rand.c()]
        self.assertEqual(list(range(8)), got)

    def test_can_return_different_values_for_different_args(self):
        rand = FakeRandom()
        rand.register('random', (), [0.1])
        rand.register('random', (0, 1), [0.2, 0.3])
        got = [rand.random()] + [rand.random(0, 1), rand.random(0, 1)]
        self.assertEqual([0.1, 0.2, 0.3], got)

    def test_can_provide_default_value(self):
        rand = FakeRandom()
        rand.register('random', (), [0.1])
        rand.register_default('random', 1)
        got = [rand.random(), rand.random(0, 1)]
        self.assertEqual([0.1, 1], got)

    def test_can_provide_default_callable(self):
        rand = FakeRandom()
        rand.register_default('randint', lambda a, b: (a+b)/2)
        got = [rand.randint(1, 2), rand.randint(0, 1)]
        self.assertEqual([1.5, 0.5], got)

    def test_can_provide_missing_value(self):
        rand = FakeRandom()
        rand.register('random', (), [0.1])
        rand.register_missing('random', 1)
        got = [rand.random() for _ in range(3)]
        self.assertEqual([0.1, 1, 1], got)

    def test_can_provide_missing_callable(self):
        rand = FakeRandom()
        rand.register('randint', (1, 2), [])
        rand.register('randint', (0, 1), [])
        rand.register_missing('randint', lambda a, b, c=[0]: c.append(len(c)) or (a+b+c[-1])/2)
        got = [rand.randint(1, 2), rand.randint(0, 1), rand.randint(0, 1)]
        self.assertEqual([2, 1.5, 2], got)

    def test_can_create_fake_random_from_dict_config(self):
        config = {
            'random': {
                (): [0.1, 0.3],
                (0, 1): [0.2],
            },
            'a': {
                (): [-1],
                'default': 1
            },
            'b': {
                (): [1],
                'missing': 2,
                'default': 3,
            }
        }
        rand = FakeRandom.from_dict(config)
        got_random = [rand.random(), rand.random(0, 1), rand.random()]
        self.assertEqual([0.1, 0.2, 0.3], got_random)

        got_a = [rand.a(), rand.a(1,2,3), rand.a(4,5,6)]
        with self.assertRaises(RuntimeError):
            rand.a()
        self.assertEqual([-1, 1, 1], got_a)

        got_b = [rand.b(), rand.b(), rand.b(), rand.b(0,1)]
        self.assertEqual([1, 2, 2, 3], got_b)
