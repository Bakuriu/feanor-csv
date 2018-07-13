from .arbitrary import Arbitrary


class IntArbitrary(Arbitrary):
    def __init__(self, random_funcs):
        super().__init__(random_funcs, 'int')

    def __call__(self):
        return self._random_funcs.randint(0, 1000000)


class MultiArbitrary(Arbitrary):
    def __init__(self, random_funcs, arbitraries):
        super().__init__(random_funcs, 'multi')
        self._arbitraries = tuple(arbitraries)

    @property
    def number_of_columns(self):
        return len(self._arbitraries)

    def __call__(self):
        return tuple(arbitrary() for arbitrary in self._arbitraries)

    def __getitem__(self, item):
        return self._arbitraries[item]