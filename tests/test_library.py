import random
from unittest import TestCase

from feanor.dsl.types import SimpleType
from feanor.library import EmptyLibrary


class TestEmptyLibrary(TestCase):
    def test_compatibility(self):
        compat = EmptyLibrary().compatibility()
        self.assertEqual(SimpleType('a'), compat.get_upperbound(SimpleType('a'), SimpleType('b')))

    def test_env(self):
        self.assertEqual({}, EmptyLibrary().env())

    def test_func_env(self):
        self.assertEqual({}, EmptyLibrary().func_env())

    def test_get_producer_factory(self):
        factory = EmptyLibrary().get_producer_factory('any_name')
        self.assertEqual(None, factory(random))
