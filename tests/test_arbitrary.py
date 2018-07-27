import unittest

from feanor.arbitrary import parse_type


class TestParseType(unittest.TestCase):
    def test_can_parse_a_type_name(self):
        self.assertEqual(('int', {}), parse_type('int'))

    def test_can_parse_a_type_with_empty_config(self):
        self.assertEqual(('int', {}), parse_type('int{}'))

    def test_can_parse_a_type_with_a_single_config(self):
        self.assertEqual(('int', {'lowerbound': 10}), parse_type('int{"lowerbound": 10}'))

    def test_can_parse_a_type_with_a_complex_config(self):
        self.assertEqual(('int', {'a': {'b': [(1,2), (3,4)]}}), parse_type('int{"a": {"b": [(1,2), (3,4)]}}'))

