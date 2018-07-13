from abc import ABCMeta, abstractmethod


class Arbitrary(metaclass=ABCMeta):
    def __init__(self, random_funcs, type_name):
        self._random_funcs = random_funcs
        self._type_name = type_name

    @property
    def type(self):
        return self._type_name

    @abstractmethod
    def __call__(self):
        raise NotImplementedError