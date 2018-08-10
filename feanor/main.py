import argparse
import sys
from itertools import starmap

from .dsl.compiler import Compiler
from .dsl import get_parser as dsl_get_parser
from .engine import generate_data


def main():
    schema, output_file, size_dict = parse_arguments()
    generate_data(schema, output_file, **size_dict)


def parse_arguments(args=None):
    parser = get_parser()

    args = parser.parse_args(args=args)
    try:
        schema, size_dict = get_schema_and_size_params(args)
    except (ValueError,TypeError) as e:
        parser.print_usage(sys.stderr)
        sys.stderr.write('{}: error: {}\n'.format(parser.prog, str(e)))
        sys.exit(2)
    else:
        return schema, args.output_file, size_dict


def get_schema_and_size_params(args):
    schema = make_schema(args.columns, args.expressions_defined, args.show_header)
    size_dict = {}
    if args.stream_mode is not None:
        size_dict['stream_mode'] = True
    if args.num_rows is not None:
        size_dict['number_of_rows'] = args.num_rows
    if args.num_bytes is not None:
        size_dict['byte_count'] = args.num_bytes
    return schema, size_dict


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--column', nargs=2, help='Add a column with the given name.', dest='columns',
                        action='append', metavar=('NAME', 'EXPR'), required=True)
    parser.add_argument('-d', '--define', nargs=2, help='Define a Feanor expression with the given name and type.',
                        dest='expressions_defined', action='append', metavar=('NAME', 'EXPR'), default=[])
    parser.add_argument('--no-header', action='store_false', help='Do not add header to the output.',
                        dest='show_header')
    size_options = parser.add_mutually_exclusive_group(required=True)
    size_options.add_argument('-n', '--num-rows', type=int, help='The number of rows of the produced CSV', metavar='N')
    size_options.add_argument('-b', '--num-bytes', type=int, help='The approximate number of bytes of the produced CSV',
                              metavar='N')
    size_options.add_argument('--stream-mode')
    parser.add_argument('output_file', nargs='?', help='The output file name.', metavar='OUTPUT-FILE',
                        default=sys.stdout, type=argparse.FileType('w'))
    return parser


def make_schema(columns, expressions_defined, show_header):
    parser = dsl_get_parser()
    expressions_defined = ' '.join(starmap('{} := ({})'.format, expressions_defined))
    columns_expressions = ' '.join(starmap('{} := ({})'.format, columns))
    columns_names = [name for name, _ in columns]
    complete_expression = 'let {} {} in ({})'.format(expressions_defined, columns_expressions, '.'.join('@'+name for name in columns_names))

    return Compiler(show_header=show_header).compile(parser.parse(complete_expression), column_names=columns_names)



if __name__ == '__main__':
    main()