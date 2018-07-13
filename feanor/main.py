import sys
import argparse

from feanor.schema import Schema
from .engine import generate_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c' ,'--column', nargs=2, help='Add a column with the given type.',
                        dest='columns', action='append', metavar=('NAME', 'TYPE'))
    parser.add_argument('output-file', nargs='?', type=argparse.FileType('w'), help='The output file name.', default=sys.stdout)
    size_options = parser.add_mutually_exclusive_group(required=True)
    size_options.add_argument('-n', '--num-rows', type=int, help='The number of rows of the produced CSV', metavar='N')
    size_options.add_argument('-b', '--num-bytes', type=int, help='The approximate number of bytes of the produced CSV',
                              metavar='N')
    size_options.add_argument('--stream-mode')

    args = parser.parse_args()
    schema = make_schema(args.columns)

    size_dict = {}
    if args.stream_mode is not None:
        size_dict['stream_mode'] = True
    if args.num_rows is not None:
        size_dict['number_of_rows'] = args.num_rows
    if args.num_bytes is not None:
        size_dict['byte_count'] = args.num_bytes

    generate_data(schema, args.output_file, **size_dict)


def make_schema(columns):
    schema = Schema()
    for name, col_type in columns:
        schema.add_column(name, type=col_type)
    return schema