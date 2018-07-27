from .ast import *
from .types import *


def default_compatibility(x, y):
    return x == y


default_compatibility.upper_bound = lambda x, _: x


def get_type(tree: AstNode, env=None, func_env=None, compatible=default_compatibility):
    if env is None:
        env = {}
    if func_env is None:
        func_env = {}

    if isinstance(tree, TypeNameNode):
        return SimpleType(tree.name)


def _get_type_from_definition(type_definition: TypeNameNode, env, func_env, compatible):
    return SimpleType(type_definition.name, type_definition.config)


def _get_type_from_reference(reference: ReferenceNode, env, func_env, compatible):
    return env[reference.name]


def _get_type_from_assignment(assignment: AssignNode, env, func_env, compatible):
    ty = get_type(assignment.expr, env, func_env)
    if assignment.name in env:
        raise TypeError('Already defined name {!r}'.format(assignment.name))
    env[assignment.name] = ty
    return ty


def _get_type_from_projection(projection: ProjectionNode, env, func_env, compatible):
    ty = get_type(projection.expr)
    if not isinstance(ty, CompositeType):
        raise TypeError('Projection on a non-composite type {}'.format(ty))
    if not all(index in range(len(ty.types)) for index in projection.indices):
        raise TypeError('Indices out of range for projection')
    return ParallelType(ty.types[index] for index in projection.indices)


def _get_type_from_call(call: CallNode, env, func_env, compatible):
    arg_types = [get_type(arg, env, func_env) for arg in call.arguments]
    expected_arg_types, ret_type = func_env[call.func_name]
    if len(arg_types) != len(expected_arg_types):
        raise TypeError(
            'Incorrect number of arguments to function {}: {} instead of {}'.format(call.func_name, len(arg_types),
                                                                                    len(expected_arg_types)))
    for i, (arg_type, expected_arg_type) in enumerate(zip(arg_types, expected_arg_types)):
        if not compatible(arg_type, expected_arg_type):
            raise TypeError(
                'Incompatible types for argument {} of {}: {} instead of {}'.format(i, call.func_name, arg_type,
                                                                                    expected_arg_type))
    return ret_type


def _get_type_from_bin_op(bin_op: BinaryOpNode, env, func_env, compatible):
    if bin_op.operator == '+':
        return _get_type_from_merge(bin_op, env, func_env, compatible)
    return _get_type_from_parallel_composition(bin_op, env, func_env, compatible)


def _get_type_from_merge(bin_op: BinaryOpNode, env, func_env, compatible):
    left_ty = get_type(bin_op.left, env, func_env, compatible)
    right_ty = get_type(bin_op.right, env, func_env, compatible)
    if not compatible(left_ty, right_ty):
        raise TypeError('Cannot add incompatible types {} and {}'.format(left_ty, right_ty))
    return SumType([left_ty, right_ty])

def _get_type_from_parallel_composition(parallel: BinaryOpNode, env, func_env, compatible):
    left_ty = get_type(parallel.left, env, func_env, compatible)
    right_ty = get_type(parallel.right, env, func_env, compatible)
    return ParallelType([left_ty, right_ty])