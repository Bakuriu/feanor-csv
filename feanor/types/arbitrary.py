import re
import ast
from types import SimpleNamespace
from abc import ABCMeta, abstractmethod


class ParsingError(ValueError):
    """Exception raised when the expression describing an arbitrary type is invalid."""


class Arbitrary(metaclass=ABCMeta):
    def __init__(self, random_funcs, type_name, config):
        self._random_funcs = random_funcs
        self._type_name = type_name
        conf = self.default_config()
        conf.update(config or {})
        self._config = SimpleNamespace(**conf)

    @property
    def type(self):
        return self._type_name

    @property
    def config(self):
        return self._config

    @classmethod
    def default_config(cls):
        return {}

    @abstractmethod
    def __call__(self):
        raise NotImplementedError


ARBITRARY_TYPE_REGEX = re.compile(r'(?P<type_name>\w+)(?P<config>{.*\})?$', re.DOTALL)


def parse_type(arbitrary_type):
    """Parse the type of an Arbitrary.

    An arbitrary type can have the following two forms:

      - a plain type name. E.g. 'int', or 'tax_code'.
      - a type name with a configuration attached. E.g. 'int{"lowerbound":10}'.

    The type name has to match the `\w+` regex, while the optional configuration must be a valid python
    `dict` literal.

    Not passing any configuration is equivalent to passing a configuration of `{}`.

    Examples
    ========

        >>> parse_type('int')
        ('int', {})
        >>> parse_type('int{}')
        ('int', {})
        >>> parse_type('int{"lowerbound": 10}')
        ('int', {'lowerbound': 10})
        >>> parse_type('int{"lowerbound": 10, "upperbound": 20}')
        ('int', {'lowerbound': 10, 'upperbound': 20})

    """
    match = ARBITRARY_TYPE_REGEX.match(arbitrary_type)
    if not match:
        raise ParsingError('Expression does not describe an arbitrary type:\n{!r}\ndoes not match regex: "(?s)\w+{{.*\}}$"'.format(arbitrary_type))

    type_name, config = match.groups()
    if config is not None:
        try:
            config = ast.literal_eval(config)
        except SyntaxError:
            raise ParsingError(f'Expression is not a valid dict literal: {repr(config)}')
        except ValueError:
            raise ParsingError(f'Expression is not a valid dict literal: {repr(config)}.\nMaybe you forgot to quote a key?')
    return type_name, (config or {})