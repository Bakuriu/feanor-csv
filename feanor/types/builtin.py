from .arbitrary import Arbitrary


class IntArbitrary(Arbitrary):
    def __init__(self, random_funcs, config=None):
        super().__init__(random_funcs, 'int', config)

    def __call__(self):
        return self._random_funcs.randint(self.config.lowerbound, self.config.upperbound)

    @classmethod
    def default_config(cls):
        return {'lowerbound': 0, 'upperbound': 1000000}


class MultiArbitrary(Arbitrary):
    def __init__(self, random_funcs, arbitraries, config=None):
        super().__init__(random_funcs, 'multi', config)
        self._arbitraries = tuple(arbitraries)

    @property
    def number_of_columns(self):
        return len(self._arbitraries)

    def __call__(self):
        return tuple(arbitrary() for arbitrary in self._arbitraries)

    def __getitem__(self, item):
        return self._arbitraries[item]