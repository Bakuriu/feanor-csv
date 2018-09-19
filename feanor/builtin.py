import inspect
import random
import string
from itertools import cycle
from datetime import datetime, timezone, timedelta, MINYEAR, MAXYEAR

from .arbitrary import Arbitrary
from .dsl.compiler import PairBasedCompatibility
from .library import Library

__all__ = [
    'Arbitrary',
    'IntArbitrary', 'FloatArbitrary',
    'StringArbitrary', 'AlphaArbitrary', 'AlphaNumericArbitrary',
    'DateArbitrary',
    'FixedArbitrary', 'CyclingArbitrary', 'RepeaterArbitrary'
]


class IntArbitrary(Arbitrary):
    def __init__(self, random_funcs, config=None):
        super().__init__(random_funcs, 'int', config)

    def __call__(self):
        return self._random_funcs.randint(self.config.min, self.config.max)

    @classmethod
    def default_config(cls):
        return {'min': 0, 'max': 1_000_000}


class FloatArbitrary(Arbitrary):
    def __init__(self, random_funcs, config=None):
        super().__init__(random_funcs, 'float', config)
        available_functions = [
            'random',
            'uniform',
            'triangular',
            'betavariate',
            'expovariate',
            'gammavariate',
            'gauss',
            'lognormvariate',
            'normalvariate',
            'normalvariate',
            'vonmisesvariate',
            'paretovariate',
            'weibullvariate',
        ]
        distribution = getattr(self.config, 'distribution')
        if not distribution in available_functions:
            raise ValueError(f'Invalid distribution name: {distribution}')
        self._distribution = getattr(self._random_funcs, distribution)
        self._kwargs = self._get_distribution_kwargs(distribution)

    def _get_distribution_kwargs(self, distribution):
        try:
            sig = inspect.signature(getattr(self._random_funcs, distribution))
        except ValueError:
            return {}
        else:
            used_names = [param.name for param in sig.parameters.values()]
            renamed_params = {
                'a': 'min',
                'b': 'max',
                'lambd': 'lambda',
            }
            config_names = ((renamed_params.get(name, name), name) for name in used_names)
            return {param_name: getattr(self.config, config_name) for config_name, param_name in config_names}

    def __call__(self):
        return self._distribution(**self._kwargs)

    @classmethod
    def default_config(cls):
        return {
            'min': 0, 'max': 1000000.0, 'distribution': 'uniform', 'alpha': 0.0, 'beta': 1.0, 'lambda': 1.0, 'mu': 1.0,
            'sigma': 1.0, 'kappa': 1.0
        }

    @classmethod
    def required_config_keys(cls):
        return {'distribution'}


class StringArbitrary(Arbitrary):
    def __init__(self, random_funcs, config=None):
        super().__init__(random_funcs, 'string', config)
        if not isinstance(self.config.characters, str):
            self.config.characters = ''.join(self.config.characters)

    def __call__(self):
        min_len = getattr(self.config, 'min_len', self.config.len)
        max_len = getattr(self.config, 'max_len', self.config.len)
        string_length = self._random_funcs.randint(min_len, max_len)
        weights = getattr(self.config, 'weights', None)
        return ''.join(self._random_funcs.choices(self.config.characters, weights, k=string_length))

    @classmethod
    def default_config(cls):
        return {'len': 10, 'characters': string.ascii_letters + string.digits + string.punctuation + ' \t'}


class AlphaArbitrary(StringArbitrary):
    def __init__(self, random_funcs, config=None):
        config = config or {}
        config['characters'] = string.ascii_letters
        super().__init__(random_funcs, config)

    @classmethod
    def default_config(cls):
        return {'len': 10}


class AlphaNumericArbitrary(StringArbitrary):
    def __init__(self, random_funcs, config=None):
        config = config or {}
        config['characters'] = string.ascii_letters + string.digits
        super().__init__(random_funcs, config)

    @classmethod
    def default_config(cls):
        return {'len': 10}


class DateArbitrary(Arbitrary):
    def __init__(self, random_funcs, config=None):
        super().__init__(random_funcs, 'date', config)
        self._mode = self.config.get_mode('interval')
        utc = timezone.utc
        if self._mode not in ('interval', 'slice'):
            raise ValueError(f'Invalid mode {repr(self._mode)}')
        if self.config.has_attrs('min_ts'):
            min_ts = self.config.min_ts
            self._start_date = datetime.utcfromtimestamp(min_ts).replace(tzinfo=utc)
            min_hour = self.config.get_min_hour(self._start_date.hour)
            min_minute = self.config.get_min_minute(self._start_date.minute)
            min_second = self.config.get_min_second(self._start_date.second)
            self._start_date = self._start_date.replace(hour=min_hour, minute=min_minute, second=min_second)
        else:
            min_year = self.config.get_min_year(MINYEAR)
            min_month = self.config.get_min_month(1)
            min_day = self.config.get_min_day(1)
            min_hour = self.config.get_min_hour(0)
            min_minute = self.config.get_min_minute(0)
            min_second = self.config.get_min_second(0)
            self._start_date = datetime(min_year, min_month, min_day, min_hour, min_minute, min_second, tzinfo=utc)

        if self.config.has_attrs('max_ts'):
            max_ts = self.config.max_ts
            self._end_date = datetime.utcfromtimestamp(max_ts).replace(tzinfo=utc)
            max_hour = self.config.get_max_hour(self._end_date.hour)
            max_minute = self.config.get_max_minute(self._end_date.minute)
            max_second = self.config.get_max_second(self._end_date.second)
            self._end_date = self._end_date.replace(hour=max_hour, minute=max_minute, second=max_second)
        else:
            max_year = self.config.get_max_year(MAXYEAR)
            max_month = self.config.get_max_month(12)
            max_day = self.config.get_max_day(31)
            max_hour = self.config.get_max_hour(23)
            max_minute = self.config.get_max_minute(59)
            max_second = self.config.get_max_second(59)
            self._end_date = datetime(max_year, max_month, max_day, max_hour, max_minute, max_second, tzinfo=utc)

    def __call__(self):
        if self._mode == 'interval':
            start_ts = self._start_date.timestamp()
            end_ts = self._end_date.timestamp()
            timestamp = self._random_funcs.randint(start_ts, end_ts)
            return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=timestamp)
        else:
            max_days_difference = (self._end_date - self._start_date).days
            num_day = self._random_funcs.randint(0, max_days_difference)
            date = self._start_date + timedelta(days=num_day)
            hour = self._random_funcs.randint(self._start_date.hour, self._end_date.hour)
            minute = self._random_funcs.randint(self._start_date.minute, self._end_date.minute)
            second = self._random_funcs.randint(self._start_date.second, self._end_date.second)
            return datetime(date.year, date.month, date.day, hour, minute, second)


class RepeaterArbitrary(Arbitrary):
    """An arbitrary that returns for `num_repeats` time the value generated by
    the wrapped arbitrary.

    """

    def __init__(self, random_funcs, arbitrary, config=None):
        super().__init__(random_funcs, 'repeater', config)
        self._arbitrary = arbitrary
        self._current_count = 0
        self._sentinel = object()
        self._last_value = self._sentinel

    def __call__(self):
        if self._last_value is self._sentinel or self._current_count >= self.config.num_repeats:
            self._last_value = self._arbitrary()
            self._current_count = 1
        else:
            self._current_count += 1

        return self._last_value

    @classmethod
    def required_config_keys(cls):
        return {'num_repeats'}


class FixedArbitrary(Arbitrary):
    def __init__(self, random_funcs, config):
        super().__init__(random_funcs, 'fixed', config)

    def __call__(self):
        return self.config.value

    @classmethod
    def required_config_keys(cls):
        return {'value'}


class CyclingArbitrary(Arbitrary):
    def __init__(self, random_funcs, config):
        super().__init__(random_funcs, 'cycle', config)
        self._values = cycle(self.config.values)

    def __call__(self):
        return next(self._values)

    @classmethod
    def required_config_keys(cls):
        return {'values'}


class BuiltInLibrary(Library):
    def __init__(self, global_configuration, random_funcs=random):
        super().__init__(global_configuration, random_funcs)
        self._builtin_factories = {
            'int': IntArbitrary,
            'float': FloatArbitrary,
            'string': StringArbitrary,
            'alpha': AlphaArbitrary,
            'alnum': AlphaNumericArbitrary,
            'date': DateArbitrary,
            'fixed': FixedArbitrary,
            'cycle': CyclingArbitrary,
        }

    def get_arbitrary_factory(self, name):
        return self._builtin_factories[name]

    def compatibility(self):
        return BuiltInCompatibility()

    def env(self):
        return {}

    def func_env(self):
        return {}


class BuiltInCompatibility(PairBasedCompatibility):

    def __init__(self):
        super().__init__()
        self.add_upperbounds({
            ('int', 'int'), ('float', 'float'), ('int', 'float'),
            ('alpha', 'alnum', 'string'),
        })


def create_library(global_configuration, random_funcs):
    """Entry-point for the arbitrary library."""
    return BuiltInLibrary(global_configuration, random_funcs)