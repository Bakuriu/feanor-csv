from collections import defaultdict
from functools import wraps


class FakeRandom:

    def __init__(self):
        self._calls_settings = defaultdict(dict)

    def register(self, name, args, ret_vals):
        self._calls_settings[name][args] = list(reversed(ret_vals))

    def register_default(self, name, value):
        self._calls_settings[name]['default'] = self._value_or_function(value)

    def register_missing(self, name, value):
        self._calls_settings[name]['missing'] = self._value_or_function(value)

    def register_signature(self, name, param_names):
        self._calls_settings[name]['signature'] = tuple(param_names)

    def __getattr__(self, name):
        if name in self._calls_settings:
            @wraps(eval('lambda {}: None'.format(', '.join(self._calls_settings[name].get('signature', [])))))
            def fake_call(*args):
                calls_dict = self._calls_settings.get(name)
                values = calls_dict.get(args)
                if values is None:
                    if 'default' in calls_dict:
                        return calls_dict['default'](*args)
                    else:
                        raise RuntimeError(f'Unknown call {name}{args}')
                if len(values) >= 1:
                    return values.pop()
                elif 'missing' in calls_dict:
                    return calls_dict['missing'](*args)
                raise RuntimeError(f'Too many calls to {name}{args}')
            return fake_call
        raise AttributeError(name)

    def _value_or_function(self, maybe_function):
        return maybe_function if callable(maybe_function) else lambda *args: maybe_function

    @classmethod
    def from_dict(cls, config):
        rand = FakeRandom()
        for name, val in config.items():
            for args, result in val.items():
                if args == 'default':
                    rand.register_default(name, result)
                elif args == 'missing':
                    rand.register_missing(name, result)
                elif args == 'signature':
                    rand.register_signature(name, result)
                else:
                    rand.register(name, args, result)
        return rand