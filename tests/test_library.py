import random
from unittest import TestCase

from feanor.dsl.types import SimpleType
from feanor.library import MockLibrary


class TestMockLibrary(TestCase):
    def test_compatibility(self):
        compat = MockLibrary().compatibility()
        self.assertEqual(SimpleType('a'), compat.get_upperbound(SimpleType('a'), SimpleType('b')))

    def test_env(self):
        self.assertEqual({}, MockLibrary().env())

    def test_func_env(self):
        self.assertEqual({}, MockLibrary().func_env())

    def test_get_producer_factory(self):
        factory = MockLibrary().get_producer_factory('any_name')
        self.assertEqual(None, factory(random))

    def test_can_register_a_function(self):
        library = MockLibrary()
        library.register_function('ciao', float, [SimpleType('int')], SimpleType('float'))
        expected_func_env = {'ciao': float, '::types::': {'ciao': ([SimpleType('int')], SimpleType('float'))}}
        self.assertEqual(expected_func_env, library.func_env())

    def test_can_register_a_variable(self):
        library = MockLibrary()
        library.register_variable('ciao', 1.0, SimpleType('float'))
        expected_env = {'ciao': 1.0, '::types::': {'ciao': SimpleType('float')}}
        self.assertEqual(expected_env, library.env())
