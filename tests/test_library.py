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

    def test_can_register_a_factory(self):
        library = MockLibrary()
        factory = lambda random_funcs, config: 10
        library.register_factory('ciao', factory)
        self.assertEqual(factory, library.get_producer_factory('ciao'))

    def test_can_register_a_definition(self):
        library = MockLibrary()
        factory = lambda random_funcs, config: 10
        library.register_factory('int', factory)
        library.register_definition('ciao', {'producer': 'int', 'config': {}})
        self.assertEqual(10, library.make_producer('ciao', {}))

    def test_raises_error_if_trying_to_register_a_factory_multiple_times(self):
        library = MockLibrary()
        factory = lambda random_funcs, config: 10
        library.register_factory('ciao', factory)
        with self.assertRaises(ValueError):
            library.register_factory('ciao', factory)

    def test_raises_error_if_trying_to_register_a_factory__that_is_already_registered_as_a_definition(self):
        library = MockLibrary()
        library.definitions = {'ciao': {'producer': 'int'}}
        factory = lambda random_funcs, config: 10
        with self.assertRaises(ValueError):
            library.register_factory('ciao', factory)

    def test_raises_error_if_trying_to_unknown_producer(self):
        library = MockLibrary()
        with self.assertRaises(LookupError):
            library.make_producer('ciao', {})

    def test_can_lookup_definitions(self):
        library = MockLibrary()
        factory = lambda random_funcs, config: 1
        library.register_factory('int', factory)
        library.register_definition('perc', {'producer': 'int'})
        self.assertEqual(1, library.make_producer('perc', {}))

    def test_can_register_multiple_definitions(self):
        library = MockLibrary()
        factory_int = lambda random_funcs, config: 1
        factory_float = lambda random_funcs, config: 2.0
        library.register_factory('int', factory_int)
        library.register_factory('float', factory_float)
        library.register_definitions({'perc': {'producer': 'int'}, 'other': {'producer': 'float'}})
        self.assertEqual(1, library.make_producer('perc', {}))
        self.assertEqual(2.0, library.make_producer('other', {}))

    def test_raises_error_when_creating_library_if_name_has_multiple_definitions(self):
        with self.assertRaises(ValueError):
            MockLibrary(factories={'a': (lambda x: 1)}, definitions={'a': None})

