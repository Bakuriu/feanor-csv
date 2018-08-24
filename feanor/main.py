import io
import sys
import csv
import argparse
from itertools import starmap

from .dsl.compiler import Compiler, BuiltInCompatibility, DefaultCompatibility
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
    if args.schema_definition_type in ('cmdline', 'options', 'opts'):
        schema = make_schema_cmdline(args.columns, args.expressions_defined, args.show_header, args.compatibility)
    elif args.schema_definition_type == 'expr':
        schema = make_schema_expr(args.schema, _parse_columns(args.columns_names), args.show_header, args.compatibility)
    else:
        raise ValueError('Invalid subcommand {!r}'.format(args.schema_definition_type))

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
    parser.add_argument('--no-header', action='store_false', help='Do not add header to the output.', dest='show_header')
    parser.add_argument('--compatibility', default='builtin', help='The compatibility to use.')
    size_options = parser.add_mutually_exclusive_group(required=True)
    size_options.add_argument('-n', '--num-rows', type=int, help='The number of rows of the produced CSV', metavar='N')
    size_options.add_argument('-b', '--num-bytes', type=int, help='The approximate number of bytes of the produced CSV', metavar='N')
    size_options.add_argument('--stream-mode')

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('output_file', nargs='?', help='The output file name.', metavar='OUTPUT-FILE',
                        default=sys.stdout, type=argparse.FileType('w'))

    schema_subparsers = parser.add_subparsers(title='Schema definition', help='Commands to define a CSV schema.',
                                              dest='schema_definition_type')
    simple_schema_cmdline = schema_subparsers.add_parser('cmdline', aliases=['opts', 'options'], parents=[common_parser])

    simple_schema_cmdline.add_argument('-c', '--column', nargs=2, help='Add a column with the given name.', dest='columns',
                        action='append', metavar=('NAME', 'EXPR'), required=True)
    simple_schema_cmdline.add_argument('-d', '--define', nargs=2, help='Define a Feanor expression with the given name and type.',
                        dest='expressions_defined', action='append', metavar=('NAME', 'EXPR'), default=[])

    expr_schema_parser = schema_subparsers.add_parser('expr', parents=[common_parser])
    expr_schema_parser.add_argument('schema', help='The expression defining the schema', metavar='SCHEMA_EXPR')
    expr_schema_parser.add_argument('-c', '--columns', dest='columns_names', help='A CSV comma-separated header line.', metavar='NAMES')

    return parser


def make_schema_cmdline(columns, expressions_defined, show_header, compatibility):
    columns_names, expression = get_definitions_and_column_names_for_cmdline(columns, expressions_defined)
    return make_schema_from_expression(expression, columns_names, show_header, compatibility)

def make_schema_expr(expression, columns_names, show_header, compatibility):
    return make_schema_from_expression(expression, columns_names, show_header, compatibility)

def make_schema_from_expression(expression, columns_names, show_header, compatibility):
    parser = dsl_get_parser()
    if compatibility == 'builtin':
        compatibility = BuiltInCompatibility()
    elif compatibility == 'none':
        compatibility = DefaultCompatibility()
    else:
        raise ValueError('Invalid compatibility: {!r}'.format(compatibility))
    return Compiler(show_header=show_header, compatibility=compatibility).compile(parser.parse(expression), column_names=columns_names)


def get_definitions_and_column_names_for_cmdline(columns, expressions_defined):
    expressions_defined = ' '.join(starmap('{} := ({})'.format, expressions_defined))
    columns_expressions = ' '.join(starmap('{} := ({})'.format, columns))
    definitions = expressions_defined + ' ' + columns_expressions
    columns_names = [name for name, _ in columns]
    return columns_names, make_schema_let_expression(definitions, columns_names)


def make_schema_let_expression(definitions, col_names):
    return 'let {} in ({})'.format(definitions, '.'.join('@' + name for name in col_names))


def _parse_columns(columns):
    in_file = io.StringIO(columns)
    reader = csv.reader(in_file, delimiter=',')
    return next(reader)


if __name__ == '__main__':
    main()