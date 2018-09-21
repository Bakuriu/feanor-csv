from itertools import starmap

from .ast import *
from .types import *
from ..schema import *
from ..util import overloaded, consecutive_pairs

__all__ = ['SimpleCompatibility', 'PairBasedCompatibility', 'TypeInferencer', 'Compiler']


class Compatibility(metaclass=ABCMeta):
    @abstractmethod
    def get_upperbound(self, first_type: Type, second_type: Type) -> Type:
        raise NotImplementedError

    def is_compatible(self, first_type: Type, second_type: Type) -> bool:
        try:
            _ = self.get_upperbound(first_type, second_type)
        except TypeError:
            return False
        else:
            return True

    def is_assignable_to(self, first_type: Type, target_type: Type) -> bool:
        if first_type == target_type:
            return True

        try:
            upperbound = self.get_upperbound(first_type, target_type)
            return upperbound == target_type
        except TypeError:
            return False


class SimpleCompatibility(Compatibility):

    def __init__(self, upperbound):
        self._get_simple_type_upperbound = upperbound

    def get_upperbound(self, first_type: Type, second_type: Type) -> Type:
        first_simple = isinstance(first_type, SimpleType)
        second_simple = isinstance(second_type, SimpleType)

        if first_simple and second_simple:
            return self._get_simple_type_upperbound(first_type, second_type)

        if not first_simple and not second_simple:
            return self._get_composites_upperbound(first_type, second_type)

        if second_simple and not first_simple:
            # avoid symmetric cases.
            return self.get_upperbound(second_type, first_type)

        return self._get_simple_and_composite_upperbound(first_type, second_type)

    def _get_simple_and_composite_upperbound(self, first_type, second_type):
        if second_type.num_outputs != 1:
            raise TypeError(f'type {first_type} is incompatible with type {second_type}.\n'
                            f'Number of outputs differs: 1 != {second_type.num_outputs}.')
        if isinstance(second_type, ParallelType):
            return self.get_upperbound(first_type, second_type.types[0])
        else:
            return self._choice_upperbound(second_type, first_type)

    def _get_composites_upperbound(self, first_type, second_type):
        if first_type.num_outputs != second_type.num_outputs:
            raise TypeError(f'type {first_type} is incompatible with type {second_type}.\n'
                            f'Number of outputs differs: {first_type.num_outputs} != {second_type.num_outputs}.')

        if isinstance(first_type, ParallelType) and isinstance(second_type, ParallelType):
            return ParallelType(starmap(self.get_upperbound, zip(first_type.types, second_type.types)))

        if isinstance(first_type, ChoiceType):
            return self._choice_upperbound(first_type, second_type)
        else:
            return self._choice_upperbound(second_type, first_type)

    def _choice_upperbound(self, main: ChoiceType, other: Type) -> ChoiceType:
        return ChoiceType(self.get_upperbound(t, other) for t in main.types)


class PairBasedCompatibility(SimpleCompatibility):

    def __init__(self):
        super().__init__(upperbound=self._simple_type_upperbound)
        self._upperbound_pairs = set()

    def add_upperbounds(self, upperbounds):
        self._upperbound_pairs.update(chain.from_iterable(map(self._get_all_pairs, upperbounds)))

    def _simple_type_upperbound(self, first_type, second_type):
        first_type_name = first_type.name
        second_type_name = second_type.name
        if (first_type_name, second_type_name) in self._upperbound_pairs:
            return second_type
        elif (second_type_name, first_type_name) in self._upperbound_pairs:
            return first_type

        raise TypeError(f'type {first_type} is incompatible with type {second_type}')

    def _get_all_pairs(self, upperbound_chain):
        pairs = consecutive_pairs(upperbound_chain)
        prevs = []
        for a, b in pairs:
            for prev in prevs:
                yield (prev, a)
            yield (a, b)
            prevs.append(a)


class TypeInferencer:
    def __init__(self, compatibility, env=None, func_env=None):
        self.compatibility = compatibility
        self.env = env if env is not None else {}
        self.func_env = func_env if func_env is not None else {}

    @overloaded
    def infer(self, tree: ExprNode) -> Type:  # pragma: no cover
        raise TypeError('Invalid node type: {}'.format(tree))

    @infer.register(TypeNameNode)
    def _(self, tree: TypeNameNode):
        inferred_type = SimpleType(tree.children[0].name)
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
            if not self.compatibility.is_assignable_to(arg_type, expected_arg_type):
                raise TypeError(
                    f'Incompatible types for argument {i} of {func_name}: {arg_type} instead of {expected_arg_type}')
        tree.info['type'] = inferred_type
        return inferred_type

    @infer.register(LetNode)
    def _(self, tree: LetNode):
        *assignments, expr = tree.children

        # we must do this for the side effects on the children and environment!
        for assignment in assignments:
            self.infer(assignment)

        inferred_type = self.infer(expr)
        tree.info['type'] = inferred_type
        return inferred_type

    @infer.register(BinaryOpNode)
    def _(self, tree: BinaryOpNode):
        left_ty = self.infer(tree.children[1])
        right_ty = self.infer(tree.children[3])
        if tree.children[0].name == '+':
            inferred_type = self._infer_merge(left_ty, right_ty)
        elif tree.children[0].name == '|':
            inferred_type = self._infer_choice(left_ty, right_ty)
        else:
            inferred_type = self._infer_concat(left_ty, right_ty)
        tree.info['type'] = inferred_type
        return inferred_type

    def _infer_merge(self, left_ty, right_ty):
        if isinstance(left_ty, ParallelType) and isinstance(right_ty, ParallelType):
            if left_ty.num_outputs != right_ty.num_outputs:
                raise TypeError('Incompatible types for merge: {!r} and {!r}.'.format(left_ty, right_ty))
            zipped_types = list(zip(left_ty.types, right_ty.types))
            if not all(starmap(self.compatibility.is_compatible, zipped_types)):
                raise TypeError('Incompatible types for merge: {!r} and {!r}'.format(left_ty, right_ty))
            new_inner_types = list(starmap(self.compatibility.get_upperbound, zipped_types))
            return ParallelType(new_inner_types)
        elif isinstance(left_ty, ParallelType) ^ isinstance(right_ty, ParallelType):
            raise TypeError('Incompatible types for merge: {!r} and {!r}'.format(left_ty, right_ty))
        if not self.compatibility.is_compatible(left_ty, right_ty):
            raise TypeError('Cannot add incompatible types {} and {}'.format(left_ty, right_ty))
        return self.compatibility.get_upperbound(left_ty, right_ty)

    def _infer_choice(self, left_ty, right_ty):
        return ChoiceType([left_ty, right_ty])

    def _infer_concat(self, left_ty, right_ty):
        return ParallelType([left_ty, right_ty])


class Compiler:
    def __init__(self, library, show_header=True):
        self.compatibility = library.compatibility()
        self.func_env = library.func_env()
        self.env = library.env()
        self._inferencer = TypeInferencer(self.compatibility, self.env.get('::types::'), self.func_env.get('::types::'))
        self._schema = Schema(show_header=show_header)
        self._cur_arbitrary_id = 0
        self._cur_transformer_id = 0
        self._compiled_expressions = []

    def compile(self, expr: ExprNode, column_names: List[str] = None) -> Schema:
        self._inferencer.infer(expr)
        result = expr.visit(self.visitor)
        return self.complete_compilation(result, column_names=column_names)

    def complete_compilation(self, result, *, column_names: List[str] = None) -> Schema:
        identity = IdentityTransformer(1)
        out_names = result.info['out_names']
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
    def visitor(self, cur_node: ExprNode, *children_values):  # pragma: no cover
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
        # TODO: we should be able to check if the configuration is valid here instead of afterwards.
        type_name, arbitrary, config = children_values
        name = self._new_arbitrary_name()
        self._schema.add_arbitrary(name, type=arbitrary if arbitrary != 'default' else type_name, config=config)
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

    @visitor.register(LetNode)
    def _(self, cur_node: LetNode, *children_values):
        *assignments, result = children_values
        cur_node.info['assigned_name'] = None
        cur_node.info['out_names'] = result.info['out_names']
        cur_node.info['in_names'] = result.info['in_names']
        return cur_node

    def _new_transformer_name(self) -> str:
        name = 'transformer#{}'.format(self._cur_transformer_id)
        self._cur_transformer_id += 1
        return name

    def _new_arbitrary_name(self) -> str:
        name = 'arbitrary#{}'.format(self._cur_arbitrary_id)
        self._cur_arbitrary_id += 1
        return name
