import random
from abc import ABCMeta, abstractmethod

from .dsl.compiler import SimpleCompatibility


class Library(metaclass=ABCMeta):
    def __init__(self, global_configuration, random_funcs):
        self.global_configuration = global_configuration
        self.random_funcs = random_funcs

    def make_arbitrary(self, name, config):
        factory = self.get_arbitrary_factory(name)
        the_config = self.global_configuration.get(name, {})
        the_config.update(config)
        return factory(self.random_funcs, the_config)

    @abstractmethod
    def compatibility(cls):
        raise NotImplementedError

    @abstractmethod
    def env(cls):
        raise NotImplementedError

    @abstractmethod
    def func_env(cls):
        raise NotImplementedError

    @abstractmethod
    def get_arbitrary_factory(self, name):
        raise NotImplementedError

    @abstractmethod
    def upperbounds(cls):
        """This method should return an iterable whose elements are upperbound chains.

        An upperbound chain is an iterable of `str` objects representing type names.
        It represents a path in the compatibility graph.

        For example, the following upperbound chain:

            ('int', 'float', 'complex')

        defines `float` as upperbound of `int` and `complex` as upperbound of both `float` and `int`.
        I.e. when the `+` operation is performed on types `int` and `float` the result will be of type `float`.

        """
        raise NotImplementedError


class EmptyLibrary(Library):
    def __init__(self):
        super().__init__({}, random)
    def compatibility(cls):
        return SimpleCompatibility(lambda x, y: x)

    def env(cls):
        return {}

    def func_env(cls):
        return {}

    def get_arbitrary_factory(self, name):
        return lambda name: None

    def upperbounds(cls):
        return set()