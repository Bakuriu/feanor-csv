import re
import json
import inspect
from abc import ABCMeta, abstractmethod
from collections import Counter
from types import SimpleNamespace

from feanor.util import to_string_list


class SchemaError(ValueError):
    pass


class SchemaParsingError(SchemaError):
    pass


class MissingVersionError(SchemaParsingError):
    pass


class InvalidVersionNumberError(SchemaParsingError):
    def __init__(self, version):
        super().__init__(repr(version))


class SchemaRef:
    def __init__(self, name, scope):
        self.name = name
        self.scope = scope

    def __eq__(self, other):
        return isinstance(other, SchemaRef) and self.name == other.name and self.scope == other.scope

    def __hash__(self):
        return hash((self.name, self.scope))

    @classmethod
    def valid_scopes(cls):
        return {'cols', 'vals'}

    @classmethod
    def parse(cls, ref):
        if '@' in ref:
            name, scope = ref.split('@')
            if scope not in cls.valid_scopes():
                raise SchemaError('Scope {!r} is not valid.'.format(scope))
            return SchemaRef(name, scope)
        return SchemaRef(ref, 'cols')


class Schema:
    def __init__(self, *, show_header=True):
        self._show_header = show_header
        self._columns = []
        self._arbitraries = {}
        self._transformers = []

    @property
    def columns(self):
        return tuple(self._columns)

    @property
    def arbitraries(self):
        """The arbitraries used in the schema.

        Note: the order of the returned list is undefined.
        """
        return [SimpleNamespace(name=name, **values) for name, values in self._arbitraries.items()]

    @property
    def transformers(self):
        """The transformers used in the schema.

        Note: the order of the returned list is undefined."""
        return [SimpleNamespace(**transformer) for transformer in self._transformers]

    @property
    def show_header(self):
        return self._show_header

    def add_column(self, name):
        """Add a column with the given name to the schema.

        :raises SchemaError: when the `name` already exists.

        """
        if name in self._columns:
            raise SchemaError('Column {!r} is already defined.'.format(name))
        self._columns.append(name)

    def define_column(self, name, *, arbitrary=None, type=None, config=None):
        if name in self._columns:
            raise SchemaError('Column {!r} is already defined.'.format(name))

        if arbitrary is not None is not type:
            raise TypeError('Cannot specify both arbitrary and type.')
        if arbitrary is not None is not config:
            raise TypeError('Cannot specify both arbitrary and config.')

        if arbitrary is not None:
            if arbitrary not in self._arbitraries:
                raise SchemaError('Arbitrary {!r} does not exist.'.format(arbitrary))
            self.add_transformer(name, transformer=ProjectionTransformer(1, 0), inputs=[arbitrary], outputs=[arbitrary])
            # FIXME: this is a hack to avoid adding&removing a column if an error occurs durign the above call...
            self._transformers[-1]['outputs'] = [name]
        elif type is not None:
            self.add_arbitrary(name, type=type, config=config)
        else:
            raise TypeError('You must specify either the type of the column or an associated arbitrary.')

        self._columns.append(name)

    def add_arbitrary(self, name, *, type, config=None):
        """Register an arbitrary to the schema."""
        if name in self._arbitraries:
            raise SchemaError('Arbitrary {!r} is already defined.'.format(name))
        self._arbitraries[name] = {'type': type, 'config': config or {}}

    def add_transformer(self, name, *, transformer, inputs, outputs):
        """Register a transformer to the schema."""
        if name in (trans['name'] for trans in self._transformers):
            raise SchemaError('Transformer {!r} is already defined.'.format(name))
        if len(inputs) != transformer.arity:
            msg = 'Got {} inputs: {} but transformer\'s arity is {.arity}.'
            raise SchemaError(msg.format(len(inputs), to_string_list(inputs), transformer))
        if len(outputs) != transformer.num_outputs:
            msg = 'Got {} outputs: {} but transformer\'s number of outputs is {.num_outputs}.'
            raise SchemaError(msg.format(len(outputs), to_string_list(outputs), transformer))
        defined_names = self._arbitraries.keys() | set(self._columns)
        undefined_inputs = set(inputs) - defined_names
        undefined_outputs = set(outputs) - defined_names
        if undefined_inputs:
            raise SchemaError("Inputs: {} are not defined in the schema.".format(to_string_list(undefined_inputs)))
        if undefined_outputs:
            raise SchemaError("Outputs: {} are not defined in the schema.".format(to_string_list(undefined_outputs)))

        unique_outputs = set(outputs)
        if len(unique_outputs) != len(outputs):
            output_counts = (output for output, count in Counter(outputs).items() if count > 1)
            multi_outputs = sorted(output_counts, key=lambda output: outputs.index(output))
            raise SchemaError('Outputs must be unique. Got multiple {} outputs.'.format(to_string_list(multi_outputs)))

        self._transformers.append({
            'name': name,
            'transformer': transformer,
            'inputs': inputs,
            'outputs': outputs,
        })

    @classmethod
    def parse(cls, text):
        data = json.loads(text)
        if not 'version' in data:
            raise MissingVersionError()
        elif not isinstance(data['version'], str) or not re.match('^\d+\.\d+$', data['version']):
            raise InvalidVersionNumberError(data['version'])

        schema = cls()
        for name in data['header']:
            schema.define_column(name)
        return schema


class Transformer(metaclass=ABCMeta):
    def __init__(self, arity, num_outputs):
        self._arity = arity
        self._num_outputs = num_outputs

    @property
    def arity(self):
        return self._arity

    @property
    def num_outputs(self):
        return self._num_outputs

    @abstractmethod
    def __call__(self, inputs):
        if len(inputs) != self._arity:
            raise ValueError('This transformer requires {} inputs. Got {} instead.'.format(self._arity, len(inputs)))


class FunctionalTransformer(Transformer):
    def __init__(self, callable, *, num_outputs=1):
        super().__init__(len(inspect.signature(callable).parameters), num_outputs)
        self._callable = callable

    def __call__(self, inputs):
        super().__call__(inputs)
        result = self._callable(*inputs)
        if self.num_outputs == 1:
            return (result,)
        return result

    def __eq__(self, other):
        return isinstance(other, FunctionalTransformer) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(self._callable)


class ProjectionTransformer(Transformer):
    def __init__(self, arity, index):
        super().__init__(arity, 1)
        self._index = index

    def __call__(self, inputs):
        return (inputs[self._index],)

    def __eq__(self, other):
        return isinstance(other, ProjectionTransformer) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
