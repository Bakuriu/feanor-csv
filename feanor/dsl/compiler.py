from .ast import *
from .types import *


def default_compatibility(x, y):
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
    return SimpleType(type_definition.children[0].name, type_definition.children[1].config)


def _get_type_from_reference(reference: ReferenceNode, env, func_env, compatible):
    return env[reference.children[0].name]


def _get_type_from_assignment(assignment: AssignNode, env, func_env, compatible):
    ty = get_type(assignment.children[0], env, func_env, compatible)
    name = assignment.children[1].name
    if name in env:
        raise TypeError('Already defined name {!r}'.format(name))
    env[name] = ty
    return ty


def _get_type_from_projection(projection: ProjectionNode, env, func_env, compatible):
    ty = get_type(projection.children[0], env, func_env, compatible)
    if not isinstance(ty, CompositeType):
        raise TypeError('Projection on a non-composite type {}'.format(ty))
    if not all(index.literal in range(len(ty.types)) for index in projection.children[1:]):
        raise TypeError('Indices out of range for projection')
    indices = projection.children[1:]
    if len(indices) > 1:
        return ParallelType(ty.types[index.literal] for index in indices)
    return ty.types[indices[0].literal]


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
    return ret_type


def _get_type_from_bin_op(bin_op: BinaryOpNode, env, func_env, compatible):
    if bin_op.children[0].name == '+':
        return _get_type_from_merge(bin_op, env, func_env, compatible)
    elif bin_op.children[0].name == '|':
        return _get_type_from_choice(bin_op, env, func_env, compatible)
    return _get_type_from_parallel_composition(bin_op, env, func_env, compatible)


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
