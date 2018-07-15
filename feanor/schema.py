import re
import json

from types import SimpleNamespace

from .types.builtin import IntArbitrary, MultiArbitrary


class SchemaParsingError(ValueError):
    pass


class MissingVersionError(SchemaParsingError):
    pass


class InvalidVersionNumberError(SchemaParsingError):
    def __init__(self, version):
        super().__init__(repr(version))


class Schema:
    def __init__(self, *, show_header=True):
        self._show_header = show_header
        self._columns = []

    @property
    def columns(self):
        return [SimpleNamespace(**column) for column in self._columns]

    @property
    def show_header(self):
        return self._show_header

    def add_column(self, name, *, type, config=None):
        self._columns.append({
            'name': name,
            'type': type,
            'config': config or {},
        })

    def header(self):
        return tuple(column['name'] for column in self._columns)

    @classmethod
    def parse(cls, text):
        data = json.loads(text)
        if not 'version' in data:
            raise MissingVersionError()
        elif not isinstance(data['version'], str) or not re.match('^\d+\.\d+$', data['version']):
            raise InvalidVersionNumberError(data['version'])

        schema = cls()
        for name in data['header']:
            schema.add_column(name)
        return schema