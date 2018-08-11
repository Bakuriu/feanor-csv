import unittest
from types import SimpleNamespace

from feanor.arbitrary import Arbitrary


class TestArbitraryDefaultConfiguration(unittest.TestCase):
    def test_uses_default_config_when_passing_none(self):
        class HasDefaultConfig(Arbitrary):
            def __call__(self):
                return None

            @classmethod
            def default_config(cls):
                return {'key': 'value'}

        arbitrary = HasDefaultConfig(None, 'test_arbitrary', None)
        self.assertEqual(SimpleNamespace(key='value'), arbitrary.config)

    def test_uses_default_config_when_passing_empty_dict(self):
        class HasDefaultConfig(Arbitrary):
            def __call__(self):
                return None

            @classmethod
            def default_config(cls):
                return {'key': 'value'}

        arbitrary = HasDefaultConfig(None, 'test_arbitrary', {})
        self.assertEqual(SimpleNamespace(key='value'), arbitrary.config)

    def test_can_override_default_config_key(self):
        class HasDefaultConfig(Arbitrary):
            def __call__(self):
                return None

            @classmethod
            def default_config(cls):
                return {'key': 'value', 'key2': 'other_value'}

        arbitrary = HasDefaultConfig(None, 'test_arbitrary', {'key': 'new_value'})
        self.assertEqual(SimpleNamespace(key='new_value', key2='other_value'), arbitrary.config)

    def test_can_add_new_keys_to_configuration(self):
        class HasDefaultConfig(Arbitrary):
            def __call__(self):
                return None

            @classmethod
            def default_config(cls):
                return {'key': 'value'}

        arbitrary = HasDefaultConfig(None, 'test_arbitrary', {'key2': 'new_value'})
        self.assertEqual(SimpleNamespace(key='value', key2='new_value'), arbitrary.config)


class TestRequiredConfigNames(unittest.TestCase):

    def test_can_set_required_config_values(self):
        class HasDefaultConfig(Arbitrary):
            def __call__(self):
                return None

            @classmethod
            def required_config_keys(cls):
                return {'key', 'a'}

            @classmethod
            def default_config(cls):
                return {'key': 'value'}

        arbitrary = HasDefaultConfig(None, 'test_arbitrary', {'key': 'new_value', 'a': 'A'})
        self.assertEqual(SimpleNamespace(key='new_value', a='A'), arbitrary.config)

    def test_raises_error_if_not_all_keys_are_provided(self):
        class HasDefaultConfig(Arbitrary):
            def __call__(self):
                return None

            @classmethod
            def required_config_keys(cls):
                return {'key', 'a'}

            @classmethod
            def default_config(cls):
                return {}

        with self.assertRaises(ValueError):
            HasDefaultConfig(None, 'test_arbitrary', {'key': 'new_value'})

    def test_can_provide_only_keys_missing_from_default_config(self):
        class HasDefaultConfig(Arbitrary):
            def __call__(self):
                return None

            @classmethod
            def required_config_keys(cls):
                return {'key', 'a'}

            @classmethod
            def default_config(cls):
                return {'key': 'value'}

        arbitrary = HasDefaultConfig(None, 'test_arbitrary', {'a': 'A'})
        self.assertEqual(SimpleNamespace(key='value', a='A'), arbitrary.config)

