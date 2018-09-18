from abc import ABCMeta
from typing import Sequence, Tuple, List


class AstNode(metaclass=ABCMeta):

    def __init__(self, *children):
        self._children = children
        self.info = {}

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__[:-4], ', '.join(map(str, self._children)))

    __repr__ = __str__

    @property
    def children(self):
        return self._children

    def is_leaf(self):
        return not self.children

    def __eq__(self, other):
        if not isinstance(other, AstNode):
            return False
        return self.__class__ == other.__class__ and self._children == other._children

    @classmethod
    def of(cls, *args, **kwargs):  # pragma: no cover
        # noinspection PyArgumentList
        return cls(*args, **kwargs)

    def visit(self, func):
        """Visit this node."""
        if self.is_leaf():
            return func(self)
        else:
            children_results = (child.visit(func) if child is not None else None for child in self._children)
            return func(self, *children_results)


class ExprNode(AstNode):
    """Base-class for expression nodes."""


class Identifier(AstNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return super().__eq__(other) and self.name == other.name

    @classmethod
    def of(cls, name):
        if isinstance(name, cls):
            return name
        return cls(name)


class Config(AstNode):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def __str__(self):
        return str(self.config)

    def __eq__(self, other):
        return super().__eq__(other) and self.config == other.config

    @classmethod
    def of(cls, config):
        config = config or {}
        if isinstance(config, cls):
            return config
        return cls(config)


class TypeNameNode(ExprNode):
    def __init__(self, identifier: Identifier, arbitrary: Identifier, config: Config):
        super().__init__(identifier, arbitrary, config)

    @classmethod
    def of(cls, name: str, arbitrary: str = 'default', config=None):
        return cls(Identifier.of(name), Identifier.of(arbitrary), Config.of(config))


class ReferenceNode(ExprNode):
    def __init__(self, identifier: Identifier):
        super().__init__(identifier)

    @classmethod
    def of(cls, name):
        return cls(Identifier.of(name))


class AssignNode(ExprNode):
    def __init__(self, expr, identifier: Identifier):
        super().__init__(expr, identifier)

    @classmethod
    def of(cls, expr, name):
        return cls(expr, Identifier.of(name))


class LiteralNode(AstNode):
    def __init__(self, literal):
        super().__init__()
        self.literal = literal
        self.literal_type = type(literal)

    def __str__(self):
        return str(self.literal)

    def __eq__(self, other):
        return super().__eq__(other) and self.literal_type == other.literal_type and self.literal == other.literal

    def to_plain_object(self):
        def maybe_to_plain_object(elem):
            return elem.to_plain_object() if isinstance(elem, LiteralNode) else elem

        if isinstance(self.literal, (list, set)):
            return self.literal_type(map(maybe_to_plain_object, self.literal))
        elif isinstance(self.literal, dict):
            return {key: maybe_to_plain_object(value) for key, value in self.literal.items()}
        else:
            return self.literal

    @classmethod
    def of(cls, literal):
        if isinstance(literal, LiteralNode):
            return literal
        return cls(literal)


class BinaryOpNode(ExprNode):
    def __init__(self, operator: Identifier, left: ExprNode, left_config: LiteralNode, right: ExprNode,
                 right_config: LiteralNode):
        super().__init__(operator, left, left_config, right, right_config)

    @classmethod
    def of(cls, operator, left, right, left_config=None, right_config=None):
        left_config = LiteralNode.of(left_config) if left_config is not None else None
        right_config = LiteralNode.of(right_config) if right_config is not None else None
        return cls(Identifier.of(operator), left, left_config, right, right_config)


class CallNode(ExprNode):
    def __init__(self, func_name: Identifier, arguments: Sequence[ExprNode]):
        super().__init__(func_name, *arguments)

    @classmethod
    def of(cls, func_name, arguments):
        return cls(Identifier.of(func_name), arguments)


class ProjectionNode(ExprNode):
    def __init__(self, expr: ExprNode, index: LiteralNode, *other_indices: LiteralNode):
        super().__init__(expr, index, *other_indices)

    @classmethod
    def of(cls, expr, *indices):
        return cls(expr, *map(LiteralNode, indices))


class LetNode(ExprNode):
    def __init__(self, assignments: List[AssignNode], expr: ExprNode):
        names = [node.children[1].name for node in assignments]
        if len(names) != len(set(names)):
            raise ParsingError('Cannot redefine an already assigned name.')
        super().__init__(*assignments, expr)

    @classmethod
    def of(cls, defines: Sequence[Tuple[str, ExprNode]], expr: ExprNode):
        return cls([AssignNode(e, Identifier.of(name)) for name, e in defines], expr)


class ParsingError(ValueError):
    """Exception raised when the expression describing an arbitrary type is invalid."""
