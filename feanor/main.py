import io
import ast
import csv
import sys
import argparse
from itertools import starmap

from . import __version__
from .util import load_python_module, cls_name
from .dsl import get_parser as dsl_get_parser
from .dsl.compiler import Compiler
from .engine import generate_data


def main():  # pragma: no cover
    schema, library, output_file, size_dict = parse_arguments()
    generate_data(schema, library, output_file, **size_dict)


def parse_arguments(args=None):
    parser = get_parser()

    args = parser.parse_args(args=args)
    try:
        schema, library, size_dict = get_schema_size_and_library_params(args)
    except (ValueError, TypeError) as e:  # pragma: no cover
        parser.print_usage(sys.stderr)
        sys.stderr.write('{}: error: {}\n'.format(parser.prog, str(e)))
        sys.exit(2)
    else:
        return schema, library, args.output_file, size_dict


def get_schema_size_and_library_params(args):
    if args.random_seed is not None:
        args.random_module.seed(args.random_seed)
    library = get_library(args.library, args.global_configuration, args.random_module)
    if args.schema_definition_type in ('cmdline', 'options', 'opts'):
        schema = make_schema_cmdline(args.columns, args.expressions_defined, args.show_header, library)
    elif args.schema_definition_type == 'expr':
        schema = make_schema_expr(args.schema, _parse_columns(args.columns_names), args.show_header, library)
    else:
        raise ValueError('Invalid subcommand {!r}'.format(args.schema_definition_type))

    size_dict = {}
    if args.stream_mode is not None:
        size_dict['stream_mode'] = True
    if args.num_rows is not None:
        size_dict['number_of_rows'] = args.num_rows
    if args.num_bytes is not None:
        size_dict['byte_count'] = args.num_bytes
    return schema, library, size_dict


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-header', action='store_false', help='Do not add header to the output.',
                        dest='show_header')
    parser.add_argument('-L', '--library', default='feanor.builtin', help='The library to use.')
    parser.add_argument('-C', '--global-configuration', default={}, type=_parse_global_configuration,
                        help='The global configuration for arbitraries.')
    parser.add_argument('-r', '--random-module', default='random', type=load_python_module,
                        help='The random module to be used to generate random data.')
    parser.add_argument('-s', '--random-seed', type=ast.literal_eval, help='The random seed to use for this run.')
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    size_options = parser.add_mutually_exclusive_group(required=True)
    size_options.add_argument('-n', '--num-rows', type=int, help='The number of rows of the produced CSV', metavar='N')
    size_options.add_argument('-b', '--num-bytes', type=int, help='The approximate number of bytes of the produced CSV',
                              metavar='N')
    size_options.add_argument('--stream-mode')

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('output_file', nargs='?', help='The output file name.', metavar='OUTPUT-FILE',
                               default=sys.stdout, type=argparse.FileType('w'))

    schema_subparsers = parser.add_subparsers(title='Schema definition', help='Commands to define a CSV schema.',
                                              dest='schema_definition_type', metavar='{expr,cmdline}')
    simple_schema_cmdline = schema_subparsers.add_parser('cmdline', aliases=['opts', 'options'],
                                                         parents=[common_parser])

    simple_schema_cmdline.add_argument('-c', '--column', nargs=2, help='Add a column with the given name.',
                                       dest='columns',
                                       action='append', metavar=('NAME', 'EXPR'), required=True)
    simple_schema_cmdline.add_argument('-d', '--define', nargs=2,
                                       help='Define a Feanor expression with the given name and type.',
                                       dest='expressions_defined', action='append', metavar=('NAME', 'EXPR'),
                                       default=[])

    expr_schema_parser = schema_subparsers.add_parser('expr', parents=[common_parser])
    expr_schema_parser.add_argument('schema', help='The expression defining the schema', metavar='SCHEMA_EXPR')
    expr_schema_parser.add_argument('-c', '--columns', dest='columns_names', help='A CSV comma-separated header line.',
                                    metavar='NAMES')

    return parser


def make_schema_cmdline(columns, expressions_defined, show_header, library):
    columns_names, expression = get_definitions_and_column_names_for_cmdline(columns, expressions_defined)
    return make_schema_from_expression(expression, columns_names, show_header, library)


def make_schema_expr(expression, columns_names, show_header, library):
    return make_schema_from_expression(expression, columns_names, show_header, library)


def make_schema_from_expression(expression, columns_names, show_header, library):
    parser = dsl_get_parser()
    return Compiler(library, show_header=show_header).compile(parser.parse(expression), column_names=columns_names)


def get_definitions_and_column_names_for_cmdline(columns, expressions_defined):
    expressions_defined = ' '.join(starmap('{} := ({})'.format, expressions_defined))
    columns_expressions = ' '.join(starmap('{} := ({})'.format, columns))
    definitions = expressions_defined + ' ' + columns_expressions
    columns_names = [name for name, _ in columns]
    return columns_names, make_schema_let_expression(definitions, columns_names)


def make_schema_let_expression(definitions, col_names):
    return 'let {} in ({})'.format(definitions, '.'.join('@' + name for name in col_names))


def get_library(library_name, global_configuration, random_funcs):
    try:
        library_module = load_python_module(library_name)
    except SystemExit as e:
        print(f'Exit requested while importing library {repr(library_name)}. Exit code {e.code}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Exception while importing library {repr(library_name)}:\n{cls_name(e)}: {e}', file=sys.stderr)
        sys.exit(1)
    except BaseException as e:
        print(f'Fatal error while importing library {repr(library_name)}:\n{cls_name(e)}: {e}', file=sys.stderr)
        sys.exit(1)
    else:
        try:
            return library_module.create_library(global_configuration, random_funcs)
        except Exception as e:
            print(f'Exception while initializing library {repr(library_name)}:\n{cls_name(e)}: {e}', file=sys.stderr)
            sys.exit(1)
        except BaseException as e:
            print(f'Fatal error while initializing library {repr(library_name)}:\n{cls_name(e)}: {e}', file=sys.stderr)
            sys.exit(1)


def _parse_columns(columns):
    in_file = io.StringIO(columns)
    reader = csv.reader(in_file, delimiter=',')
    return next(reader)


def _parse_global_configuration(configuration):
    value = ast.literal_eval(configuration)
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError
    return value


if __name__ == '__main__':
    main()
