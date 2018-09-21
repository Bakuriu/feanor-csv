class Engine:
    def __init__(self, schema, library):
        self._schema = schema
        self._library = library
        self._generator = self._schema_to_generator(schema)

    def _schema_to_generator(self, schema):
        arbitraries = {arbitrary.name: self._library.make_arbitrary(arbitrary.type, arbitrary.config) for arbitrary in
                       schema.arbitraries}
        return DataGenerator(schema.columns, arbitraries, schema.transformers)

    @property
    def number_of_columns(self):
        return len(self._generator._columns)

    def generate_data(self, number_of_rows=float('+inf')):
        while number_of_rows > 0:
            yield self._generator()
            number_of_rows -= 1


class DataGenerator:
    def __init__(self, columns, arbitraries, transformers):
        self._transformers = tuple(transformers)
        self._arbitraries = arbitraries
        self._columns = tuple(columns)

    def __call__(self):
        env = {name: arbitrary() for name, arbitrary in self._arbitraries.items()}
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
