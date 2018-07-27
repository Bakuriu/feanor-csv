from abc import ABCMeta, abstractmethod
from itertools import chain


class Type(metaclass=ABCMeta):
    def __init__(self, name, num_outputs=1, config=None):
        self.name = name
        self.num_outputs = num_outputs
        self.config = config or {}

    def __str__(self):
        return self.name


class SimpleType(Type):
    def __init__(self, name, config=None):
        super().__init__(name, config=config)


class CompositeType(Type):
    def __init__(self, types, config=None):
        self.types = tuple(flatten_types(types, self.__class__))
        name = '{}({})'.format(self.__class__.__name__[:-4], ', '.join(ty.name for ty in self.types))
        super().__init__(name, self.compute_num_outputs(self.types), config=config)

    @classmethod
    @abstractmethod
    def compute_num_outputs(cls, types):
        raise NotImplementedError


class ParallelType(CompositeType):

    @classmethod
    def compute_num_outputs(cls, types):
        return sum(ty.num_outputs for ty in types)


class SumType(CompositeType):

    @classmethod
    def compute_num_outputs(cls, types):
        tys_num_outputs = tuple(ty.num_outputs for ty in types)
        if len(set(tys_num_outputs)) != 1:
            different_outputs = ', '.join(map(str, tys_num_outputs))
            raise ValueError('Types must all have same number of outputs. Got {} instead.'.format(different_outputs))
        return any(tys_num_outputs)


def flatten_types(types, base_class):
    return chain.from_iterable([ty] if not isinstance(ty, base_class) else ty._types for ty in types)
