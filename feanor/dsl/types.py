from abc import ABCMeta, abstractmethod
from itertools import chain


class Type(metaclass=ABCMeta):
    def __init__(self, name, num_outputs=1):
        self.name = name
        self.num_outputs = num_outputs

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name and self.num_outputs == other.num_outputs

    def __hash__(self):
        return hash((self.name, self.num_outputs))


class SimpleType(Type):
    def __init__(self, name):
        super().__init__(name)


class CompositeType(Type):
    def __init__(self, types):
        self.types = tuple(flatten_types(types, self.__class__))
        self._expanded_name = self.compute_name(self.types)
        super().__init__(self.__class__.__name__[:-4], self.compute_num_outputs(self.types))

    def __str__(self):
        return self._expanded_name

    __repr__ = __str__

    @classmethod
    def compute_name(cls, types):
        return '{}({})'.format(cls.__name__[:-4], ', '.join(ty.name for ty in types))

    @classmethod
    @abstractmethod
    def compute_num_outputs(cls, types):
        raise NotImplementedError

    def __eq__(self, other):
        return super().__eq__(other) and self.types == other.types

    def __hash__(self):
        return hash((super().__hash__(),) + self.types)


class ParallelType(CompositeType):

    @classmethod
    def compute_num_outputs(cls, types):
        return sum(ty.num_outputs for ty in types)


class ChoiceType(CompositeType):
    def __init__(self, types):
        super().__init__(types)
        self.types = tuple(sorted(set(self.types), key=lambda type_: hash(type_)))
        self._expanded_name = self.compute_name(self.types)

    @classmethod
    def compute_num_outputs(cls, types):
        tys_num_outputs = tuple(ty.num_outputs for ty in types)
        if len(set(tys_num_outputs)) != 1:
            different_outputs = ', '.join(map(str, tys_num_outputs))
            raise ValueError('Types must all have same number of outputs. Got {} instead.'.format(different_outputs))
        return tys_num_outputs[0]


def flatten_types(types, base_class):
    return chain.from_iterable([ty] if not isinstance(ty, base_class) else ty.types for ty in types)
