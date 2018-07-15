import json
import re
from types import SimpleNamespace


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
        self._arbitraries = {}

    @property
    def columns(self):
        return [SimpleNamespace(**column) for column in self._columns]

    @property
    def arbitraries(self):
        return [SimpleNamespace(name=name, **values) for name, values in self._arbitraries.items()]

    @property
    def show_header(self):
        return self._show_header

    def add_column(self, name, *, type, config=None):
        arbitrary_name = 'column#%d' % len(self._columns)
        self.add_arbitrary(arbitrary_name, type=type, config=config)
        self._columns.append({
            'name': name,
            'arbitrary': arbitrary_name,
        })

    def add_arbitrary(self, name, *, type, config=None):
        """Register an arbitrary to the schema."""
        self._arbitraries[name] = {'type': type, 'config': config or {}}

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
