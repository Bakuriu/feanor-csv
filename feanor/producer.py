# Copyright 2018 Giacomo Alzetta <giacomo.alzetta+feanor@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from abc import ABCMeta, abstractmethod
from types import SimpleNamespace
from typing import Set

from .util import to_string_list


class Producer(metaclass=ABCMeta):
    def __init__(self, random_funcs, type_name, config):
        self._random_funcs = random_funcs
        self._type_name = type_name
        conf = self.default_config()
        conf.update(config or {})
        if self.required_config_keys() <= conf.keys():
            self._config = Config(**conf)
        else:
            raise ValueError(f'Type {type_name} requires at least the following configuration values: '
                             + to_string_list(self.required_config_keys()))

    @property
    def type(self):  # pragma: no cover
        return self._type_name

    @property
    def config(self):
        return self._config

    @classmethod
    def default_config(cls):
        return {}

    @classmethod
    def required_config_keys(cls) -> Set[str]:
        return set()

    @abstractmethod
    def __call__(self):
        raise NotImplementedError


class Config(SimpleNamespace):
    def __getattr__(self, item):
        match = re.fullmatch(r'get_(?P<attr>\w+)', item)
        if match:
            return lambda default=None: getattr(self, match.group('attr'), default)
        raise AttributeError(item)

    def has_attrs(self, *attrs):
        return all(hasattr(self, attr) for attr in attrs)
