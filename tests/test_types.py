import unittest

from feanor.dsl.types import SimpleType, ParallelType, ChoiceType


class TestType(unittest.TestCase):
    def test_simple_types_are_equals_if_same_name(self):
        self.assertEqual(SimpleType('int'), SimpleType('int'))
        self.assertEqual(hash(SimpleType('int')), hash(SimpleType('int')))

    def test_simple_types_are_different_if_different_name(self):
        self.assertNotEqual(SimpleType('float'), SimpleType('int'))

    def test_parallel_types_are_equals_if_equal_subtypes(self):
        self.assertEqual(ParallelType([SimpleType('int'), SimpleType('float')]),
                         ParallelType([SimpleType('int'), SimpleType('float')]))
        self.assertEqual(hash(ParallelType([SimpleType('int'), SimpleType('float')])),
                         hash(ParallelType([SimpleType('int'), SimpleType('float')])))

    def test_parallel_types_are_different_if_different_subtypes(self):
        self.assertNotEqual(ParallelType([SimpleType('int'), SimpleType('int')]),
                            ParallelType([SimpleType('int'), SimpleType('float')]))

    def test_parallel_types_are_different_if_different_num_outputs(self):
        self.assertNotEqual(ParallelType([SimpleType('int')]), ParallelType([SimpleType('int'), SimpleType('float')]))

    def test_choice_types_are_equals_if_equal_subtypes(self):
        self.assertEqual(ChoiceType([SimpleType('int'), SimpleType('float')]),
                         ChoiceType([SimpleType('int'), SimpleType('float')]))
        self.assertEqual(hash(ChoiceType([SimpleType('int'), SimpleType('float')])),
                         hash(ChoiceType([SimpleType('int'), SimpleType('float')])))

    def test_choice_types_are_different_if_different_subtypes(self):
        self.assertNotEqual(ChoiceType([SimpleType('int'), SimpleType('int')]),
                            ChoiceType([SimpleType('int'), SimpleType('float')]))

    def test_choice_types_are_different_if_different_num_outputs(self):
        self.assertNotEqual(ChoiceType([SimpleType('int')]), ChoiceType([SimpleType('int'), SimpleType('float')]))

    def test_choice_types_are_equals_if_equal_subtypes_unordered(self):
        self.assertEqual(ChoiceType([SimpleType('int'), SimpleType('float')]),
                         ChoiceType([SimpleType('float'), SimpleType('int')]))
        self.assertEqual(hash(ChoiceType([SimpleType('int'), SimpleType('float')])),
                         hash(ChoiceType([SimpleType('float'), SimpleType('int')])))

    def test_choice_types_do_not_keep_duplicates(self):
        self.assertEqual(ChoiceType([SimpleType('int'), SimpleType('int')]), ChoiceType([SimpleType('int')]))
        self.assertEqual(hash(ChoiceType([SimpleType('int'), SimpleType('int')])),
                         hash(ChoiceType([SimpleType('int')])))
