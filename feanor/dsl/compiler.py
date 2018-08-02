from itertools import starmap
from typing import List

from ..util import overloaded
from .ast import *
from .types import *
from ..schema import *

__all__ = ['default_compatibility', 'TypeInferencer', 'Compiler']


def default_compatibility(x, y):
    """The default compatibility function for the type inferencer.

    The default compatibility is an equivalence relation defined by the following rules:

     - two `SimpleType`s are compatible if they are identical (same name and config).
     - two `CompositeType`s are compatible if:
       + they are of the same class
       + they have the same configuration
       + they have the same number of outputs
       + all their types "children" are default-compatible

    """
    if isinstance(x, SimpleType) and isinstance(y, SimpleType):
        return x == y
    elif isinstance(x, CompositeType) and isinstance(y, CompositeType):
        return (
                x.__class__ == y.__class__
                and x.num_outputs == y.num_outputs
                and x.config == y.config
                and all(default_compatibility(a, b) for a, b in zip(x.types, y.types))
        )


class TypeInferencer:
    def __init__(self, env=None, func_env=None, compatible=default_compatibility):
        self.env = env if env is not None else {}
        self.func_env = func_env if func_env is not None else {}
        self.compatible = compatible

    @overloaded
    def infer(self, tree: ExprNode) -> Type:
        raise TypeError('Invalid node type: {}'.format(tree))

    @infer.register(TypeNameNode)
    def _(self, tree: TypeNameNode):
        inferred_type = SimpleType(tree.children[0].name, tree.children[1].config)
        tree.info['type'] = inferred_type
        return inferred_type

    @infer.register(ReferenceNode)
    def _(self, tree: ReferenceNode):
        inferred_type = self.env[tree.children[0].name]
        tree.info['type'] = inferred_type
        return inferred_type

    @infer.register(AssignNode)
    def _(self, tree: AssignNode):
        inferred_type = self.infer(tree.children[0])
        name = tree.children[1].name
        if name in self.env:
            raise TypeError('Already defined name {!r}'.format(name))
        self.env[name] = inferred_type
        tree.info['type'] = inferred_type
        return inferred_type

    @infer.register(ProjectionNode)
    def _(self, tree: ProjectionNode):
        argument_type = self.infer(tree.children[0])
        if not isinstance(argument_type, CompositeType):
            raise TypeError('Projection on a non-composite type {}'.format(argument_type))
        if not all(index.literal in range(len(argument_type.types)) for index in tree.children[1:]):
            raise TypeError('Indices out of range for projection')
        indices = tree.children[1:]
        if len(indices) > 1:
            inferred_type = ParallelType(argument_type.types[index.literal] for index in indices)
        else:
            inferred_type = argument_type.types[indices[0].literal]
        tree.info['type'] = inferred_type
        return inferred_type

    @infer.register(CallNode)
    def _(self, tree: CallNode):
        inferred_arg_types = list(map(self.infer, tree.children[1:]))
        func_name = tree.children[0].name
        expected_arg_types, inferred_type = self.func_env[func_name]
        if len(inferred_arg_types) != len(expected_arg_types):
            raise TypeError(
                f'Incorrect number of arguments to function {func_name}: '
                f'{len(inferred_arg_types)} instead of {len(expected_arg_types)}')
        for i, (arg_type, expected_arg_type) in enumerate(zip(inferred_arg_types, expected_arg_types)):
            if not self.compatible(arg_type, expected_arg_type):
                raise TypeError(
                    f'Incompatible types for argument {i} of {func_name}: {arg_type} instead of {expected_arg_type}')
        tree.info['type'] = inferred_type
        return inferred_type

    @infer.register(BinaryOpNode)
    def _(self, tree: BinaryOpNode):
        left_ty = self.infer(tree.children[1])
        right_ty = self.infer(tree.children[3])
        if tree.children[0].name == '+':
            inferred_type = self._infer_merge(tree, left_ty, right_ty)
        elif tree.children[0].name == '|':
            inferred_type = self._infer_choice(tree, left_ty, right_ty)
        else:
            inferred_type = self._infer_concat(tree, left_ty, right_ty)
        tree.info['type'] = inferred_type
        return inferred_type

    def _infer_merge(self, merge: BinaryOpNode, left_ty, right_ty):
        if isinstance(left_ty, ParallelType) and isinstance(right_ty, ParallelType):
            if left_ty.num_outputs != right_ty.num_outputs:
                raise TypeError('Incompatible types for merge: {!r} and {!r}.'.format(left_ty, right_ty))
            zipped_types = list(zip(left_ty.types, right_ty.types))
            if not all(starmap(self.compatible, zipped_types)):
                raise TypeError('Incompatible types for merge: {!r} and {!r}'.format(left_ty, right_ty))
            new_inner_types = list(map(MergeType, zipped_types))
            return ParallelType(new_inner_types)
        elif isinstance(left_ty, ParallelType) ^ isinstance(right_ty, ParallelType):
            raise TypeError('Incompatible types for merge: {!r} and {!r}'.format(left_ty, right_ty))
        if not self.compatible(left_ty, right_ty):
            raise TypeError('Cannot add incompatible types {} and {}'.format(left_ty, right_ty))
        return MergeType([left_ty, right_ty])

    def _infer_choice(self, choice: BinaryOpNode, left_ty, right_ty):
        return ChoiceType([left_ty, right_ty],
                          {'left_config': choice.children[2] or {}, 'right_config': choice.children[4] or {}})

    def _infer_concat(self, parallel: BinaryOpNode, left_ty, right_ty):
        return ParallelType([left_ty, right_ty])


class Compiler:
    def __init__(self, env=None, func_env=None, compatibility=default_compatibility, show_header=True):
        self.compatibility = compatibility
        self.func_env = func_env if func_env is not None else {}
        self.env = env if env is not None else {}
        self.typing_env = self.env.setdefault('::types::', {})
        self._inferencer = TypeInferencer(env=self.typing_env, func_env=self.func_env, compatible=self.compatibility)
        self._schema = Schema(show_header=show_header)
        self._cur_arbitrary_id = 0
        self._cur_transformer_id = 0
        self._compiled_expressions = []

    def compile(self, expr: ExprNode) -> Schema:
        self.feed_expression(expr)
        return self.complete_compilation()

    def feed_expression(self, expr: ExprNode) -> None:
        self._inferencer.infer(expr)
        self._compiled_expressions.append(expr.visit(self.visitor))

    def complete_compilation(self, *, column_names: List[str]=None) -> Schema:
        identity = IdentityTransformer(1)
        out_names = list(chain.from_iterable(res.info['out_names'] for res in self._compiled_expressions))
        if column_names is None:
            column_names = []
            for i, name in enumerate(out_names):
                if name.startswith('arbitrary#') or name.startswith('transformer#'):
                    column_names.append('column#{}'.format(i))
                else:
                    column_names.append(name)

        for col_name in column_names:
            self._schema.add_column(col_name)

        if len(out_names) == len(column_names):
            for name, col_name in zip(out_names, column_names):
                if name != col_name:
                    self._schema.add_transformer(
                        self._new_transformer_name(),
                        inputs=[name], outputs=[col_name],
                        transformer=identity
                        )

        return self._schema

    @overloaded
    def visitor(self, cur_node: ExprNode, *children_values):
        raise TypeError('Invalid node ' + str(cur_node))

    @visitor.register(Identifier)
    def _(self, cur_node: Identifier):
        return cur_node.name

    @visitor.register(Config)
    def _(self, cur_node: Config):
        return cur_node.config

    @visitor.register(LiteralNode)
    def _(self, cur_node: LiteralNode):
        return cur_node.literal

    @visitor.register(TypeNameNode)
    def _(self, cur_node: TypeNameNode, *children_values):
        type_name, config = children_values
        name = self._new_arbitrary_name()
        self._schema.add_arbitrary(name, type=type_name, config=config)
        cur_node.info['assigned_name'] = None
        cur_node.info['in_names'] = [name]
        cur_node.info['out_names'] = [name]
        return cur_node

    @visitor.register(AssignNode)
    def _(self, cur_node: AssignNode, *children_values):
        result, name = children_values
        res_outputs = result.info['out_names']
        self.env[name] = res_outputs
        if len(res_outputs) == 1:
            self._schema.add_transformer(self._new_transformer_name(), inputs=res_outputs, outputs=[name],
                                         transformer=IdentityTransformer(1))
            cur_node.info['in_names'] = res_outputs
            cur_node.info['out_names'] = [name]
        else:
            names = ['{}#{}'.format(name, i) for i in range(len(res_outputs))]
            self._schema.add_transformer(self._new_transformer_name(), inputs=res_outputs, outputs=names,
                                         transformer=IdentityTransformer(len(res_outputs)))
            cur_node.info['in_names'] = res_outputs
            cur_node.info['out_names'] = names
        cur_node.info['assigned_name'] = name
        return cur_node

    @visitor.register(BinaryOpNode)
    def _(self, cur_node: AssignNode, *children_values):
        operator, left, left_config, right, right_config = children_values
        all_in_names = left.info['out_names'] + right.info['out_names']
        if operator == '.':
            cur_node.info['assigned_name'] = None
            cur_node.info['in_names'] = all_in_names
            cur_node.info['out_names'] = all_in_names
            return cur_node
        elif operator == '|':
            transformer_name = self._new_transformer_name()
            left_config = left_config.literal if left_config is not None else 0.5
            right_config = right_config.literal if right_config is not None else 0.5
            transformer = ChoiceTransformer(len(all_in_names), left_config, right_config)
            self._schema.add_transformer(transformer_name, inputs=all_in_names, outputs=[transformer_name],
                                         transformer=transformer)
            cur_node.info['assigned_name'] = None
            cur_node.info['in_names'] = all_in_names
            cur_node.info['out_names'] = [transformer_name]
            return cur_node
        elif operator == '+':
            transformer_name = self._new_transformer_name()
            transformer = MergeTransformer(len(all_in_names))
            outputs = ['{}#{}'.format(transformer_name, i) for i in range(transformer.num_outputs)]
            self._schema.add_transformer(transformer_name, inputs=all_in_names, outputs=outputs,
                                         transformer=transformer)
            cur_node.info['assigned_name'] = None
            cur_node.info['in_names'] = all_in_names
            cur_node.info['out_names'] = outputs
            return cur_node
        else:
            raise TypeError('Invalid operator ' + operator)

    @visitor.register(ReferenceNode)
    def _(self, cur_node: ReferenceNode, *children_values):
        name, = children_values
        cur_node.info['assigned_name'] = None
        cur_node.info['in_names'] = [name]
        cur_node.info['out_names'] = self.env[name]
        return cur_node

    @visitor.register(ProjectionNode)
    def _(self, cur_node: ProjectionNode, *children_values):
        result, *indices = children_values
        cur_node.info['assigned_name'] = None
        output_names = [n for i, n in enumerate(result.info['out_names']) if i in indices]
        cur_node.info['out_names'] = output_names
        cur_node.info['in_names'] = result.info['out_names']
        return cur_node

    def _new_transformer_name(self) -> str:
        name = 'transformer#{}'.format(self._cur_transformer_id)
        self._cur_transformer_id += 1
        return name

    def _new_arbitrary_name(self) -> str:
        name = 'arbitrary#{}'.format(self._cur_arbitrary_id)
        self._cur_arbitrary_id += 1
        return name
