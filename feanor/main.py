import argparse
import sys

from feanor.schema import Schema
from feanor.types.arbitrary import parse_type, ParsingError
from .engine import generate_data


def main():
    parser = argparse.ArgumentParser()
    column_typer = Column()
    parser.add_argument('-c', '--column', nargs=2, type=column_typer.type,
                        help='Add a column with the given type or using the given arbitrary.\n'
                             'An arbitrary name must be preceded by the @ sign.',
                        dest='columns', action='append', metavar=('NAME', 'TYPE_OR_ARBITRARY'),
                        required=True)
    parser.add_argument('-a', '--arbitrary', nargs=2, help='Add an arbitrary with the given type.',
                        type=column_typer.arbitrary, dest='arbitraries', action='append', metavar=('NAME', 'TYPE'),
                        default=[])
    parser.add_argument('--no-header', action='store_false', help='Do not add header to the output.',
                        dest='show_header')
    size_options = parser.add_mutually_exclusive_group(required=True)
    size_options.add_argument('-n', '--num-rows', type=int, help='The number of rows of the produced CSV', metavar='N')
    size_options.add_argument('-b', '--num-bytes', type=int, help='The approximate number of bytes of the produced CSV',
                              metavar='N')
    size_options.add_argument('--stream-mode')
    parser.add_argument('output_file', nargs='?', help='The output file name.', metavar='OUTPUT-FILE',
                        default=sys.stdout, type=argparse.FileType('w'))

    args = parser.parse_args()
    schema = make_schema(args.arbitraries, args.columns, args.show_header)

    size_dict = {}
    if args.stream_mode is not None:
        size_dict['stream_mode'] = True
    if args.num_rows is not None:
        size_dict['number_of_rows'] = args.num_rows
    if args.num_bytes is not None:
        size_dict['byte_count'] = args.num_bytes

    generate_data(schema, args.output_file, **size_dict)


def make_schema(arbitraries, columns, show_header):
    schema = Schema(show_header=show_header)
    for name, (arbitrary_type, config) in arbitraries:
        schema.add_arbitrary(name, type=arbitrary_type, config=config)
    for name, (col_type, config, arbitrary) in columns:
        schema.define_column(name, arbitrary=arbitrary, type=col_type, config=config or None)
    return schema


class Column:
    def __init__(self):
        self._num_type_calls = 0
        self._num_arbitrary_calls = 0

    def type(self, string):
        """Callable that works as ArgumentParser's `type` parameter for describing the type or arbitrary of a column."""
        self._num_type_calls += 1
        if self._num_type_calls % 2 == 1:
            # this is the name of the column. Keep as is.
            return string
        # This is the "type or arbitrary name" of the column.
        if string[:1] != '@':
            # it's a type:
            return self._parse_type(string) + (None,)
        else:
            # it's a reference to an arbitrary with that name. Remove initial @
            return (None, None, string[1:])

    def arbitrary(self, string):
        """Callable that works as ArgumentParser's `type` parameter for describing the type of an arbitrary."""
        self._num_arbitrary_calls += 1
        if self._num_arbitrary_calls % 2 == 1:
            # this is the name of the arbitrary. Keep as is.
            return string
        # This is the "type" of the arbitrary.
        return self._parse_type(string)

    def _parse_type(self, string):
        try:
            return parse_type(string)
        except ParsingError as e:
            raise argparse.ArgumentTypeError(str(e))
