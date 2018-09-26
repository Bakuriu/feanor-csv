# Copyright 2018 Giacomo Alzetta <giacomo.alzetta+feanor@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

class Engine:
    def __init__(self, schema, library):
        self._schema = schema
        self._library = library
        self._generator = self._schema_to_generator(schema)

    def _schema_to_generator(self, schema):
        factory = self._library.make_producer
        producers = {producer.name: factory(producer.type, producer.config) for producer in schema.producers}
        return DataGenerator(schema.columns, producers, schema.transformers)

    @property
    def number_of_columns(self):
        return len(self._generator._columns)

    def generate_data(self, number_of_rows=float('+inf')):
        while number_of_rows > 0:
            yield self._generator()
            number_of_rows -= 1


class DataGenerator:
    def __init__(self, columns, producers, transformers):
        self._transformers = tuple(transformers)
        self._producers = producers
        self._columns = tuple(columns)

    def __call__(self):
        env = {name: producer() for name, producer in self._producers.items()}
        for transformer in self._transformers:
            output_values = transformer.transformer([env[input_name] for input_name in transformer.inputs])
            for name, value in zip(transformer.outputs, output_values):
                env[name] = value

        return tuple(env[name] for name in self._columns)


def generate_data(schema, library, output_file, *, number_of_rows=None, byte_count=None, stream_mode=False):
    if number_of_rows is None is byte_count and not stream_mode:
        raise TypeError('You must specify the size either by number of rows or byte count or use stream mode')
    elif number_of_rows is not None is not byte_count:
        raise TypeError('You cannot specify both a number of rows and a byte count.')

    if number_of_rows is not None:
        _generate_data_by_number_of_rows(schema, library, output_file, number_of_rows)
    elif byte_count is not None:
        _generate_data_by_byte_count(schema, library, output_file, byte_count)
    else:
        _generate_data_stream(schema, library, output_file)


def _generate_data_by_number_of_rows(schema, library, output_file, number_of_rows):
    generator = _make_stream_of_data(schema, library, number_of_rows)

    for data in generator:
        output_file.write(','.join(map(str, data)) + '\n')


def _generate_data_by_byte_count(schema, library, output_file, byte_count):
    generator = _make_stream_of_data(schema, library)
    num_bytes = 0

    def write_to_file(seq):
        nonlocal num_bytes
        line = ','.join(map(str, seq)) + '\n'
        num_bytes += len(line)
        output_file.write(line)

    while num_bytes < byte_count:
        write_to_file(next(generator))


def _generate_data_stream(schema, library, output_file):
    generator = _make_stream_of_data(schema, library)

    def write_to_file(seq):
        output_file.write(','.join(map(str, seq)) + '\n')

    for data in generator:  # pragma: no cover
        write_to_file(data)


def _make_stream_of_data(schema, library, number_of_rows=float('+inf')):
    engine = Engine(schema, library)
    if schema.show_header:
        yield schema.columns

    yield from engine.generate_data(number_of_rows)
