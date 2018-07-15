import random
from collections import Counter

from .types.builtin import MultiArbitrary, IntArbitrary, RepeaterArbitrary

DEFAULT_ENVIRONMENT = {
    'int': IntArbitrary,
}


class Engine:
    def __init__(self, schema, *, environment=DEFAULT_ENVIRONMENT, random_funcs=random):
        self._random_funcs = random_funcs
        self._schema = schema
        self._env = dict(environment)
        self._generator = self._schema_to_generator(schema)

    def _schema_to_generator(self, schema):
        arbitraries = {arbitrary.name: self._env[arbitrary.type](self._random_funcs, config=arbitrary.config) for arbitrary in schema.arbitraries}
        arbitraries_repeats = Counter(column.arbitrary for column in schema.columns)
        for arbitrary, count in arbitraries_repeats.items():
            if count > 1:
                arbitraries[arbitrary] = RepeaterArbitrary(self._random_funcs, arbitraries[arbitrary], {'num_repeats': count})

        return MultiArbitrary(
            self._random_funcs,
            (arbitraries[column.arbitrary] for column in schema.columns)
        )

    @property
    def number_of_columns(self):
        return self._generator.number_of_columns

    @property
    def columns(self):
        return self._generator

    def generate_data(self, number_of_rows=float('+inf')):
        while number_of_rows > 0:
            yield self._generator()
            number_of_rows -= 1


def generate_data(schema, output_file, *, number_of_rows=None, byte_count=None, stream_mode=False):
    if number_of_rows is None is byte_count and not stream_mode:
        raise TypeError('You must specify the size either by number of rows or byte count or use stream mode')
    elif number_of_rows is not None is not byte_count:
        raise TypeError('You cannot specify both a number of rows and a byte count.')

    if number_of_rows is not None:
        _generate_data_by_number_of_rows(schema, output_file, number_of_rows)
    elif byte_count is not None:
        _generate_data_by_byte_count(schema, output_file, byte_count)
    else:
        _generate_data_stream(schema, output_file)


def _generate_data_by_number_of_rows(schema, output_file, number_of_rows):
    generator = _make_stream_of_data(schema, number_of_rows)

    for data in generator:
        output_file.write(','.join(map(str, data)) + '\n')


def _generate_data_by_byte_count(schema, output_file, byte_count):
    generator = _make_stream_of_data(schema)
    num_bytes = 0

    def write_to_file(seq):
        nonlocal num_bytes
        line = ';'.join(map(str, seq)) + '\n'
        num_bytes += len(line)
        output_file.write(line)

    while num_bytes < byte_count:
        write_to_file(next(generator))


def _generate_data_stream(schema, output_file):
    generator = _make_stream_of_data(schema)

    def write_to_file(seq):
        output_file.write(';'.join(map(str, seq)) + '\n')

    for data in generator:
        write_to_file(data)


def _make_stream_of_data(schema, number_of_rows=float('+inf')):
    engine = Engine(schema)
    if schema.show_header:
        yield schema.header()

    yield from engine.generate_data(number_of_rows)
