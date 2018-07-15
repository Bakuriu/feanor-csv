import unittest

from feanor.schema import Schema, MissingVersionError, InvalidVersionNumberError


class TestSchema(unittest.TestCase):
    def test_can_obtain_the_header_from_a_schema(self):
        schema = Schema()
        schema.add_column('A', type='int')
        schema.add_column('B', type='int')
        schema.add_column('C', type='int')
        self.assertEqual(schema.header(), ('A', 'B', 'C'))

    def test_can_obtain_a_column_type(self):
        schema = Schema()
        schema.add_column('A', type='int')
        self.assertEqual(schema.columns[0].name, 'A')
        self.assertEqual(schema.columns[0].type, 'int')

    def test_can_specify_header_visibility(self):
        schema = Schema(show_header=False)
        self.assertFalse(schema.show_header)

    def test_can_add_column_configuration(self):
        schema = Schema()
        schema.add_column('A', type='int', config={'a': 10})
        self.assertEqual(schema.columns[0].name, 'A')
        self.assertEqual(schema.columns[0].type, 'int')
        self.assertEqual(schema.columns[0].config, {'a': 10})



@unittest.skip
class TestSchemaParsing(unittest.TestCase):

    def test_can_parse_header_from_json_schema(self):
        schema = Schema.parse('{"version": "1.0", "header": ["A", "B", "C"]}')
        self.assertEqual(schema.header(), ('A', 'B', 'C'))

    def test_json_schema_must_have_version(self):
        with self.assertRaises(MissingVersionError):
            Schema.parse('{"header": ["A", "B", "C"]}')

    def test_json_schema_must_have_valid_version_number(self):
        for invalid_number in ('1', 'string', '1.0.2', ''):
            with self.assertRaises(InvalidVersionNumberError):
                Schema.parse('{"version": "%s", "header": ["A", "B", "C"]}' % invalid_number)