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
        return lambda random_funcs, config=None: None
