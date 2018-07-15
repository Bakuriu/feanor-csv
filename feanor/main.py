import sys
import argparse

from feanor.schema import Schema
from feanor.types.arbitrary import parse_type, ParsingError
from .engine import generate_data

def main():
    parser = argparse.ArgumentParser()
    column_typer = Column()
    parser.add_argument('-c' ,'--column', nargs=2, help='Add a column with the given type.', type=column_typer.type,
                        dest='columns', action='append', metavar=('NAME', 'TYPE'))
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
    schema = make_schema(args.columns, args.show_header)

    size_dict = {}
    if args.stream_mode is not None:
        size_dict['stream_mode'] = True
    if args.num_rows is not None:
        size_dict['number_of_rows'] = args.num_rows
    if args.num_bytes is not None:
        size_dict['byte_count'] = args.num_bytes

    generate_data(schema, args.output_file, **size_dict)


def make_schema(columns, show_header):
    schema = Schema(show_header=show_header)
    for name, (col_type, config) in columns:
        schema.add_column(name, type=col_type, config=config)
    return schema


class Column:
    def __init__(self):
        self._num_calls = 0

    def type(self, string):
        """Callable that works as ArgumentParser's `type` parameter for describing the type of an arbitrary."""
        self._num_calls += 1
        if self._num_calls % 2 == 1:
            return string
        try:
            return parse_type(string)
        except ParsingError as e:
            raise argparse.ArgumentTypeError(str(e))