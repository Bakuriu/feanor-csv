import inspect
import random
from abc import ABCMeta, abstractmethod
from collections import Counter
from itertools import chain
from types import SimpleNamespace

from .util import to_string_list


class SchemaError(ValueError):
    pass


class Schema:
    def __init__(self, *, show_header=True):
        self._show_header = show_header
        self._columns = []
        self._arbitraries = {}
        self._transformers = []

    def __eq__(self, other):
        return isinstance(other, Schema) and self.__dict__ == other.__dict__

    def __str__(self):
        return 'Schema(\n\tcolumns={},\n\tarbitraries={{{}}},\n\ttransformers={}\n\tshow_header={}\n)'.format(
            self._columns,
            ', '.join(': '.join([name, str(arb)]) for name, arb in self._arbitraries.items()),
            ', '.join(map(str, self._transformers)),
            self._show_header,
        )

    __repr__ = __str__

    @property
    def columns(self):
        return tuple(self._columns)

    @property
    def arbitraries(self):
        """The arbitraries used in the schema.

        Note: the order of the returned list is undefined.
        """
        return tuple(SimpleNamespace(name=name, **values) for name, values in self._arbitraries.items())

    @property
    def transformers(self):
        """The transformers used in the schema.

        Note: the order of the returned list is undefined."""
        return tuple(SimpleNamespace(**transformer) for transformer in self._transformers)

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
        defined_names = (
                self._arbitraries.keys()
                | set(self._columns)
                | set(chain.from_iterable(trans['outputs'] for trans in self._transformers))
        )
        undefined_inputs = set(inputs) - defined_names
        if undefined_inputs:
            raise SchemaError("Inputs: {} are not defined in the schema.".format(to_string_list(undefined_inputs)))

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
        super().__call__(inputs)
        return (inputs[self._index],)

    def __eq__(self, other):
        return isinstance(other, ProjectionTransformer) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


class ChoiceTransformer(Transformer):
    def __init__(self, arity, left_config, right_config):
        super().__init__(arity, arity // 2)
        self._left_config = left_config
        self._right_config = right_config
        if not isinstance(self._left_config, (int, float)) or not (0 <= self._left_config <= 1):
            raise TypeError('Invalid configuration for choice operator: {!r}'.format(self._left_config))
        if not isinstance(self._right_config, (int, float)) or not (0 <= self._right_config <= 1):
            raise TypeError('Invalid configuration for choice operator: {!r}'.format(self._right_config))
        if self._left_config + self._right_config > 1:
            raise ValueError(
                'Invalid configuration for choice operator: {!r} {!r}'.format(self._left_config, self._right_config))
        self._right_config += self._left_config

    def __call__(self, inputs):
        super().__call__(inputs)
        left_inputs = inputs[:self.num_outputs]
        right_inputs = inputs[self.num_outputs:]
        value = random.random()
        if value <= self._left_config:
            return left_inputs
        elif value <= self._right_config:
            return right_inputs
        else:
            return (None,) * self.num_outputs

    def __eq__(self, other):
        return isinstance(other, ChoiceTransformer) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


class MergeTransformer(Transformer):
    def __init__(self, arity):
        super().__init__(arity, arity // 2)

    def __call__(self, inputs):
        super().__call__(inputs)
        left_inputs = inputs[:self.num_outputs]
        right_inputs = inputs[self.num_outputs:]
        return tuple(x + y for x, y in zip(left_inputs, right_inputs))

    def __eq__(self, other):
        return isinstance(other, MergeTransformer) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


class IdentityTransformer(Transformer):
    def __init__(self, arity):
        super().__init__(arity, arity)

    def __call__(self, inputs):
        super().__call__(inputs)
        return tuple(inputs)

    def __eq__(self, other):
        return isinstance(other, IdentityTransformer) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
