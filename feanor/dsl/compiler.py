import re

from ..schema import (
    Schema, FunctionalTransformer, ProjectionTransformer, ChoiceTransformer, MergeTransformer,
    IdentityTransformer,
)
from .ast import *
from .types import *

__all__ = ['default_compatibility', 'get_type', 'compile_expression']


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


def get_type(tree: ExprNode, env=None, func_env=None, compatible=default_compatibility) -> Type:
    if env is None:
        env = {}
    if func_env is None:
        func_env = {}

    func_mapping = {
        TypeNameNode: _get_type_from_definition,
        ReferenceNode: _get_type_from_reference,
        AssignNode: _get_type_from_assignment,
        ProjectionNode: _get_type_from_projection,
        CallNode: _get_type_from_call,
        BinaryOpNode: _get_type_from_bin_op,

    }

    return func_mapping[tree.__class__](tree, env, func_env, compatible)


def _get_type_from_definition(type_definition: TypeNameNode, env, func_env, compatible):
    ty = SimpleType(type_definition.children[0].name, type_definition.children[1].config)
    type_definition.info['type'] = ty
    return ty


def _get_type_from_reference(reference: ReferenceNode, env, func_env, compatible):
    ty = env[reference.children[0].name]
    reference.info['type'] = ty
    return ty


def _get_type_from_assignment(assignment: AssignNode, env, func_env, compatible):
    ty = get_type(assignment.children[0], env, func_env, compatible)
    name = assignment.children[1].name
    if name in env:
        raise TypeError('Already defined name {!r}'.format(name))
    env[name] = ty
    assignment.info['type'] = ty
    return ty


def _get_type_from_projection(projection: ProjectionNode, env, func_env, compatible):
    ty = get_type(projection.children[0], env, func_env, compatible)
    if not isinstance(ty, CompositeType):
        raise TypeError('Projection on a non-composite type {}'.format(ty))
    if not all(index.literal in range(len(ty.types)) for index in projection.children[1:]):
        raise TypeError('Indices out of range for projection')
    indices = projection.children[1:]
    if len(indices) > 1:
        ret_type = ParallelType(ty.types[index.literal] for index in indices)
    else:
        ret_type = ty.types[indices[0].literal]
    projection.info['type'] = ret_type
    return ret_type


def _get_type_from_call(call: CallNode, env, func_env, compatible):
    arg_types = [get_type(arg, env, func_env, compatible) for arg in call.children[1:]]
    func_name = call.children[0].name
    expected_arg_types, ret_type = func_env[func_name]
    if len(arg_types) != len(expected_arg_types):
        raise TypeError(
            f'Incorrect number of arguments to function {func_name}: {len(arg_types)} instead of {len(expected_arg_types)}')
    for i, (arg_type, expected_arg_type) in enumerate(zip(arg_types, expected_arg_types)):
        if not compatible(arg_type, expected_arg_type):
            raise TypeError(
                f'Incompatible types for argument {i} of {func_name}: {arg_type} instead of {expected_arg_type}')
    call.info['type'] = ret_type
    return ret_type


def _get_type_from_bin_op(bin_op: BinaryOpNode, env, func_env, compatible):
    if bin_op.children[0].name == '+':
        ty = _get_type_from_merge(bin_op, env, func_env, compatible)
    elif bin_op.children[0].name == '|':
        ty = _get_type_from_choice(bin_op, env, func_env, compatible)
    else:
        ty = _get_type_from_parallel_composition(bin_op, env, func_env, compatible)
    bin_op.info['type'] = ty
    return ty


def _get_type_from_merge(merge: BinaryOpNode, env, func_env, compatible):
    left_ty = get_type(merge.children[1], env, func_env, compatible)
    right_ty = get_type(merge.children[3], env, func_env, compatible)
    if not compatible(left_ty, right_ty):
        raise TypeError('Cannot add incompatible types {} and {}'.format(left_ty, right_ty))
    return MergeType([left_ty, right_ty],
                     {'left_config': merge.children[2] or {}, 'right_config': merge.children[4] or {}})


def _get_type_from_parallel_composition(parallel: BinaryOpNode, env, func_env, compatible):
    left_ty = get_type(parallel.children[1], env, func_env, compatible)
    right_ty = get_type(parallel.children[3], env, func_env, compatible)
    return ParallelType([left_ty, right_ty],
                        {'left_config': parallel.children[2] or {}, 'right_config': parallel.children[4] or {}})


def _get_type_from_choice(choice: BinaryOpNode, env, func_env, compatible):
    left_ty = get_type(choice.children[1], env, func_env, compatible)
    right_ty = get_type(choice.children[3], env, func_env, compatible)
    return ChoiceType([left_ty, right_ty],
                      {'left_config': choice.children[2] or {}, 'right_config': choice.children[4] or {}})


def compile_expression(expr: ExprNode, func_env=None, compatible=default_compatibility) -> Schema:
    func_env = {} if func_env is None else {}
    env = {}

    schema = Schema()

    cur_arbitrary_id = 0
    cur_transformer_id = 0

    def new_transformer_name():
        nonlocal cur_transformer_id
        name = 'transformer#{}'.format(cur_transformer_id)
        cur_transformer_id += 1
        return name

    def visitor(cur_node: ExprNode, *children_values):
        nonlocal cur_arbitrary_id, cur_transformer_id

        if isinstance(cur_node, Identifier):
            return cur_node.name
        elif isinstance(cur_node, Config):
            return cur_node.config
        elif isinstance(cur_node, LiteralNode):
            return cur_node.literal
        elif isinstance(cur_node, TypeNameNode):
            ty, config = children_values
            name = 'arbitrary#{}'.format(cur_arbitrary_id)
            cur_arbitrary_id += 1
            schema.add_arbitrary(name, type=ty, config=config)
            return (name,)
        elif isinstance(cur_node, AssignNode):
            result, name = children_values
            env[name] = result
            if len(result) == 1:
                if isinstance(result[0], tuple):
                    from_ = result[0][1]
                else:
                    from_ = result[0]
                schema.add_transformer(new_transformer_name(), inputs=[from_], outputs=[name],
                                       transformer=IdentityTransformer(1))
                return ((result[0], name),)
            else:
                names = ['{}#{}'.format(name, i) for i in range(len(result))]
                schema.add_transformer(new_transformer_name(), inputs=list(result), outputs=names,
                                       transformer=IdentityTransformer(len(result)))
                return names
        elif isinstance(cur_node, BinaryOpNode):
            operator, left, left_config, right, right_config = children_values
            if operator == '.':
                return left + right
            elif operator == '|':
                transformer_name = new_transformer_name()
                left_config = left_config.literal if left_config is not None else 0.5
                right_config = right_config.literal if right_config is not None else 0.5
                transformer = ChoiceTransformer(len(left) + len(right), left_config, right_config)
                schema.add_transformer(transformer_name, inputs=list(left + right), outputs=[transformer_name],
                                       transformer=transformer)
                return (transformer_name,)
            elif operator == '+':
                transformer_name = new_transformer_name()
                transformer = MergeTransformer(len(left) + len(right), left_config, right_config)
                outputs = ['{}#{}'.format(transformer_name, i) for i in range(transformer.num_outputs)]
                schema.add_transformer(transformer_name, inputs=list(left + right), outputs=outputs,
                                       transformer=transformer)
                return tuple(outputs)
            else:
                raise TypeError('Invalid operator ' + operator)
        elif isinstance(cur_node, ReferenceNode):
            name, = children_values
            transformer_name = new_transformer_name()
            transformer = IdentityTransformer(len(env[name]))
            schema.add_transformer(transformer_name, inputs=[name], outputs=[transformer_name], transformer=transformer)
            return (transformer_name,)
        elif isinstance(cur_node, ProjectionNode):
            result, *indices = children_values
            transformer_name = new_transformer_name()
            schema.add_transformer(transformer_name, inputs=list(result), outputs=[transformer_name],
                                   transformer=ProjectionTransformer(len(result), *indices))
            return (transformer_name,)
        else:
            raise TypeError('Invalid node ' + str(cur_node))

    result = expr.visit(visitor)
    identity = IdentityTransformer(1)
    for i, name in enumerate(result):
        if isinstance(name, tuple):
            name, col_name = name
            schema.add_column(col_name)
        elif name.startswith('arbitrary#') or name.startswith('transformer#'):
            col_name = 'column#{}'.format(i)
            schema.add_column(col_name)
            schema.add_transformer(new_transformer_name(), inputs=[name], outputs=[col_name], transformer=identity)
        else:
            schema.add_column(name)
    return schema