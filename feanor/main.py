import argparse
import sys

from .util import to_string_list
from .schema import Schema, FunctionalTransformer
from .types.arbitrary import parse_type, ParsingError
from .engine import generate_data


def main():
    schema, output_file, size_dict = parse_arguments()
    generate_data(schema, output_file, **size_dict)


def parse_arguments(args=None):
    parser = get_parser()

    args = parser.parse_args(args=args)
    try:
        schema, size_dict = get_schema_and_size_params(args)
    except ValueError as e:
        parser.print_usage(sys.stderr)
        sys.stderr.write('{}: error: {}\n'.format(parser.prog, str(e)))
        sys.exit(2)
    else:
        return schema, args.output_file, size_dict

def get_schema_and_size_params(args):
    transformers = ((name, values) for name, *values in args.transformers)
    schema = make_schema(args.columns, args.arbitraries, transformers, args.show_header)
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
    parser.add_argument('-c', '--column', help='Add a column with the given name.', dest='columns', action='append',
                        metavar='NAME', required=True)
    parser.add_argument('-a', '--arbitrary', nargs=2, help='Add an arbitrary with the given name and type.',
                        type=ArbitraryType(), dest='arbitraries', action='append', metavar=('NAME', 'TYPE'),
                        default=[])
    parser.add_argument('-t', '--transformer', nargs=4,
                        help='Add a transformer with the given name, inputs, outputs and expression.',
                        type=TransformerType(), dest='transformers', action='append',
                        metavar=('NAME', 'INPUTS', 'OUTPUTS', 'EXPR'),
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
    return parser


def make_schema(columns, arbitraries, transformers, show_header):
    schema = Schema(show_header=show_header)
    for column in columns:
        schema.add_column(column)
    for name, (arbitrary_type, config) in arbitraries:
        schema.add_arbitrary(name, type=arbitrary_type, config=config)
    for name, (inputs, outputs, transformer) in transformers:
        schema.add_transformer(name, inputs=inputs, outputs=outputs, transformer=transformer)

    defined_names = {arbitrary.name for arbitrary in schema.arbitraries}
    for trans in schema.transformers:
        defined_names |= set(trans.outputs)
    undefined_columns = set(schema.columns) - defined_names
    if undefined_columns:
        raise ValueError('Invalid schema. Columns {} have no associated generator.'.format(to_string_list(undefined_columns)))
    return schema


class ArbitraryType:
    """Class that works as ArgumentParser's `type` parameter for describing the type of an arbitrary."""

    def __init__(self):
        self._num_calls = 0

    def __call__(self, string):
        self._num_calls += 1
        if self._num_calls % 2 == 1:
            # this is the name of the arbitrary. Keep as is.
            return string
        # This is the "type" of the arbitrary.
        return self._parse_type(string)

    def _parse_type(self, string):
        try:
            return parse_type(string)
        except ParsingError as e:
            raise argparse.ArgumentTypeError(str(e))


class TransformerType:
    """Class that works as ArgumentParser's `type` parameter for describing the type of an arbitrary."""

    def __init__(self):
        self._num_calls = 0
        self._inputs = None
        self._num_outputs = None

    def __call__(self, string):
        self._num_calls += 1
        modulo = self._num_calls % 4
        if modulo == 1:
            # name of the transformer
            return string
        if modulo in (2, 3):
            # this is either the input or the output list.
            seq_names = string.split(',')
            if modulo == 2:
                self._inputs = seq_names
            else:
                self._num_outputs = len(seq_names)
            return seq_names
        # This is the "expression" defining the transformer.
        return self._parse_expr(string)

    def _parse_expr(self, expr):
        import random
        try:
            # TODO: Python kernel thing.
            real_expr = f'lambda {",".join(self._inputs)}: ({expr})'
            function = eval(real_expr, {'random': random})
            return FunctionalTransformer(function, num_outputs=self._num_outputs)
        except SyntaxError as e:
            raise argparse.ArgumentTypeError(str(e))
